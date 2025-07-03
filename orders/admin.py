from django.contrib import admin
from .models import Order, OrderUser, ProductType

admin.site.register(Order)
admin.site.register(OrderUser)
admin.site.register(ProductType)


