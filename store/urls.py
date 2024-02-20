from django.urls import path
from . import views, api

urlpatterns = [
    path('', views.store, name='store'),
    path('register/', views.user_register, name='register'),
    path('signin/', views.user_login, name='login'),
    path('account/', views.account, name='account'),
    path('add-to-cart/', api.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('update-quantity/', api.update_quantity, name='update_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-order/', api.process_order),
    path('update-avatar/', api.update_avatar, name='update_avatar'),
    path('pay/', views.pay, name='pay'),
    path('google/', views.google_auth, name='google'),
]
