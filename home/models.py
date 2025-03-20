from django.db import models
import uuid



class Package(models.Model):
    name = models.CharField(max_length=255)  # Package name
    img = models.CharField(max_length=255)  # Image file name
    entries = models.IntegerField(blank=True, null=True)  # Number of entries
    description = models.TextField(blank=True, null=True)  # Description of the package
    crypto_amount = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)  # Price in BTC
    fiat_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Price in USD
    crypto_currency = models.CharField(max_length=50 ,blank=True, null=True)
    fiat_currency = models.CharField(max_length=50 ,blank=True, null=True)

    discount = models.CharField(max_length=50)  # Discount info
    message = models.TextField()  # Short message about the package

    def __str__(self):
        return f"{self.name} - {self.entries} entries"


class UserInfo(models.Model):
    first_name = models.CharField(max_length=100,blank=True, null=True)
    last_name = models.CharField(max_length=100,blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100,blank=True, null=True)
    street_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20,blank=True, null=True)
    phone = models.CharField(max_length=20,blank=True, null=True)
    email = models.EmailField(unique=True,blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"



class Order(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name="orders")
    package = models.ForeignKey(Package, on_delete=models.CASCADE)  # Link to package
    order_id = models.CharField(max_length=36, unique=True, editable=False, default=uuid.uuid4)
    
    # Automatically fetch details from the package
    entries = models.IntegerField()
    crypto_amount = models.DecimalField(max_digits=10, decimal_places=8)  # Price in BTC
    fiat_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Price in USD
    crypto_currency = models.CharField(max_length=50)
    fiat_currency = models.CharField(max_length=50)
    
    date_and_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.user.email}"



# Create your models here.
class CryptoPayment(models.Model):
    status = models.CharField(max_length=50, null=True, blank=True)  # e.g., "confirmed", "failed", etc.
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orders")
    
    currency = models.CharField(max_length=10)  # E.g., BTC, ETH, USDT
    network = models.CharField(max_length=50, null=True, blank=True)  # E.g., Ethereum, Binance Smart Chain
    
    # Crypto
    initiated_crypto_amount = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    paid_crypto_amount = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)

    # Fiat 
    price_amount = models.FloatField(null=True, blank=True)
    price_currency = models.CharField(max_length=10, null=True, blank=True)

    wallet_address = models.CharField(max_length=255, null=True, blank=True)
    payment_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    order_description = models.TextField(null=True, blank=True)

    ipn_callback_url = models.URLField(null=True, blank=True)
    invoice_url = models.URLField(null=True, blank=True)
    success_url = models.URLField(null=True, blank=True)
    cancel_url = models.URLField(null=True, blank=True)
    
    # New fields for wallet addresses
    payin_address = models.CharField(max_length=255, blank=True, null=True)  # User's wallet address (payer)
    payout_address = models.CharField(max_length=255, blank=True, null=True)  # Merchant's wallet address (receiver)
    payin_tx_hash = models.CharField(max_length=255, blank=True, null=True)   # Transaction hash of the payment
    payout_tx_hash = models.CharField(max_length=255, blank=True, null=True)  # Transaction hash of the payout

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.order_id} ({self.currency}) - {self.status}"








