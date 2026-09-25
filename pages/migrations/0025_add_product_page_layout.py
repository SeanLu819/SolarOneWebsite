# Product.page_layout — picks between the series-overview template and the
# full product-detail template (see pages/views/views_products.py).
#
# NOTE: `makemigrations` also wanted to emit two unrelated
# `AlterField(siteconfig.font_family_*)` operations (pre-existing model-state
# drift left by 0024). They are deliberately NOT included here — this migration
# carries only the change it is named after.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0024_update_siteconfig_font_chinese_fallback'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='page_layout',
            field=models.CharField(
                choices=[
                    ('detail', 'Product detail page (full specs)'),
                    ('overview', 'Series overview page (landing)'),
                ],
                default='detail',
                help_text='系列首页：只展示 banner、主图轮播与文字说明（无光束角/尺寸/参数表），'
                          '适合作为大系列的落地页（如 M Series、RGB / RGBW、Accessory）。'
                          '产品详细页：展示全部技术参数（如 FL4M）。默认「产品详细页」。',
                max_length=16,
                verbose_name='Page template',
            ),
        ),
    ]
