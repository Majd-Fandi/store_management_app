from django.contrib import admin
from .models import Product,Settings,Sale,SaleItem

admin.site.register(Product)
admin.site.register(Settings)
admin.site.register(Sale)
admin.site.register(SaleItem)
