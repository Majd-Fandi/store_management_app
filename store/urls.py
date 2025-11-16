from django.urls import path
from . import views
from django.views.generic import TemplateView
handler404 = views.custom_404

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('products', views.product_list, name='home'),
    path('classifications', views.classifications_list, name='classifications_list'),
    path('products/<int:product_id>', views.product_detail, name='product_detail'),
    
    path('add', views.add_product, name='add_product'),
    path('add-classification', views.add_classification, name='add_classification'),
    path('remove/<int:product_id>', views.remove_product, name='remove_product'),
    path('remove-category/<int:classification_id>', views.remove_classification, name='remove_classification'),
    path('sell', views.sell_product, name='sell_product'),

    path('sales', views.list_sales, name='list_sales'),
    path('sales/<int:sale_id>', views.sale_detail, name='sale_detail'),
    path('sales/delete/<int:sale_id>', views.remove_sale, name='remove_sale'),
    path('sales/delete-all', views.remove_all_sales, name='remove_all_sales'),

    path('generate_pdf', views.generate_pdf, name='generate_pdf'),
    path('settings', views.settings_view, name='settings'),
    
    path('import-products/', views.import_products, name='import_products'),
    path('insert-products/', views.add_bulk_products, name='insert_products'),
    path('sales-statistics/', views.sales_statistics, name='sales_statistics'),

    path('offline/', TemplateView.as_view(template_name='offline.html')),
]
