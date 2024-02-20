from .models import Customer, Order, OrderItem, Product
from .utils import total_avatar, modify_intent, verify_payment
from .serializers import AddressSerializer, ChangeAvatarSerializer
from django.conf import settings
from django.db.models import F, Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from decimal import Decimal
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['POST'])
def add_to_cart(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(user=request.user, complete=False)
        OrderItem.objects.update_or_create(order=order, product_id=request.data['product_id'],
                                           defaults={'quantity': F('quantity') + 1},
                                           create_defaults={'quantity': 1})
    else:
        product_id = str(request.data['product_id'])
        cart = request.session.get('cart', {})
        cart[product_id] = {'quantity': cart.get(product_id, {}).get('quantity', 0) + 1,
                            'price': str(Product.objects.filter(pk=product_id).values('price')[0]['price'])}
        request.session['cart'] = cart
    modify_intent(request)
    return Response({'cartItems': total_avatar(request)['items_in_cart']})


@api_view(['POST'])
def update_quantity(request):
    if request.user.is_authenticated:
        conditions = Q(order__user=request.user) & Q(order__complete=False) & Q(
            product_id=request.data['product_id'])
        order_item = OrderItem.objects.filter(conditions).select_for_update()
        if request.data['action'] == 'add':
            order_item.update(quantity=F('quantity')+1)
        elif request.data['action'] == 'remove':
            order_item.update(quantity=F('quantity')-1)
        data = OrderItem.objects.filter(conditions, quantity__gt=0
                                        ).values('quantity', total=F('quantity') * F('product__price')).first()
        if not data:
            order_item.delete()
            data = {'deleted': True}
    else:
        id_product = str(request.data['product_id'])
        product = request.session['cart'][id_product]
        quantity = product['quantity']
        action = request.data['action']
        quantity += 1 if action == 'add' else -1 if action == 'remove' else None
        if quantity > 0:
            request.session['cart'][id_product]['quantity'] = quantity
            data = {'total': quantity * Decimal(product['price']), 'quantity': quantity}
        else:
            del request.session['cart'][id_product]
            data = {'deleted': True}
        request.session.modified = True
    modify_intent(request)
    data.update(total_avatar(request))
    return Response(data)


# receives a webhook from Stripe and saves the order in case of success
@csrf_exempt
@api_view(['POST'])
def process_order(request):
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(request.body, sig_header, settings.ENDPOINT_SECRET)
    except stripe.error.SignatureVerificationError as e:
        return Response({'error': 'Webhook signature verification failed' + str(e)}, status=400)
    if event['type'] == 'payment_intent.succeeded':
        payment = event['data']['object']
        order = verify_payment(payment['metadata']['session_key'], payment['amount'] / Decimal(100))
        order.transaction_id = payment.id
        customer_data = stripe.Customer.retrieve(payment['customer'])
        order.customer = Customer.objects.create(name=customer_data['name'], email=customer_data['email'])
        if any(not order_item.product.digital for order_item in order.order_items.all()):
            serializer = AddressSerializer(data=payment['shipping']['address'])
            if serializer.is_valid():
                order.shipping = serializer.save()
        order.complete = True
        order.save()
    return Response()


@permission_classes([IsAuthenticated])
@api_view(['POST'])
def update_avatar(request):
    serializer = ChangeAvatarSerializer(request.user, data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response({'avatarUrl': request.user.avatar.url})
