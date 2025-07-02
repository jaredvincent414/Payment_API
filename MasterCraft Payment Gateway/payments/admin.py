from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_id', 'customer_name', 'customer_email', 
        'amount', 'currency', 'status', 'created_at'
    ]
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['payment_id', 'customer_name', 'customer_email', 'paypal_transaction_id']
    readonly_fields = [
        'id', 'payment_id', 'created_at', 'updated_at', 
        'completed_at', 'paypal_transaction_id'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'status', 'amount', 'currency')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'description')
        }),
        ('PayPal Information', {
            'fields': ('paypal_transaction_id', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual payment creation through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow editing of payment status and error messages"""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Disable payment deletion through admin"""
        return False
