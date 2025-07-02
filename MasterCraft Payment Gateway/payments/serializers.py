from rest_framework import serializers
from .models import Payment


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new payment"""
    
    class Meta:
        model = Payment
        fields = ['customer_name', 'customer_email', 'amount', 'currency', 'description']
        extra_kwargs = {
            'currency': {'required': False, 'default': 'USD'},
            'description': {'required': False},
        }
    
    def validate_amount(self, value):
        """Validate that amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate_customer_email(self, value):
        """Validate email format"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.lower()


class PaymentResponseSerializer(serializers.ModelSerializer):
    """Serializer for payment response"""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'customer_name', 'customer_email', 
            'amount', 'currency', 'status', 'description',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = fields


class PaymentStatusSerializer(serializers.ModelSerializer):
    """Serializer for payment status response"""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'customer_name', 'customer_email', 
            'amount', 'currency', 'status', 'paypal_transaction_id',
            'created_at', 'completed_at', 'error_message'
        ]
        read_only_fields = fields


class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing payments"""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'customer_name', 'customer_email', 
            'amount', 'currency', 'status', 'created_at'
        ]
        read_only_fields = fields 