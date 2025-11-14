from django import forms
from .models import Product
from django.utils import timezone

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
            'name': forms.TextInput(attrs={'placeholder': 'اسم المنتج'}),
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
            raise forms.ValidationError('يجب إدخال اسم المنتج')
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
