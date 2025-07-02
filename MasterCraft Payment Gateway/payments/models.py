from django.db import models
import uuid
from decimal import Decimal


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Payment identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_id = models.CharField(max_length=100, unique=True, help_text="External payment gateway ID")
    
    # Customer information
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # PayPal information
    paypal_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.customer_name} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Generate payment_id if not provided
        if not self.payment_id:
            self.payment_id = f"PAY-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
