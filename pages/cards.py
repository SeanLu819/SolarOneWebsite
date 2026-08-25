from django.db import models


class ProductsPageCard(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='卡片标题，如 "M Series"、"Sports Lighting" 等'
    )
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        help_text='卡片副标题 / 简短描述，显示在标题下方'
    )
    image = models.ImageField(
        upload_to='products_page/',
        blank=True,
        help_text='卡片图片。建议 1280×720 像素（16:9），用于产品列表页卡片展示'
    )
    slug = models.CharField(
        max_length=200,
        blank=True,
        help_text='关联的产品 slug，用于匹配卡片与产品。如 "m-series"。修改此字段将改变卡片关联的产品。',
        db_index=True,
    )
    link_url = models.CharField(
        max_length=200,
        help_text='卡片点击跳转链接，如 "/products/m-series/"。仅用于前台跳转，不影响卡片与产品的匹配。',
        db_index=True,
    )
    order = models.IntegerField(
        default=0,
        help_text='显示顺序（数字越小越靠前）'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='是否在 Products 页面显示此卡片'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Products Page Card'
        verbose_name_plural = 'Products Page Cards'

    def __str__(self):
        return f'{self.title} -> {self.link_url}'