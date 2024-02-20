from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('store.urls')),
    path('admin/', admin.site.urls),
]
handler404 = 'store.views.handler404'
