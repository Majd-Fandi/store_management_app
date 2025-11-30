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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField() 
    classification=models.ForeignKey(Classification, on_delete=models.SET_NULL,null=True,blank=True) 
    retail_sale_percent = models.PositiveIntegerField(null=True, blank=True)
    whole_sale_percent = models.PositiveIntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def syp_price(self):
        dollar_rate = Settings.objects.get(key="dollar_rate").value 
        return int(self.price * dollar_rate)
    
    def safe_delete(self):
        if SaleItem.objects.filter(product=self).exists():
            self.is_active = False
            self.save()
            return f"{self.name} marked as discontinued"
        else:
            self.delete()
            return f"{self.name} completely deleted"
        
# ======================================================================
# ======================================================================
# ======================================================================

class Sale(models.Model):
    date = models.DateField(default=timezone.now)
    products = models.ManyToManyField(Product, through='SaleItem') 

    def __str__(self):
        return f"Sale on {self.date.strftime('%Y-%m-%d %H:%M:%S')}"

# ======================================================================
# ======================================================================
# ======================================================================

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)  # CASCADE is fine here because SaleItem is a child of Sale
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()  # Quantity of the product sold
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of sale
    dollar_rate_at_sale=models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
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

from django.db.models import Case, When, DecimalField, Sum, F

class Trader(models.Model):
    """
    Represents a dealer or supplier.
    The current_balance is cached here for quick lookup.
    A positive balance means the store (you) owes the trader (liability).
    A negative balance means the trader owes the store (asset).
    """
    name = models.CharField(max_length=150, verbose_name="اسم الشركة \ التاجر")
    contact_info = models.TextField(blank=True, verbose_name="معلومات التواصل")
    current_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Current Financial Balance"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


    def update_balance(self):
        """
        Recalculates the total balance based on all related transactions.
        """
        balance_qs = self.transactions.aggregate(
            total=Sum(
                Case(
                    When(transaction_type=Transaction.TransactionType.PURCHASE, then=F('amount')),
                    When(transaction_type=Transaction.TransactionType.PAYMENT, then=-F('amount')),
                    default=0,
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        )
        new_balance = balance_qs['total'] or 0.00
        self.current_balance = new_balance
        self.save(update_fields=['current_balance'])

    # def update_balance(self):
    #     """
    #     Recalculates the total balance based on all related transactions.
    #     This is a fallback/verification method. The Transaction save method handles
    #     real-time updates.
    #     """
    #     # Calculate the sum of amounts, where Purchase adds to the balance (we owe them)
    #     # and Payment subtracts from the balance (we pay them, reducing our debt).
    #     balance_qs = self.transactions.aggregate(
    #         total=Sum(
    #             F('amount'), 
    #             filter=models.Q(transaction_type=Transaction.TransactionType.PURCHASE)
    #         ) - Sum(
    #             F('amount'),
    #             filter=models.Q(transaction_type=Transaction.TransactionType.PAYMENT)
    #         )
    #     )
    #     new_balance = balance_qs['total'] if balance_qs['total'] is not None else 0.00
    #     self.current_balance = new_balance
    #     self.save(update_fields=['current_balance'])


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        # PURCHASE = 'P', 'Purchase'  # Store buys from trader (increases debt/liability)
        # PAYMENT = 'T', 'Payment'    # Store pays trader (decreases debt/liability)
        PURCHASE = 'P', 'استلام'  # Store buys from trader (increases debt/liability)
        PAYMENT = 'T', 'دفع'    # Store pays trader (decreases debt/liability)

    trader = models.ForeignKey(
        Trader, 
        on_delete=models.CASCADE, 
        related_name='transactions', 
        verbose_name="Trader"
    )
    transaction_type = models.CharField(
        max_length=1, 
        choices=TransactionType.choices, 
        verbose_name="Type"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount")
    notes = models.TextField(blank=True, verbose_name="Notes")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        ordering = ['-date']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount} with {self.trader.name}"

    def save(self, *args, **kwargs):
        """
        Overrides save method to update the trader's balance.
        If it's an existing transaction being updated, we need to handle the old amount.
        We assume this is a new transaction for simplicity, but a full app would need
        to handle updates/deletions via signals/overrides. For a new record:
        """
        super().save(*args, **kwargs)  # Save the transaction first

        # Simple logic for NEW transaction: update the associated Trader's balance
        self.trader.update_balance()

    # Note: For production use, you would also need to implement delete() and update 
    # logic to reverse the balance changes correctly.
