from django.db import models


class OrderUser(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    tg_id = models.CharField(max_lenth=50, null=True, blank=True)
    passport_id = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Order User"
        verbose_name_plural = "Order Users"
        db_table = "order_users"

class Order(models.Model):
    user = models.ForeignKey(OrderUser, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=100)
    product_year = models.IntegerField(null=True, blank=True)
    product_type = models.ForeignKey("ProductType", on_delete=models.SET_NULL, null=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    all_debt = models.DecimalField(max_digits=10, decimal_places=2)
    debt_term = models.IntegerField()
    per_month_debt = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    benefit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    first_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    given_time = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name}"


    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        db_table = "orders"


class ProductType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Product Type"
        verbose_name_plural = "Product Types"
        db_table = "product_types"

