from django.contrib import admin
from .models import Product, Category

# Register your models here.


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
    )

    ordering=('name',)

class CategoryAdmin(admin.ModelAdmin):
    list_display=(
        'name',
    )

# Register your models here.
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)