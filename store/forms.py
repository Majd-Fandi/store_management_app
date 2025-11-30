from django import forms
from .models import Product ,Classification
from django.utils import timezone

# --- هذا هو النموذج الجديد لصفحة الإضافة المجمعة ---
class ProductBulkAddForm(forms.ModelForm):
    
    # تحويل حقل التصنيف إلى قائمة منسدلة
    classification = forms.ModelChoiceField(
        queryset=Classification.objects.all(), 
        required=False, 
        label="التصنيف"
    )

    class Meta:
        model = Product
        # لاحظ: لا يوجد 'additional_quantity'
        fields = [
            'name', 'price', 'quantity', 'description', 
            'classification', 'retail_sale_percent', 'whole_sale_percent'
        ]
        labels = {
            'name': 'المادة',
            'price': 'السعر (التكلفة)',
            'quantity': 'الكمية',
            'description': 'الوصف',
            'retail_sale_percent': 'نسبة ربح التجزئة %',
            'whole_sale_percent': 'نسبة ربح الجملة %',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'المادة'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'quantity': forms.NumberInput(attrs={'min': '0'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'اختياري'}), 
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # وضع القيم الافتراضية للنسب
        self.fields['retail_sale_percent'].initial = 5
        self.fields['whole_sale_percent'].initial = 3
        
        # جعل الحقول الاختيارية غير مطلوبة
        self.fields['description'].required = False
        self.fields['classification'].required = False
        self.fields['retail_sale_percent'].required = False
        self.fields['whole_sale_percent'].required = False

    def clean_name(self):
        # من الجيد دائماً تنظيف الاسم
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('يجب إدخال المادة')
        return name.strip() # .strip() لإزالة المسافات الزائدة
    
class ProductForm(forms.ModelForm):
    description = forms.CharField(
        required=False,  # Make description optional
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'اختياري'}),
        label='الوصف'
    )
    additional_quantity = forms.IntegerField(
        required=False,  # Make additional quantity optional
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'أدخل الكمية الإضافية', 'min': '0'}),
        label='الكمية الإضافية'
    )

    whole_sale_percent = forms.IntegerField(
        required=False, 
        min_value=1,
        widget=forms.NumberInput(attrs={'min': '1'}),
        label='نسبة الربح % (جملة)'
    )
    retail_sale_percent = forms.IntegerField(
        required=False, 
        min_value=1,
        widget=forms.NumberInput(attrs={'min': '1'}),
        label='نسبة الربح % (مفرق)'
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'quantity', 'additional_quantity', 'classification','whole_sale_percent','retail_sale_percent']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'المادة'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'quantity': forms.NumberInput(attrs={'min': '0'}),
            'classification': forms.Select(attrs={'placeholder': 'اختر التصنيف'}),  # Add widget for classification
        }
        labels = {
            'classification': 'التصنيف',  # Add a label for the classification field
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if not name:
            raise forms.ValidationError('يجب إدخال المادة')
        return name

    def clean_price(self):
        price = self.cleaned_data['price']
        if price is not None and price < 0:
            raise forms.ValidationError('السعر لا يمكن أن يكون سالباً')
        return price

    def save(self, commit=True):
        instance = super().save(commit=False)
        additional_quantity = self.cleaned_data.get('additional_quantity', 0)
        if additional_quantity:
            instance.quantity += additional_quantity  # Add additional quantity to the existing quantity
        if commit:
            instance.save()
        return instance
    



class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        label="Start Date",
        widget=forms.DateInput(attrs={'type': 'date'}),  # Use 'date' input type
        initial=timezone.now().date()  # Set initial value to today's date
    )
    end_date = forms.DateField(
        label="End Date",
        widget=forms.DateInput(attrs={'type': 'date'}),  # Use 'date' input type
        initial=timezone.now().date()  # Set initial value to today's date
    )










from django import forms
from .models import Trader, Transaction

class TraderForm(forms.ModelForm):
    """Form for adding or editing a Trader."""
    class Meta:
        model = Trader
        fields = ['name', 'contact_info']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'أدخل اسم الشركة أو اسم التاجر'}),
            'contact_info': forms.Textarea(attrs={'class': 'input-field', 'rows': 3, 'placeholder': 'رقم تواصل , عنوان , بريد إلكتروني ...'}),
        }

class TransactionForm(forms.ModelForm):
    """Form for adding a new Transaction."""
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'notes']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'input-field'}),
            'amount': forms.NumberInput(attrs={'class': 'input-field', 'min': 0.01, 'step': 0.01, 'placeholder': ''}),
            'notes': forms.Textarea(attrs={'class': 'input-field', 'rows': 2, 'placeholder': 'إختياري'}),
        }
        labels = {
            'transaction_type': 'نوع المعاملة (استلام / دفع)',
            'amount': 'المبلغ (SYP)',
            'notes': 'ملاحظات',
        }