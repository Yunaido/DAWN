# Generated by Django 5.0.3 on 2024-03-07 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matsecom", "0006_alter_subscription_price_per_extra_minute"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="basic_fee",
            field=models.PositiveIntegerField(),
        ),
    ]