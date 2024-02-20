from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, forms
from django.db.models import F
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Product, CustomUser
from .utils import total_avatar, cart_checkout
from .forms import CustomUserCreationForm
from .serializers import CustomerSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from google.oauth2 import id_token
from google.auth.transport import requests
import stripe

# Google Oauth client id (NOT client secret)
client_id = '...apps.googleusercontent.com'


def store(request):
    context = {'products': Product.objects.filter(is_active=True), **total_avatar(request)}
    return render(request, 'store.html', context)


def cart(request):
    context = cart_checkout(request)
    for item in context['items']:
        item.total = item.quantity * item.price
    return render(request, 'cart.html', context)


def checkout(request):
    context = cart_checkout(request)
    if any(not item.digital for item in context['items']):
        context['shipping'] = True
    return render(request, 'checkout.html', context)


@api_view(['POST'])
def pay(request):
    serializer = CustomerSerializer(data=request.data)
    if serializer.is_valid():
        user_data = serializer.validated_data
        customer = stripe.Customer.create(name=user_data['name'], email=user_data['email'])
        intent_id = request.session.get('intent_id')
        metadata = {'session_key': request.session.session_key}
        client_secret = stripe.PaymentIntent.modify(intent_id, customer=customer,
                                                    metadata=metadata)['client_secret']
        return Response({'clientResponse': client_secret})
    else:
        return Response()


def user_register(request):
    if request.user.is_anonymous:
        context = {'form': CustomUserCreationForm(), **total_avatar(request)}
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                login(request, form.save())
                return redirect('store')
            else:
                context['form'] = form
        return render(request, 'sign_up.html', context)
    else:
        return redirect('store')


# Django AuthenticationForm uses email as a 'username' field
def user_login(request):
    if request.user.is_anonymous:
        context = {'form': forms.AuthenticationForm(), **total_avatar(request)}
        if request.method == 'POST':
            form = forms.AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = authenticate(email=form.cleaned_data['username'], password=form.cleaned_data['password'])
                login(request, user)
                return redirect('store')
            else:
                context['form'] = form
        return render(request, 'sign_in.html', context)
    else:
        return redirect('store')


@api_view(['POST'])
def google_auth(request):
    if request.user.is_anonymous:
        auth_header = request.headers.get('Authorization')
        jwt_code = auth_header.split('Bearer ')[1]
        try:
            id_info = id_token.verify_oauth2_token(jwt_code, requests.Request(), client_id)
        except Exception as e:
            return Response({'error': str(e)}, status=401)
        user, created = CustomUser.objects.get_or_create(email=id_info['email'])
        login(request, user)
        return Response({'redirectUrl': reverse('store')})


# account page
@login_required(login_url='login')
def account(request):
    context = {'items': Product.objects.filter(orderitem__order__user=request.user, orderitem__order__complete=True
                                               ).annotate(quantity=F('orderitem__quantity')
                                                          ).order_by('-orderitem__order__date_ordered'),
               **total_avatar(request)}
    return render(request, 'account.html', context)


def handler404(request, exception):
    return redirect('store')
