from django.contrib import admin
from .models import Product,Settings,Sale,SaleItem,FinancialBox,Trader,Transaction
from django.contrib.auth.models import Group, User

# Unregister default Django models
admin.site.unregister(Group)
admin.site.unregister(User)   

# Set admin site header, title, and index title
admin.site.site_header = "POS System Administration"  # Header on login page and main admin page
admin.site.site_title = "Admin Portal"           # Title tag (browser tab)
admin.site.index_title = "POS"  # Subtitle on the main admin page

admin.site.register(Product)
admin.site.register(Settings)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(FinancialBox)
admin.site.register(Transaction)
admin.site.register(Trader)
