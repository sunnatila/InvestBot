# Generated by Django 5.2.3 on 2025-07-12 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0008_alter_order_payment_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="paymentdate",
            name="payment_date",
            field=models.DateField(),
        ),
    ]
