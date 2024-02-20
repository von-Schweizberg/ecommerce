from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    username = models.CharField(null=True, blank=True, unique=True, max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    avatar = models.ImageField(upload_to='user_avatars', default='default/default_user.png')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    digital = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products', null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        try:
            url = self.image.url
        except Exception:
            url = ''
        return url


class Customer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=200)

    def __str__(self):
        return f"Customer {self.id}"


class ShippingAddress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    country = models.CharField(max_length=100)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=150)
    state = models.CharField(max_length=50, null=True)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return f"Address {self.id}"


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True)
    shipping = models.ForeignKey(ShippingAddress, on_delete=models.PROTECT, null=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    transaction_id = models.CharField(max_length=1000, null=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        order_items = ', '.join(
            f'{item.id} {item.product.name}'
            for item in self.order_items.all()
        )
        return f'Order {self.id} | {order_items}'


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f'Order item | {self.id}'
