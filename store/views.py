from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Sum, Q, F ,Count
from django.db.models.functions import TruncDay

from decimal import Decimal
from datetime import datetime
from io import BytesIO

from .models import Product, Settings, Sale, SaleItem,Classification
from .forms import ProductForm
from .forms import DateRangeForm

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import json
import pandas as pd

# =======================================================================================

# Helper functions : 

def format_number_with_commas(number):
    """Format a number with commas as thousands separators."""
    return f"{int(number):,}"

# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def product_list(request):

    # Get search and quantity filter from the request
    search_query = request.GET.get('search', '')
    quantity_filter = request.GET.get('quantity', '')
    classification_filter = request.GET.get('classification', '') #new
    minimum_setting = Settings.objects.filter(key='minimum').first().value


    # Fetch all products initially
    products = Product.objects.all()

    # Fetch all classifications 
    classifications = Classification.objects.all()

    # Apply search filter (filter by name or description)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Apply quantity filter
    if quantity_filter:
        if quantity_filter == 'low':
            products = products.filter(quantity__lt=minimum_setting)
        elif quantity_filter == 'high':
            products = products.filter(quantity__gte=minimum_setting)
        elif quantity_filter == 'none':
            products = products.filter(quantity=0)

    # Apply classification filter
    if classification_filter:
        if classification_filter=="no-category":
            products=products.filter(classification=None) # no classification 
        else:
            products = products.filter(classification=classification_filter)

    # Order products by name to enable grouping in the template
    products = products.order_by('name')

     # Fetch the setting with the key 'minimum'
    minimum_setting = Settings.objects.filter(key='minimum').first()
    return render(
        request,
        'store/product_list.html',
        {
            'products': products,
            'classifications':classifications,
            'search_query': search_query,
            'quantity_filter': quantity_filter,
            'classification_filter':classification_filter,
            'minimum_value': minimum_setting.value if minimum_setting else None,
        },
    )


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def classifications_list(request):
    # Fetch all classifications and annotate them with the count of related products and sum of quantities
    classifications = Classification.objects.annotate(
        product_type_count=Count('product', distinct=True),  # Count distinct products
        all_types_count=Sum('product__quantity')  # Sum the quantities of related products
    ).order_by('category')

    return render(
        request,
        'store/classifications_list.html',
        {
            'classifications': classifications,
        },
    )


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def remove_classification(request, classification_id):
    product = get_object_or_404(Classification, id=classification_id)
    product.delete()
    return redirect('home')

# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================


from django.shortcuts import render, redirect
# Assuming Classification and Product are imported from your models
# from .models import Classification, Product 

def add_product(request):
    if request.method == "POST":
        
        # --- 1. Get All POST Data ---
        name = request.POST.get('name')
        product_type = request.POST.get('type') # Renamed 'type' to 'product_type' to avoid shadowing built-in 'type'
        items_per_package_str = request.POST.get('items_per_package')
        description = request.POST.get('description')
        price_str = request.POST.get('price')
        quantity_str = request.POST.get('quantity')
        classification_id = request.POST.get('classification')

        retail_sale_percent = request.POST.get('retail_sale_percent')
        whole_sale_percent = request.POST.get('whole_sale_percent')

        if not retail_sale_percent:
            retail_sale_percent = 5
        if not whole_sale_percent:
            whole_sale_percent = 3
        # Helper to simplify error rendering
        def render_error(error_message):
            return render(request, 'store/add_product.html', {
                'error': error_message,
                'classifications': Classification.objects.all()
            })

        # --- 2. Basic Validation & Type Conversion ---
        if not all([name, price_str, quantity_str]):
            return render_error('الرجاء تعبئة الحقول المطلوبة (المادة و السعر و الكمية)')
        
        try:
            entered_price = float(price_str)
            entered_quantity = int(quantity_str)
        except ValueError:
            return render_error('السعر والكمية يجب أن تكون أرقامًا صالحة')

        # Variables to store the final, calculated values for the database
        final_price_per_unit = entered_price
        final_quantity_of_items = entered_quantity

        # --- 3. Handle 'many' (Package) Scenario ---
        if product_type == "many":
            if not items_per_package_str:
                return render_error('يرجى تحديد عدد القطع في الطرد')
            
            try:
                items_per_package = int(items_per_package_str)
                if items_per_package <= 0:
                    raise ValueError
            except ValueError:
                return render_error('عدد القطع في الطرد يجب أن يكون رقمًا صحيحًا وموجبًا')

            # Calculation for the database:
            # Price per piece = Package Price / Items per Package
            final_price_per_unit = entered_price / items_per_package
            
            # Total quantity of items = Number of Packages * Items per Package
            final_quantity_of_items = entered_quantity * items_per_package
        
        # If product_type is "one", final_price_per_unit and final_quantity_of_items
        # already hold the entered_price and entered_quantity, so no change is needed.


        # --- 4. Handle Classification Lookup ---
        classification = None
        if classification_id:
            try:
                # Fetch the Classification instance using the ID
                classification = Classification.objects.get(id=classification_id)
            except Classification.DoesNotExist:
                return render_error('التصنيف المحدد غير صحيح')

        # --- 5. Create Product in Database ---
        Product.objects.create(
            name=name,
            description=description,
            price=final_price_per_unit,          # Store the calculated price per single item
            quantity=final_quantity_of_items,    # Store the calculated total quantity of single items
            classification=classification,        # Pass the Classification instance or None
            # tareek
            retail_sale_percent=retail_sale_percent,
            whole_sale_percent=whole_sale_percent
        )
        
        return redirect('add_product')
        
    # --- GET Request ---
    return render(request, 'store/add_product.html', {
        'classifications': Classification.objects.all()
    })

# def add_product(request):
#     if request.method == "POST":
#         name = request.POST['name']
#         type=request.POST['type']
#         items_per_package=request.POST['items_per_package']
#         description = request.POST['description']
#         price = request.POST['price']
#         quantity = request.POST['quantity']
#         classification_id = request.POST.get('classification')  # Use .get() to avoid KeyError

#         if name and price and quantity:
#             classification = None  # Default to None if no classification is selected
#             if classification_id:  # If a classification ID is provided
#                 try:
#                     # Fetch the Classification instance using the ID
#                     classification = Classification.objects.get(id=classification_id)
#                 except Classification.DoesNotExist:
#                     return render(request, 'store/add_product.html', {
#                         'error': 'التصنيف المحدد غير صحيح',
#                         'classifications': Classification.objects.all()
#                     })

#             # Create the Product instance with the Classification instance (or None)
#             Product.objects.create(
#                 name=name,
#                 description=description,
#                 price=price,
#                 quantity=quantity,
#                 classification=classification  # Pass the Classification instance or None
#             )
#             # return redirect('home')
#             return redirect('add_product')
#         else:
#             return render(request, 'store/add_product.html', {
#                 'error': 'الرجاء تعبئة الحقول المطلوبة (المادة و السعر و الكمية)',
#                 'classifications': Classification.objects.all()
#             })
#     return render(request, 'store/add_product.html', {
#         'classifications': Classification.objects.all()
#     })


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def add_classification(request):
    if request.method == "POST":
        category = request.POST['category']
        if category:
            Classification.objects.create(category=category)
            return redirect('classifications_list')
        else:
            return render(request, 'store/add_classification.html', {
                'error': 'الرجاء تعبئة الحقول المطلوبة',
            })
    return render(request, 'store/add_classification.html')


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def remove_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('home')




# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def remove_sale(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    sale.delete()
    return redirect('list_sales')


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def remove_all_sales(request):
    Sale.objects.all().delete()
    return redirect('list_sales')


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def sell_product(request):
    # Retrieve all selected product IDs from the query parameters
    selected_ids = request.GET.getlist('ids')
    products=[]
    # Fetch products based on selected IDs
    if selected_ids:
        # If there are selected IDs, filter products
        products = Product.objects.filter(id__in=selected_ids)
    else:
        # If no IDs are selected, fetch all products
        products = Product.objects.all()

    dollar_rate = Settings.objects.filter(key='dollar_rate').first().value

    if request.method == 'POST':
        cart_data = request.POST.get('cart_data')
        
        # Ensure cart data is valid
        if not cart_data:
            return render(request, 'store/sell_product.html', {
                'error': 'الرجاء تعبئة الحقول المطلوبة .',
                # 'products': Product.objects.all()
                'products': products
            })

        try:
            cart = json.loads(cart_data)  # Parse the JSON string into a Python list
            total_price = Decimal(0)

            # Create a new Sale instance
            sale = Sale.objects.create()
            serial_number=sale.id  # You can add a date or other fields if needed

            for item in cart:
                product_id = item['productId']
                quantity = item['quantity']
                profit_percentage = Decimal(item['profitPercentage']) / 100

                product = get_object_or_404(Product, id=product_id)

                # Calculate total price for this item
                cost_price = product.price
                selling_price = cost_price + (cost_price * profit_percentage)
                total_price += selling_price * quantity

                # Handle product quantity update
                if product.quantity < quantity:
                    return render(request, 'store/sell_product.html', {
                        'error': f'لا يوجد كمية كافية من {product.name}, لديك {product.quantity} قطع متبقية في المستودع .',
                        'products': products,
                    })

                # Update product quantity
                product.quantity -= quantity
                product.save()

                # Create SaleItem instance
                SaleItem.objects.create(sale=sale, product=product, quantity=quantity,price_at_sale=selling_price)

            total_syp_price = total_price * dollar_rate

            return render(request, 'store/sell_success.html', {
                'cart': cart,
                'serial_number':serial_number,
                'total_price': total_price,
                'total_syp_price': total_syp_price
            })

        except (ValueError, json.JSONDecodeError):
            return render(request, 'store/sell_product.html', {
                'error': 'Invalid input.',
                'products': products
            })

    return render(request, 'store/sell_product.html', {'products': products})


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================



def list_sales(request):
    # here 
    sales_message=""
    current_year = datetime.now().year
    months = [(i, f"{i:02d}") for i in range(1, 13)]  # List of tuples
    sales = Sale.objects.all()

    # Get the date range from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    single_date = request.GET.get('single_date')

    if start_date and end_date:
        # Convert string dates to datetime objects using the correct format
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Include the end date by setting the time to the end of the day
        end_date = end_date.replace(hour=23, minute=59, second=59)

        sales_message = f'المبيعات من تاريخ {start_date.strftime("%d/%m/%Y")} إلى تاريخ {end_date.strftime("%d/%m/%Y")}'
        # Filter sales within the date range
        sales = sales.filter(date__range=[start_date, end_date])
    elif single_date:
        # Convert single date to datetime object using the correct format
        single_date = datetime.strptime(single_date, '%Y-%m-%d')
        sales = sales.filter(date=single_date)
        sales_message = f'المبيعات في تاريخ {single_date.strftime("%d/%m/%Y")}'


    if  not start_date and not end_date and not single_date: #no filters => latest 20 sales
        sales = sales.order_by('-date', '-id')[:20]
        sales_message='اخر عمليات البيع'

    sales_data = []

    for sale in sales:
        total_items = SaleItem.objects.filter(sale=sale).aggregate(total=Sum('quantity'))['total'] or 0
        total_price = sum(item.price_at_sale * item.quantity for item in SaleItem.objects.filter(sale=sale))
        total_price_syp = sum(item.price_at_sale * item.quantity * item.dollar_rate_at_sale for item in SaleItem.objects.filter(sale=sale))
        sales_data.append({
            'sale': sale,
            'total_items': total_items,
            'total_price': total_price,
            'total_price_syp': total_price_syp
        })

    return render(request, 'store/list_sales.html', {'sales_message':sales_message,'sales_data': sales_data,'current_year': current_year,'months': months})


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    # try:
    #     sale = get_object_or_404(Sale, id=sale_id)
    # except Http404:
    #     return render(request, '404.html', status=404)  # Render your custom 404 page

    all_items_price = sum(item.price_at_sale * item.quantity for item in SaleItem.objects.filter(sale=sale))
    sale_items = SaleItem.objects.filter(sale=sale)

    # Calculate total prices for each item
    sale_item_details = []
    all_items_price_syp = 0
    for item in sale_items:
        total_price = item.price_at_sale * item.quantity  # Use the captured price
        all_items_price_syp += total_price * item.dollar_rate_at_sale
        sale_item_details.append({
            'product': item.product,
            'quantity': item.quantity,
            'price_per_item': item.price_at_sale,  # Use the captured price
            'dollar_rate_at_sale': item.dollar_rate_at_sale,
            'total_price': total_price,
            'total_syp_price': total_price * item.dollar_rate_at_sale
        })

    return render(request, 'store/sale_detail.html', {
        'sale': sale,
        'sale_items': sale_item_details,
        'all_items_price': all_items_price,
        'all_items_price_syp': all_items_price_syp
    })


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def settings_view(request):
    settings = Settings.objects.all()
        # Map keys to Arabic labels
    labels = {
        'dollar_rate': 'سعر الدولار :',
        'minimum': 'الحد الأدنى للكمية المتوفرة :',
    }

        # Prepare settings with labels
    settings_with_labels = [
        {
            'key': setting.key,
            'value': setting.value,
            'label': labels.get(setting.key, setting.key)  # Default to the key if no label is found
        }
        for setting in settings
    ]

    if request.method == 'POST':
        for setting in settings:
            # Get the new value from the POST data
            new_value = request.POST.get(setting.key)
            if new_value is not None:
                # Update the setting instance
                setting.value = new_value
                setting.save()
        return redirect('home')  # Redirect to the same page after saving

    # return render(request, 'store/settings.html', {'settings': settings,'labels': labels})
    return render(request, 'store/settings.html', {
        'settings': settings_with_labels,
    })


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # try:
    #     product = get_object_or_404(Product, id=product_id)
    # except Http404:
    #     return render(request, '404.html', status=404)  # Render your custom 404 page

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('home')  # Redirect back to product list
    else:
        form = ProductForm(instance=product)

    return render(request, 'store/product_detail.html', {
        'product_id': product.id,
        'form': form
    })


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def generate_pdf(request):
    if request.method == 'POST':
        month = request.POST.get('month')
        year = request.POST.get('year')
        sales_data = []
        
        # Fetch sales data for the selected month and year
        sales = Sale.objects.filter(date__year=year, date__month=month)

        # Add the sale detail for each sale
        for sale in sales:
            total_items = SaleItem.objects.filter(sale=sale).aggregate(total=Sum('quantity'))['total'] or 0
            total_price = sum(item.price_at_sale * item.quantity for item in SaleItem.objects.filter(sale=sale))
            total_price_syp = sum(item.price_at_sale * item.quantity * item.dollar_rate_at_sale for item in SaleItem.objects.filter(sale=sale))
            sales_data.append({
                'sale_id': sale.id,
                'date': sale.date.strftime("%Y-%m-%d"),
                'total_items': total_items,
                'total_price': total_price,
                'total_price_syp': total_price_syp
            })

        # Create a PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sales_{year}_{month}.pdf"'

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Create a table for sales data
        table_data = [['Sale ID', 'Date', 'Total Items', 'Total Price', 'Total Price (SYP)']]
        
        # Check if sales_data is empty
        if len(sales_data) == 0:
            table_data.append(['-', '-', '-', '-', '-'])  # Append a row with "No sales" message
        else:
            total_price_sum = 0
            total_price_syp_sum = 0
            
            for data in sales_data:
                table_data.append([
                    data['sale_id'],
                    data['date'],
                    data['total_items'],
                    f"{data['total_price']:.2f}",  # Format total price to 2 decimal places
                    f"{format_number_with_commas(data['total_price_syp'])}"
                ])
                total_price_sum += data['total_price']
                total_price_syp_sum += data['total_price_syp']

            # Append the totals row
            table_data.append([
                '',
                '',
                '',
                f"{total_price_sum:.2f}",  # Total price formatted to 2 decimal places
                f"{format_number_with_commas(total_price_syp_sum)}"  # Total price in SYP as an integer
            ])

        # Create a title for the report
        styles = getSampleStyleSheet()
        title = Paragraph(f'Sales Report for Month: {month} - Year: {year}', styles['Title'])

        # Create the table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        # Build the PDF
        elements = [title, table]
        doc.build(elements)

        # Get the PDF from the buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
    

# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================
    
def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def import_products(request):
    context = {
        'success': False,
        'error': None,
        'file_received': False,
    }

    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        
        if not excel_file:
            context['error'] = 'الرجاء تحميل ملف Excel.'
            return render(request, 'store/import_products.html', context)

        context['file_received'] = True
        print("File received:", excel_file.name)  # Debugging

        try:
            # Read the Excel file
            df = pd.read_excel(excel_file)

            # Check if required columns exist
            required_columns = ['name', 'price', 'quantity']
            if not all(column in df.columns for column in required_columns):
                context['error'] = f'الملف يجب أن يحتوي على الأعمدة التالية : ({" - ".join(required_columns)}) و عمود للوصف : description (اختياري)'
                return render(request, 'store/import_products.html', context)

            # Iterate over rows and create Product objects
            for index, row in df.iterrows():
                try:
                    # Create a new Product object
                    product = Product(
                        name=row['name'],
                        description=row.get('description', ''),
                        price=float(row['price']),  # Ensure price is a float
                        quantity=int(row['quantity'])  # Ensure quantity is an integer
                    )
                    product.save()  # Save the product to the database
                    print(f"Product saved: {product.name}")  # Debugging
                except Exception as e:
                    print(f"Error processing row {index}: {e}")  # Debugging

            context['success'] = True
        except Exception as e:
            context['error'] = f'حدث خطأ أثناء استيراد المنتجات: {str(e)}'

    return render(request, 'store/import_products.html', context)


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def sales_statistics(request):
    form = DateRangeForm(request.GET or None)
    sales = Sale.objects.none()  # Empty queryset by default
    total_income = 0
    total_revenue = 0
    total_products_sold = 0
    most_sold_product = None
    income_over_time = []
    revenue_over_time = []
    products_sold_over_time = []
    labels = []

    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        # Filter sales within the date range
        # sales = Sale.objects.filter(date__range=(start_date, end_date))
        sales = Sale.objects.filter(date__gte=start_date, date__lte=end_date)

        # Calculate total income (including quantity)
        total_income = SaleItem.objects.filter(sale__in=sales).annotate(
            total_item_income=F('price_at_sale') * F('quantity')
        ).aggregate(
            total_income=Sum('total_item_income')
        )['total_income'] or 0

        # Calculate total revenue (net profit, including quantity)
        total_revenue = SaleItem.objects.filter(sale__in=sales).annotate(
            net_profit=(F('price_at_sale') - F('product__price')) * F('quantity')
        ).aggregate(
            total_revenue=Sum('net_profit')
        )['total_revenue'] or 0

        # Calculate total products sold
        total_products_sold = SaleItem.objects.filter(sale__in=sales).aggregate(
            total_products_sold=Sum('quantity')
        )['total_products_sold'] or 0

        # Find the most sold product
        most_sold_product = SaleItem.objects.filter(sale__in=sales).values(
            'product__name'
        ).annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold').first()

        # Prepare data for the chart
        # sales_over_time = Sale.objects.filter(date__range=(start_date, end_date)).annotate(
        sales_over_time = Sale.objects.filter(date__gte=start_date, date__lte=end_date).annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            total_income=Sum(F('saleitem__price_at_sale') * F('saleitem__quantity')),  # Multiply by quantity
            total_products=Sum('saleitem__quantity'),
            total_revenue=Sum((F('saleitem__price_at_sale') - F('saleitem__product__price')) * F('saleitem__quantity'))  # Multiply by quantity
        ).order_by('day')

        for entry in sales_over_time:
            labels.append(entry['day'].strftime('%Y-%m-%d'))
            income_over_time.append(float(entry['total_income'] or 0))
            revenue_over_time.append(float(entry['total_revenue'] or 0))
            products_sold_over_time.append(entry['total_products'] or 0)

    context = {
        'form': form,
        'total_income': total_income,
        'total_revenue': total_revenue,
        'total_products_sold': total_products_sold,
        'most_sold_product': most_sold_product,
        'labels': labels,
        'income_over_time': income_over_time,
        'revenue_over_time': revenue_over_time,
        'products_sold_over_time': products_sold_over_time,
    }

    return render(request, 'store/sales_statistics.html', context)


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================