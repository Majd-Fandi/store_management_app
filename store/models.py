from django.db import models
from django.utils import timezone

# ======================================================================
# ======================================================================
# ======================================================================

class Classification(models.Model):
    category=models.CharField(max_length=100)
    
    def __str__(self):
        return self.category
    
# ======================================================================
# ======================================================================
# ======================================================================

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Original cost
    quantity = models.PositiveIntegerField()  # Number of items available
    # newly added  
    classification=models.ForeignKey(Classification, on_delete=models.SET_NULL,null=True,blank=True) 
    retail_sale_percent = models.PositiveIntegerField(null=True, blank=True)
    whole_sale_percent = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    def syp_price(self):
        dollar_rate = Settings.objects.get(key="dollar_rate").value 
        return int(self.price * dollar_rate)

# ======================================================================
# ======================================================================
# ======================================================================

class Sale(models.Model):
    date = models.DateField(default=timezone.now)  # Date of the sale
    products = models.ManyToManyField(Product, through='SaleItem') 

    def __str__(self):
        return f"Sale on {self.date.strftime('%Y-%m-%d %H:%M:%S')}"

# ======================================================================
# ======================================================================
# ======================================================================

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)  # CASCADE is fine here because SaleItem is a child of Sale
    product = models.ForeignKey(Product, on_delete=models.PROTECT)  # Reference to the Product
    quantity = models.PositiveIntegerField()  # Quantity of the product sold
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of sale
    dollar_rate_at_sale=models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Set the price_at_sale to the current product price if it's not already set
        if self.dollar_rate_at_sale is None:
            self.dollar_rate_at_sale = Settings.objects.filter(key='dollar_rate').first().value
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} sold in {self.sale}"

# ======================================================================
# ======================================================================
# ======================================================================

class Settings(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.key}: {self.value}"
    class Meta:
        verbose_name = "Setting"         
        verbose_name_plural = "Settings" 

# ======================================================================
# ======================================================================
# ======================================================================


