from django.contrib.sessions.models import Session
from .models import Product, OrderItem, Order
from django.db.models import F
from decimal import Decimal
import stripe


# function returns quantity of items in cart, cart total amount and user's avatar url
def total_avatar(request):
    if request.user.is_authenticated:
        order_items = OrderItem.objects.filter(order__user=request.user, order__complete=False).values(
            'quantity', 'product__price')
        items_in_cart = sum([item['quantity'] for item in order_items])
        cart_total = sum(item['quantity'] * item['product__price'] for item in order_items)
        avatar = request.user.avatar.url
    else:
        cart = request.session['cart'] if request.session.get('cart') else {}
        items_in_cart = sum(item['quantity'] for item in cart.values())
        cart_total = sum(item['quantity']*Decimal(item['price']) for item in cart.values())
        avatar = 'default/default_user.png'
    return {'items_in_cart': items_in_cart, 'cart_total': cart_total, 'avatar': avatar}


# create or modify Stripe payment intent and save its id into the user's session
def modify_intent(request):
    intent = stripe.PaymentIntent
    amount = total_avatar(request)['cart_total']
    intent_id = request.session.get('intent_id')
    if not intent_id:
        request.session['intent_id'] = intent.create(amount=int(amount * 100), currency='usd').id
    else:
        if intent.retrieve(intent_id)['status'] == 'succeeded':
            request.session['intent_id'] = intent.create(amount=int(amount * 100), currency='usd').id
        else:
            intent.modify(intent_id, amount=int(amount * 100)) if amount > 0 else None


# returns context for 'cart' and 'checkout' view functions
def cart_checkout(request):
    if request.user.is_authenticated:
        items = Product.objects.filter(
            orderitem__order__user=request.user,
            orderitem__order__complete=False
        ).annotate(quantity=F('orderitem__quantity'))
    else:
        cart = request.session['cart'] if request.session.get('cart') else {}
        items = Product.objects.filter(id__in=cart.keys())
        for item in items:
            item.quantity = cart[str(item.id)]['quantity']
    return {'items': items, **total_avatar(request)}


# checks whether amount from stripe equal to the amount from db and creates an Order for unknown user
def verify_payment(session_key, amount):
    session = Session.objects.get(pk=session_key)
    user_id = session.get_decoded().get('_auth_user_id')
    if user_id:
        order_items = OrderItem.objects.filter(order__user_id=user_id, order__complete=False).values(
            'quantity', 'product__price')
        cart_total = sum(item['quantity'] * item['product__price'] for item in order_items)
        if amount == cart_total:
            order = Order.objects.get(user_id=user_id, complete=False)
            order.amount = amount
    else:
        cart = session.get_decoded().get('cart')
        cart_total = sum(item['quantity'] * Decimal(item['price']) for item in cart.values())
        if amount == cart_total:
            order = Order.objects.create(amount=amount)
            for item in cart.keys():
                OrderItem.objects.create(product_id=item, order=order, quantity=cart[item]['quantity'])
            session.delete()
    return order
