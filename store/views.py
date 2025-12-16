# Standard Library Imports (Python Built-ins)
from decimal import Decimal
from datetime import datetime
from io import BytesIO

# Third-Party Library Imports (Django, ReportLab, Pandas, etc.)
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q, F, Count
from django.db.models.functions import TruncDay
from django.forms import formset_factory

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

import json
import pandas as pd

# Local Application/Project Imports
from .models import Product, Settings, Sale, SaleItem, Classification,FinancialBox
from .forms import ProductBulkAddForm, ProductForm, DateRangeForm

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
    # products = Product.objects.all()
    products = Product.objects.filter(is_active=True)

    # store_products_price = products.aggregate(
    #     total=Sum(F('quantity') * F('price'))
    # )['total'] or 0
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
        elif classification_filter=="weight-category":
            products=products.filter(is_weight=True) # no classification 
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
            # 'store_products_price':store_products_price,
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

# def classifications_list(request):
#     # Fetch all classifications and annotate them with the count of related products and sum of quantities
#     classifications = Classification.objects.annotate(
#         product_type_count=Count('product', distinct=True),  # Count distinct products
#         all_types_count=Sum('product__quantity')  # Sum the quantities of related products
#     ).order_by('category')

#     return render(
#         request,
#         'store/classifications_list.html',
#         {
#             'classifications': classifications,
#         },
#     )



def classifications_list(request):
    # Fetch all classifications and annotate them with the count of related products and sum of quantities
    # نستخدم prefetch_related لتحسين الأداء لاحقاً عند الوصول إلى المنتجات في القالب
    classifications = Classification.objects.annotate(
        product_type_count=Count('product', distinct=True),
        all_types_count=Sum('product__quantity')
    ).prefetch_related('product_set').order_by('category')

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
    return redirect('classifications_list')

# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================
# def add_product(request):
#     if request.method == "POST":
        
#         # --- 1. Get All POST Data ---
#         name = request.POST.get('name')
#         product_type = request.POST.get('type') # Renamed 'type' to 'product_type' to avoid shadowing built-in 'type'
#         items_per_package_str = request.POST.get('items_per_package')
#         description = request.POST.get('description')
#         price_str = request.POST.get('price')
#         quantity_str = request.POST.get('quantity')
#         classification_id = request.POST.get('classification')
#         is_weight = product_type == 'weight'
#         retail_sale_percent = request.POST.get('retail_sale_percent')
#         whole_sale_percent = request.POST.get('whole_sale_percent')

#         if not retail_sale_percent:
#             retail_sale_percent = 5
#         if not whole_sale_percent:
#             whole_sale_percent = 3
            
#         # Helper to simplify error rendering
#         def render_error(error_message):
#             return render(request, 'store/add_product.html', {
#                 'error': error_message,
#                 'classifications': Classification.objects.all()
#             })

#         # --- 2. Basic Validation & Type Conversion ---
#         if not all([name, price_str, quantity_str]):
#             return render_error('الرجاء تعبئة الحقول المطلوبة (المادة و السعر و الكمية)')
        
#         try:
#             entered_price = float(price_str)
#         except ValueError:
#             return render_error('السعر يجب أن يكون رقماً صالحاً')

#         # --- 3. Handle Different Product Types ---
#         final_price_per_unit = entered_price
#         final_quantity_of_items = 0  # Will be calculated differently based on type

#         if product_type == "many":
#             if not items_per_package_str:
#                 return render_error('يرجى تحديد عدد القطع في الطرد')
            
#             try:
#                 items_per_package = int(items_per_package_str)
#                 if items_per_package <= 0:
#                     raise ValueError
#                 entered_quantity = int(quantity_str)
#                 if entered_quantity <= 0:
#                     raise ValueError
#             except ValueError:
#                 return render_error('عدد القطع في الطرد والكمية يجب أن يكونا رقمين صحيحين وموجبين')

#             # Calculation for the database:
#             # Price per piece = Package Price / Items per Package
#             final_price_per_unit = entered_price / items_per_package
            
#             # Total quantity of items = Number of Packages * Items per Package
#             final_quantity_of_items = entered_quantity * items_per_package

#         elif product_type == "weight":
#             try:
#                 # Allow decimal values for weight
#                 entered_quantity = float(quantity_str)
#                 if entered_quantity <= 0:
#                     raise ValueError
#             except ValueError:
#                 return render_error('الكمية (Kg) يجب أن يكون رقماً موجباً')

#             # For weight, convert to grams (or keep as kg depending on your needs)
#             # Option 1: Store in grams (multiply by 1000)
#             final_quantity_of_items = int(entered_quantity * 1000)  # Convert kg to grams
            
#             # Price per gram (or per kg depending on your business logic)
#             # If price is entered per kg, store price per gram
#             final_price_per_unit = entered_price / 1000  # Price per gram
            
#             # Option 2: Store in kg with decimal
#             # final_quantity_of_items = entered_quantity  # Store as decimal kg
#             # final_price_per_unit = entered_price  # Price per kg

#         else:  # product_type == "one" (مفرد)
#             try:
#                 entered_quantity = int(quantity_str)
#                 if entered_quantity <= 0:
#                     raise ValueError
#             except ValueError:
#                 return render_error('الكمية (عدد القطع) يجب أن يكون رقماً صحيحاً وموجباً')
            
#             final_quantity_of_items = entered_quantity
#             final_price_per_unit = entered_price

#         # --- 4. Handle Classification Lookup ---
#         classification = None
#         if classification_id:
#             try:
#                 # Fetch the Classification instance using the ID
#                 classification = Classification.objects.get(id=classification_id)
#             except Classification.DoesNotExist:
#                 return render_error('التصنيف المحدد غير صحيح')

#         # --- 5. Create Product in Database ---
#         Product.objects.create(
#             is_weight=is_weight,
#             name=name,
#             description=description,
#             price=final_price_per_unit,          # Store the calculated price per single item
#             quantity=final_quantity_of_items,    # Store the calculated total quantity
#             classification=classification,        # Pass the Classification instance or None
#             retail_sale_percent=retail_sale_percent,
#             whole_sale_percent=whole_sale_percent
#         )
        
#         return redirect('add_product')
        
#     # --- GET Request ---
#     return render(request, 'store/add_product.html', {
#         'classifications': Classification.objects.all()
#     })

from django.db import IntegrityError

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
        is_weight = product_type == 'weight'
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
                'classifications': Classification.objects.all(),
                'form_data': request.POST  # Pass form data back to preserve user input
            })

        # --- 2. Basic Validation & Type Conversion ---
        if not all([name, price_str, quantity_str]):
            return render_error('الرجاء تعبئة الحقول المطلوبة (المادة و السعر و الكمية)')
        
        try:
            entered_price = float(price_str)
        except ValueError:
            return render_error('السعر يجب أن يكون رقماً صالحاً')

        # --- 3. Handle Different Product Types ---
        final_price_per_unit = entered_price
        final_quantity_of_items = 0  # Will be calculated differently based on type

        if product_type == "many":
            if not items_per_package_str:
                return render_error('يرجى تحديد عدد القطع في الطرد')
            
            try:
                items_per_package = int(items_per_package_str)
                if items_per_package <= 0:
                    raise ValueError
                entered_quantity = int(quantity_str)
                if entered_quantity <= 0:
                    raise ValueError
            except ValueError:
                return render_error('عدد القطع في الطرد والكمية يجب أن يكونا رقمين صحيحين وموجبين')

            # Calculation for the database:
            # Price per piece = Package Price / Items per Package
            final_price_per_unit = entered_price / items_per_package
            
            # Total quantity of items = Number of Packages * Items per Package
            final_quantity_of_items = entered_quantity * items_per_package

        elif product_type == "weight":
            try:
                # Allow decimal values for weight
                entered_quantity = float(quantity_str)
                if entered_quantity <= 0:
                    raise ValueError
            except ValueError:
                return render_error('الكمية (Kg) يجب أن يكون رقماً موجباً')

            # For weight, convert to grams (or keep as kg depending on your needs)
            # Option 1: Store in grams (multiply by 1000)
            final_quantity_of_items = int(entered_quantity * 1000)  # Convert kg to grams
            
            # Price per gram (or per kg depending on your business logic)
            # If price is entered per kg, store price per gram
            final_price_per_unit = entered_price / 1000  # Price per gram
            
            # Option 2: Store in kg with decimal
            # final_quantity_of_items = entered_quantity  # Store as decimal kg
            # final_price_per_unit = entered_price  # Price per kg

        else:  # product_type == "one" (مفرد)
            try:
                entered_quantity = int(quantity_str)
                if entered_quantity < 0:
                    raise ValueError
            except ValueError:
                return render_error('الكمية (عدد القطع) يجب أن يكون رقماً صحيحاً وموجباً')
            
            final_quantity_of_items = entered_quantity
            final_price_per_unit = entered_price

        # --- 4. Handle Classification Lookup ---
        classification = None
        if classification_id:
            try:
                # Fetch the Classification instance using the ID
                classification = Classification.objects.get(id=classification_id)
            except Classification.DoesNotExist:
                return render_error('التصنيف المحدد غير صحيح')

        # --- 5. Check if product name already exists (OPTIONAL - for better UX) ---
        # This check is optional since the database constraint will catch it,
        # but it provides a better user experience with a cleaner error message
        if Product.objects.filter(name=name).exists():
            return render_error(f'المادة "{name}" موجودة مسبقاً في النظام. الرجاء استخدام اسم مختلف.')

        # --- 6. Create Product in Database ---
        try:
            Product.objects.create(
                is_weight=is_weight,
                name=name,
                description=description,
                price=final_price_per_unit,          # Store the calculated price per single item
                quantity=final_quantity_of_items,    # Store the calculated total quantity
                classification=classification,        # Pass the Classification instance or None
                retail_sale_percent=retail_sale_percent,
                whole_sale_percent=whole_sale_percent
            )
        except IntegrityError as e:
            # Catch the database-level unique constraint violation
            if 'name' in str(e) or 'unique' in str(e).lower():
                return render_error(f'المادة "{name}" موجودة مسبقاً في النظام. الرجاء استخدام اسم مختلف.')
            else:
                # For other database errors
                return render_error('حدث خطأ في قاعدة البيانات. الرجاء المحاولة مرة أخرى.')
        
        return redirect('add_product')
        
    # --- GET Request ---
    return render(request, 'store/add_product.html', {
        'classifications': Classification.objects.all()
    })
# def add_product(request):
#     if request.method == "POST":
        
#         # --- 1. Get All POST Data ---
#         name = request.POST.get('name')
#         product_type = request.POST.get('type') # Renamed 'type' to 'product_type' to avoid shadowing built-in 'type'
#         items_per_package_str = request.POST.get('items_per_package')
#         description = request.POST.get('description')
#         price_str = request.POST.get('price')
#         quantity_str = request.POST.get('quantity')
#         classification_id = request.POST.get('classification')
#         is_weight = product_type == 'weight'
#         retail_sale_percent = request.POST.get('retail_sale_percent')
#         whole_sale_percent = request.POST.get('whole_sale_percent')

#         if not retail_sale_percent:
#             retail_sale_percent = 5
#         if not whole_sale_percent:
#             whole_sale_percent = 3
#         # Helper to simplify error rendering
#         def render_error(error_message):
#             return render(request, 'store/add_product.html', {
#                 'error': error_message,
#                 'classifications': Classification.objects.all()
#             })

#         # --- 2. Basic Validation & Type Conversion ---
#         if not all([name, price_str, quantity_str]):
#             return render_error('الرجاء تعبئة الحقول المطلوبة (المادة و السعر و الكمية)')
        
#         try:
#             entered_price = float(price_str)
#             entered_quantity = int(quantity_str)
#         except ValueError:
#             return render_error('السعر والكمية يجب أن تكون أرقامًا صالحة')

#         # Variables to store the final, calculated values for the database
#         final_price_per_unit = entered_price
#         final_quantity_of_items = entered_quantity

#         # --- 3. Handle 'many' (Package) Scenario ---
#         if product_type == "many":
#             if not items_per_package_str:
#                 return render_error('يرجى تحديد عدد القطع في الطرد')
            
#             try:
#                 items_per_package = int(items_per_package_str)
#                 if items_per_package <= 0:
#                     raise ValueError
#             except ValueError:
#                 return render_error('عدد القطع في الطرد يجب أن يكون رقمًا صحيحًا وموجبًا')

#             # Calculation for the database:
#             # Price per piece = Package Price / Items per Package
#             final_price_per_unit = entered_price / items_per_package
            
#             # Total quantity of items = Number of Packages * Items per Package
#             final_quantity_of_items = entered_quantity * items_per_package

#         if product_type == "weight":

#             # Calculation for the database:
#             # Price per piece = Package Price / Items per Package
#             final_price_per_unit = entered_price / 1000
            
#             # Total quantity of items = Number of Packages * Items per Package
#             final_quantity_of_items = entered_quantity *1000
#         # If product_type is "one", final_price_per_unit and final_quantity_of_items
#         # already hold the entered_price and entered_quantity, so no change is needed.


#         # --- 4. Handle Classification Lookup ---
#         classification = None
#         if classification_id:
#             try:
#                 # Fetch the Classification instance using the ID
#                 classification = Classification.objects.get(id=classification_id)
#             except Classification.DoesNotExist:
#                 return render_error('التصنيف المحدد غير صحيح')

#         # --- 5. Create Product in Database ---
#         Product.objects.create(
#             is_weight=is_weight,
#             name=name,
#             description=description,
#             price=final_price_per_unit,          # Store the calculated price per single item
#             quantity=final_quantity_of_items,    # Store the calculated total quantity of single items
#             classification=classification,        # Pass the Classification instance or None
#             # tareek
#             retail_sale_percent=retail_sale_percent,
#             whole_sale_percent=whole_sale_percent
#         )
        
#         return redirect('add_product')
        
#     # --- GET Request ---
#     return render(request, 'store/add_product.html', {
#         'classifications': Classification.objects.all()
#     })

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
        category = request.POST.get('category', '').strip()

        if category:
            Classification.objects.create(category=category)
            # If it's an AJAX request (from the modal), return success JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Classification added successfully.'})
            # Otherwise, for a regular POST, redirect as before
            return redirect('classifications_list')
        else:
            error_message = 'الرجاء تعبئة الحقول المطلوبة'
            # For an AJAX request, return failure JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_message}, status=400)
            # Otherwise, render the error in the original page context
            return render(request, 'store/add_classification.html', {
                'error': error_message,
            })
    
    # This part remains for displaying the modal content if it needs to be loaded separately, 
    # but for a simple modal, you'll likely just use the template below.
    return render(request, 'store/add_classification.html')

# def add_classification(request):
#     if request.method == "POST":
#         category = request.POST['category']
#         if category:
#             Classification.objects.create(category=category)
#             return redirect('classifications_list')
#         else:
#             return render(request, 'store/add_classification.html', {
#                 'error': 'الرجاء تعبئة الحقول المطلوبة',
#             })
#     return render(request, 'store/add_classification.html')


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================

def remove_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # product.delete()
    product.safe_delete()
    return redirect('product_list')




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
        # products = Product.objects.all()
        products = Product.objects.filter(is_active=True)

    dollar_rate = Settings.objects.filter(key='dollar_rate').first().value

    if request.method == 'POST':
        cart_data = request.POST.get('cart_data')
        payable_price=request.POST.get('payablePrice')
        
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
            # sale = Sale.objects.create()
            sale = Sale.objects.create(
                total_payable_price=payable_price
            )
            serial_number=sale.id  # You can add a date or other fields if needed
            box = FinancialBox.objects.get() 
    
    # Use F() expression to perform atomic update (highly recommended for concurrency)
            box.current_amount = F('current_amount') + payable_price 
            box.save()

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
                'payablePrice':payable_price,
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



# def list_sales(request):
#     # here 
#     sales_message=""
#     current_year = datetime.now().year
#     months = [(i, f"{i:02d}") for i in range(1, 13)]  # List of tuples
#     sales = Sale.objects.all()

#     # Get the date range from the request
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')
#     single_date = request.GET.get('single_date')

#     if start_date and end_date:
#         # Convert string dates to datetime objects using the correct format
#         start_date = datetime.strptime(start_date, '%Y-%m-%d')
#         end_date = datetime.strptime(end_date, '%Y-%m-%d')

#         # Include the end date by setting the time to the end of the day
#         end_date = end_date.replace(hour=23, minute=59, second=59)

#         sales_message = f'المبيعات من تاريخ {start_date.strftime("%d/%m/%Y")} إلى تاريخ {end_date.strftime("%d/%m/%Y")}'
#         # Filter sales within the date range
#         sales = sales.filter(date__range=[start_date, end_date])
#     elif single_date:
#         # Convert single date to datetime object using the correct format
#         single_date = datetime.strptime(single_date, '%Y-%m-%d')
#         sales = sales.filter(date=single_date)
#         sales_message = f'المبيعات في تاريخ {single_date.strftime("%d/%m/%Y")}'


#     if  not start_date and not end_date and not single_date: #no filters => latest 20 sales
#         sales = sales.order_by('-date', '-id')[:20]
#         sales_message='اخر عمليات البيع'

#     sales_data = []

#     for sale in sales:
#         total_items = SaleItem.objects.filter(sale=sale).aggregate(total=Sum('quantity'))['total'] or 0
#         total_price = sum(item.price_at_sale * item.quantity for item in SaleItem.objects.filter(sale=sale))
#         total_price_syp = sum(item.price_at_sale * item.quantity * item.dollar_rate_at_sale for item in SaleItem.objects.filter(sale=sale))
#         sales_data.append({
#             'sale': sale,
#             'total_items': total_items,
#             'total_price': total_price,
#             'total_price_syp': total_price_syp
#         })

#     return render(request, 'store/list_sales.html', {'sales_message':sales_message,'sales_data': sales_data,'current_year': current_year,'months': months})

def list_sales(request):
    sales_message = ""
    current_year = datetime.now().year
    months = [(i, f"{i:02d}") for i in range(1, 13)]  # List of tuples
    sales = Sale.objects.all()

    # Get the date range from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    single_date = request.GET.get('single_date')
    sale_id = request.GET.get('sale_id')  # Get sale_id from request

    # Handle sale_id search first (highest priority)
    if sale_id:
        try:
            sale_id_int = int(sale_id)
            sales = sales.filter(id=sale_id_int)
            if sales.exists():
                sales_message = f'نتائج البحث عن العملية رقم {sale_id}'
            else:
                sales_message = f'لا توجد عملية بيع بالرقم {sale_id}'
        except ValueError:
            sales_message = 'رقم العملية غير صالح'
            sales = Sale.objects.none()
    
    # If no sale_id search, apply date filters
    elif start_date and end_date:
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
    
    # If no filters applied, show latest 20 sales
    elif not start_date and not end_date and not single_date and not sale_id:
        sales = sales.order_by('-date', '-id')[:20]
        sales_message = 'اخر عمليات البيع'

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

    return render(request, 'store/list_sales.html', {
        'sales_message': sales_message,
        'sales_data': sales_data,
        'current_year': current_year,
        'months': months
    })
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
            return redirect('product_list')  # Redirect back to product list
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
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return HttpResponse("Invalid dates", status=400)

        # 1. SALES DATA PROCESSING (Unchanged from your code)
        sales_data = []
        sales = Sale.objects.filter(date__range=(start_date, end_date)).order_by('date')
        
        total_sell_sum = 0
        total_buy_sum = 0
        total_profit_sum = 0
        total_quantity_sum = 0

        for sale in sales:
            items = SaleItem.objects.filter(sale=sale)

            total_items = items.aggregate(total=Sum('quantity'))['total'] or 0

            total_sell_price_syp = 0
            total_buy_price_syp = 0

            for item in items:
                sell_price_syp = item.price_at_sale * item.quantity * item.dollar_rate_at_sale
                buy_price_syp = item.product.price * item.quantity * item.dollar_rate_at_sale

                total_sell_price_syp += sell_price_syp
                total_buy_price_syp += buy_price_syp

            profit = total_sell_price_syp - total_buy_price_syp

            data = {
                'sale_id': sale.id,
                'date': sale.date.strftime("%Y-%m-%d"),
                'total_items': total_items,
                'total_price_sell_syp': total_sell_price_syp,
                'total_price_buy_syp': total_buy_price_syp,
                'total_profit': profit,
            }
            sales_data.append(data)

            total_sell_sum += data['total_price_sell_syp']
            total_buy_sum += data['total_price_buy_syp']
            total_profit_sum += data['total_profit']
            total_quantity_sum += data['total_items']
            


        # 4. PREPARE PDF RESPONSE (Modified)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Sales Report ( {start_date} to {end_date} ).pdf"'

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_text = f"Sales Report: {start_date} to {end_date}"
        title = Paragraph(title_text, styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Sales Table Title
        sales_title = Paragraph("Sales Summary", styles['h2'])
        elements.append(sales_title)

        # Sales Table Data (Table 1)
        sales_table_data = [['Sale ID', 'Date', 'Price (Buy)', 'Price (Sell)', 'Profit']]

        if not sales_data:
            sales_table_data.append(['No Sales Found', '', '', '', '', ''])
        else:
            for data in sales_data:
                sales_table_data.append([
                    data['sale_id'],
                    data['date'],
                    # data['total_items'],
                    f"{data['total_price_buy_syp']:,.0f}",
                    f"{data['total_price_sell_syp']:,.0f}",
                    f"{data['total_profit']:,.0f}",
                ])

            # Add totals row
            sales_table_data.append([
                # Paragraph("<b>Total</b>", styles['Normal']), '',
                '',
                '',
                # f"{total_quantity_sum}",
                f"{total_buy_sum:,.0f}",
                f"{total_sell_sum:,.0f}",
                f"{total_profit_sum:,.0f}",
            ])

        sales_table = Table(sales_table_data, colWidths=[90, 60, 100, 100, 100])

        # Sales Table Styling (Unchanged)
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10), # Reduced font size for better fit
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9), # Reduced font size for better fit
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F3F4F6")),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, -1), (1, -1), 'LEFT'),
            ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor("#DCFCE7")),
            ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor("#166534")),
            ('SPAN', (0, -1), (1, -1)),
        ]))
        
        elements.append(sales_table)
        elements.append(Spacer(1, 24))

        # Build the PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
    
    return HttpResponse("This view only accepts POST requests with date parameters.", status=405)

# def generate_pdf(request):
#     if request.method == 'POST':
#         month = request.POST.get('month')
#         year = request.POST.get('year')
#         sales_data = []
        
#         # Fetch sales data for the selected month and year
#         sales = Sale.objects.filter(date__year=year, date__month=month)

#         # Add the sale detail for each sale
#         for sale in sales:
#             total_items = SaleItem.objects.filter(sale=sale).aggregate(total=Sum('quantity'))['total'] or 0
#             total_price = sum(item.price_at_sale * item.quantity for item in SaleItem.objects.filter(sale=sale))
#             total_price_syp = sum(item.price_at_sale * item.quantity * item.dollar_rate_at_sale for item in SaleItem.objects.filter(sale=sale))
#             sales_data.append({
#                 'sale_id': sale.id,
#                 'date': sale.date.strftime("%Y-%m-%d"),
#                 'total_items': total_items,
#                 'total_price': total_price,
#                 'total_price_syp': total_price_syp
#             })

#         # Create a PDF response
#         response = HttpResponse(content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="sales_{year}_{month}.pdf"'

#         # Create PDF
#         buffer = BytesIO()
#         doc = SimpleDocTemplate(buffer, pagesize=letter)
        
#         # Create a table for sales data
#         table_data = [['Sale ID', 'Date', 'Total Items', 'Total Price', 'Total Price (SYP)']]
        
#         # Check if sales_data is empty
#         if len(sales_data) == 0:
#             table_data.append(['-', '-', '-', '-', '-'])  # Append a row with "No sales" message
#         else:
#             total_price_sum = 0
#             total_price_syp_sum = 0
            
#             for data in sales_data:
#                 table_data.append([
#                     data['sale_id'],
#                     data['date'],
#                     data['total_items'],
#                     f"{data['total_price']:.2f}",  # Format total price to 2 decimal places
#                     f"{format_number_with_commas(data['total_price_syp'])}"
#                 ])
#                 total_price_sum += data['total_price']
#                 total_price_syp_sum += data['total_price_syp']

#             # Append the totals row
#             table_data.append([
#                 '',
#                 '',
#                 '',
#                 f"{total_price_sum:.2f}",  # Total price formatted to 2 decimal places
#                 f"{format_number_with_commas(total_price_syp_sum)}"  # Total price in SYP as an integer
#             ])

#         # Create a title for the report
#         styles = getSampleStyleSheet()
#         title = Paragraph(f'Sales Report for Month: {month} - Year: {year}', styles['Title'])

#         # Create the table
#         table = Table(table_data)
#         table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('GRID', (0, 0), (-1, -1), 1, colors.black),
#         ]))

#         # Build the PDF
#         elements = [title, table]
#         doc.build(elements)

#         # Get the PDF from the buffer
#         pdf = buffer.getvalue()
#         buffer.close()
#         response.write(pdf)
#         return response
    

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



# def add_bulk_products(request):
    
#     # استخدام النموذج الجديد لإنشاء الـ FormSet
#     ProductFormSet = formset_factory(ProductBulkAddForm, extra=1) # يمكنك تغيير 5 إلى أي عدد صفوف تريده

#     if request.method == 'POST':
#         formset = ProductFormSet(request.POST, prefix='products')
        
#         if formset.is_valid():
#             for form in formset:
#                 # التحقق أن الصف ليس فارغاً
#                 if form.has_changed() and form.cleaned_data.get('name'):
                    
#                     product_name = form.cleaned_data.get('name')
#                     # هذه هي الكمية المدخلة في النموذج
#                     quantity_to_add = form.cleaned_data.get('quantity', 0) 
                    
#                     try:
#                         # 1. البحث في قاعدة البيانات
#                         product = Product.objects.get(name__iexact=product_name)
                        
#                         # 2. المنتج موجود: زيادة الكمية فقط
#                         product.quantity += quantity_to_add
#                         product.save(update_fields=['quantity'])
                    
#                     except Product.DoesNotExist:
#                         # 3. المنتج غير موجود: إنشاء منتج جديد
#                         # استدعاء .save() هنا آمن لأنه سيستخدم 
#                         # دالة .save() الافتراضية (وليس المخصصة)
#                         new_product = form.save() 

#             # غير 'store:product_list' إلى اسم المسار الصحيح لصفحة قائمة المنتجات
#             return redirect('product_list') 

#     else:
#         formset = ProductFormSet(prefix='products')

#     # استخدم نفس القالب المقترح سابقاً
#     return render(request, 'store/add_bulk_products.html', {'formset': formset})


# store/views.py

def add_bulk_products(request):
    
    # أضف can_delete=True
    ProductFormSet = formset_factory(ProductBulkAddForm, extra=1, can_delete=True)

    if request.method == 'POST':
        formset = ProductFormSet(request.POST, prefix='products')
        
        if formset.is_valid():
            for form in formset:
                
                # --- أضف هذا التحقق ---
                # إذا كان المربع "DELETE" محدداً، تجاهل هذا الصف
                if form.cleaned_data.get('DELETE'):
                    continue  # اذهب إلى الصف التالي
                # --- نهاية التحقق ---

                # التحقق أن الصف ليس فارغاً
                if form.has_changed() and form.cleaned_data.get('name'):
                    
                    product_name = form.cleaned_data.get('name')
                    quantity_to_add = form.cleaned_data.get('quantity', 0) 
                    
                    try:
                        product = Product.objects.get(name__iexact=product_name)
                        product.quantity += quantity_to_add
                        product.save(update_fields=['quantity'])
                    
                    except Product.DoesNotExist:
                        new_product = form.save() 

            return redirect('product_list') 

    else:
        formset = ProductFormSet(prefix='products')

    return render(request, 'store/add_bulk_products.html', {'formset': formset})














from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from .models import Trader, Transaction
from .forms import TraderForm, TransactionForm
from django.urls import reverse

# --- Trader Management Views ---

def trader_list(request):
    """Displays a list of all traders with their current balances."""
    traders = Trader.objects.all().order_by('name')
    context = {
        'traders': traders,
    }
    return render(request, 'store/traders/trader_list.html', context)

def add_trader(request):
    """Handles adding a new trader."""
    if request.method == 'POST':
        form = TraderForm(request.POST)
        if form.is_valid():
            trader = form.save()
            return redirect('trader_detail', pk=trader.pk)
    else:
        form = TraderForm()
    
    context = {
        'form': form,
    }
    return render(request, 'store/traders/add_trader.html', context)

def trader_detail(request, pk):
    """Displays details and all transactions for a specific trader."""
    trader = get_object_or_404(Trader, pk=pk)
    transactions = trader.transactions.all()
    
    context = {
        'trader': trader,
        'transactions': transactions,
    }
    return render(request, 'store/traders/trader_detail.html', context)


# --- Transaction Management Views ---

def add_transaction(request, trader_pk):
    """Handles adding a new transaction (Purchase or Payment) for a trader."""
    trader = get_object_or_404(Trader, pk=trader_pk)

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.trader = trader
            transaction.save() # The save method updates the trader balance
# ⭐️ NEW BOX UPDATE LOGIC ⭐️
            
            # Check if the transaction is a PAYMENT (Cash is leaving the store)
            if transaction.transaction_type == Transaction.TransactionType.PAYMENT:
                try:
                    # Retrieve the single FinancialBox instance
                    box = FinancialBox.objects.get() 
                    
                    # Atomically decrease the box amount by the transaction amount
                    # Using F() is crucial to prevent race conditions.
                    box.current_amount = F('current_amount') - transaction.amount
                    box.save(update_fields=['current_amount'])
                    
                    # Optional: Check if the amount went negative (cash shortage)
                    # For simple logic, we rely on the database, but a proper check 
                    # should be done client-side or before saving to prevent overdrawing.
                    
                except FinancialBox.DoesNotExist:
                    # Log or handle the error if the FinancialBox object is missing
                    print("Error: FinancialBox object not found.")
                
            # ⭐️ END BOX UPDATE LOGIC ⭐️
            return redirect('trader_detail', pk=trader.pk)
    else:
        form = TransactionForm()
    
    context = {
        'form': form,
        'trader': trader,
    }
    return render(request, 'store/traders/add_transaction.html', context)











# store/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Sale, SaleItem, Settings # Import your models
from .printer_utils import print_receipt_usb # Import the utility we made

def print_receipt(request, serial_number):
    # 1. Fetch the Sale
    sale = get_object_or_404(Sale, id=serial_number)
    
    # 2. Fetch the Items associated with this sale
    sale_items = SaleItem.objects.filter(sale=sale)
    
    # 3. Prepare data for the printer
    printer_items = []
    
    for item in sale_items:
        # Calculate Total SYP for this line: 
        syp_unit_price = item.price_at_sale * item.dollar_rate_at_sale
        total_syp_line = syp_unit_price * item.quantity
        
        # Check if product is sold by weight
        if item.product.is_weight:
            # Convert from grams to Kg with 2 decimal places
            display_quantity = item.quantity / 1000
            # display_quantity_str = f"{display_quantity:.2f} Kg"  # 2 decimal places + " kg"
            # display_quantity_str = f"{display_quantity:.2f}Kg"  # 2 decimal places + " kg"
            display_quantity_str = f"{display_quantity:.2f} كغ"  # 2 decimal places + " kg"
        else:
            # For non-weight products, just show the quantity
            display_quantity = item.quantity
            display_quantity_str = str(item.quantity)

        printer_items.append({
            'product_name': item.product.name,
            # 'quantity': item.quantity,  # Original quantity in grams/units
            'quantity': display_quantity_str,  # Formatted for display
            # 'display_quantity_raw': display_quantity,  # Numeric value for calculations if needed
            'total_price': total_syp_line,
            # 'is_weight': item.product.is_weight
        })

    # Format the final payable price
    payable_display = sale.total_payable_price
    date_display = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    # print(printer_items)
    # 4. Trigger the Print
    success, msg = print_receipt_usb(
        serial_number=serial_number,
        cart_items=printer_items,
        total_payable=payable_display,
        date_str=date_display
    )

    if success:
        messages.success(request, "تمت الطباعة بنجاح")
    else:
        messages.error(request, f"خطأ في الطباعة: {msg}")

    return redirect('home')

# def print_receipt(request, serial_number):
#     # 1. Fetch the Sale
#     sale = get_object_or_404(Sale, id=serial_number)
    
#     # 2. Fetch the Items associated with this sale
#     sale_items = SaleItem.objects.filter(sale=sale)
    
#     # 3. Prepare data for the printer
#     # We need to calculate the SYP price per line item based on the stored data
#     printer_items = []
    
#     for item in sale_items:
#         # Calculate Total SYP for this line: 
#         # (Price USD * Rate) * Quantity
#         syp_unit_price = item.price_at_sale * item.dollar_rate_at_sale
#         total_syp_line = syp_unit_price * item.quantity
#         # Access product.is_weight
#         # is_weight_product = item.product.is_weight

#         printer_items.append({
#             'product_name': item.product.name,
#             'quantity': item.quantity,
#             'total_price': total_syp_line
#         })

#     # Format the final payable price
#     # Assuming total_payable_price in Sale model is already in SYP 
#     # (Based on your template {{payablePrice|intcomma}})
#     # payable_display = "{:,}".format(sale.total_payable_price)
#     payable_display = sale.total_payable_price
#     # date_display = sale.date.strftime("%Y-%m-%d")
#     # Current date and time with AM/PM format
#     # Example: "2025-12-05 04:52 PM"
#     date_display = datetime.now().strftime("%Y-%m-%d %I:%M %p")


#     # 4. Trigger the Print
#     success, msg = print_receipt_usb(
#         serial_number=serial_number,
#         cart_items=printer_items,
#         total_payable=payable_display,
#         date_str=date_display

#     )

#     if success:
#         messages.success(request, "تمت الطباعة بنجاح")
#     else:
#         messages.error(request, f"خطأ في الطباعة: {msg}")

#     # Redirect back to home or wherever you prefer
#     return redirect('home')




from django.utils import timezone
def financial_box(request):
    products = Product.objects.filter(is_active=True)
    box = FinancialBox.objects.all().first()
    current_box_value=box.current_amount
    today = timezone.localdate()
    total_sales_today = Sale.objects.filter(
        date=today
    ).aggregate(
        total=Sum('total_payable_price')
    )['total'] or 0

    dollar_rate = Settings.objects.filter(key='dollar_rate').first().value

    store_products_price = products.aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0

    store_products_price_syp=store_products_price*dollar_rate
    return render(
        request,
        'store/financial_box.html',
        {
            'current_box_value':current_box_value,
            'store_products_price':store_products_price,
            'store_products_price_syp':store_products_price_syp,
            'total_sales_today':total_sales_today,
        },
    )