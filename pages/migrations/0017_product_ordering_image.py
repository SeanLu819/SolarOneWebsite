# Generated manually for ordering_image field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0016_product_ordering_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='ordering_image',
            field=models.ImageField(blank=True, upload_to='products/ordering/', verbose_name='Ordering Information Image', help_text='订购信息示意图，展示在 ORDERING INFORMATION 表格上方。建议 1920×600 像素。'),
        ),
    ]