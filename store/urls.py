from django.urls import path
from . import views
handler404 = views.custom_404

urlpatterns = [
    path('print_receipt/<int:serial_number>/', views.print_receipt, name='print_receipt'),
    path('', views.product_list, name='home'),

    path('products', views.product_list, name='product_list'),
    path('add', views.add_product, name='add_product'),
    path('remove/<int:product_id>', views.remove_product, name='remove_product'),
    path('products/<int:product_id>', views.product_detail, name='product_detail'),

    path('classifications', views.classifications_list, name='classifications_list'),
    path('add-classification', views.add_classification, name='add_classification'),
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

        # Trader URLs
    path('traders/', views.trader_list, name='trader_list'),
    path('traders/add/', views.add_trader, name='add_trader'),
    path('traders/<int:pk>/', views.trader_detail, name='trader_detail'),
    path('financial-box', views.financial_box, name='financial_box'),
    # path('retrieve-sale-item/<int:item_id>/', views.retrieve_sale_item, name='retrieve_sale_item'),

    
    # Transaction URLs
    path('traders/<int:trader_pk>/add_transaction/', 
         views.add_transaction, 
         name='add_transaction'),

]
