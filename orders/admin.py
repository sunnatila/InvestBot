from django.contrib import admin
from .models import Order, OrderUser, ProductType, PaymentDate


@admin.register(PaymentDate)
class PaymentDateAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_date', 'is_payment')
    list_filter = ('is_payment', 'payment_date')
    search_fields = ('order__product_name',)

admin.site.register(Order)
admin.site.register(OrderUser)
admin.site.register(ProductType)


