import requests
import json
import base64
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Payment


class PayPalService:
    """PayPal payment gateway service"""
    
    def __init__(self):
        self.base_url = settings.PAYPAL_BASE_URL
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.access_token = None
    
    def _get_access_token(self):
        """Get PayPal access token"""
        if self.access_token:
            return self.access_token
        
        auth_url = f"{self.base_url}/v1/oauth2/token"
        auth_data = {
            'grant_type': 'client_credentials'
        }
        
        # Proper Basic Authentication encoding
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        auth_headers = {
            'Authorization': f"Basic {encoded_credentials}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(auth_url, data=auth_data, headers=auth_headers)
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            return self.access_token
        else:
            raise Exception(f"Failed to get PayPal access token: {response.text}")
    
    def create_payment(self, payment_data):
        """Create a PayPal payment"""
        try:
            access_token = self._get_access_token()
            
            payment_url = f"{self.base_url}/v1/payments/payment"
            payment_payload = {
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(payment_data['amount']),
                        "currency": payment_data.get('currency', 'USD')
                    },
                    "description": payment_data.get('description', 'Payment for services')
                }],
                "redirect_urls": {
                    "return_url": f"http://localhost:8000/api/v1/payments/success",
                    "cancel_url": f"http://localhost:8000/api/v1/payments/cancel"
                }
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(payment_url, json=payment_payload, headers=headers)
            
            if response.status_code == 201:
                payment_response = response.json()
                return {
                    'success': True,
                    'transaction_id': payment_response['id'],
                    'approval_url': next(link['href'] for link in payment_response['links'] if link['rel'] == 'approval_url'),
                    'gateway_response': payment_response
                }
            else:
                return {
                    'success': False,
                    'error': f"PayPal payment creation failed: {response.text}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"PayPal service error: {str(e)}"
            }
    
    def verify_payment(self, transaction_id):
        """Verify a PayPal payment"""
        try:
            access_token = self._get_access_token()
            
            payment_url = f"{self.base_url}/v1/payments/payment/{transaction_id}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(payment_url, headers=headers)
            
            if response.status_code == 200:
                payment_data = response.json()
                state = payment_data.get('state', 'unknown')
                
                return {
                    'success': True,
                    'status': 'completed' if state == 'approved' else 'failed',
                    'gateway_response': payment_data
                }
            else:
                return {
                    'success': False,
                    'error': f"PayPal payment verification failed: {response.text}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"PayPal verification error: {str(e)}"
            }


class PaymentService:
    """Main payment service that coordinates with PayPal"""
    
    @classmethod
    def create_payment(cls, payment_data):
        """Create a payment using PayPal"""
        try:
            # Create payment record
            payment = Payment.objects.create(
                customer_name=payment_data['customer_name'],
                customer_email=payment_data['customer_email'],
                amount=payment_data['amount'],
                currency=payment_data.get('currency', 'USD'),
                description=payment_data.get('description', ''),
                status='pending'
            )
            
            # Get PayPal service
            paypal_service = PayPalService()
            
            # Create payment in PayPal
            payment_data['payment_id'] = payment.payment_id
            paypal_result = paypal_service.create_payment(payment_data)
            
            if paypal_result['success']:
                # Update payment with PayPal transaction ID
                payment.paypal_transaction_id = paypal_result['transaction_id']
                payment.status = 'processing'
                payment.save()
                
                return {
                    'success': True,
                    'payment': payment,
                    'gateway_response': paypal_result
                }
            else:
                # Update payment with error
                payment.status = 'failed'
                payment.error_message = paypal_result['error']
                payment.save()
                
                return {
                    'success': False,
                    'payment': payment,
                    'error': paypal_result['error']
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Payment creation error: {str(e)}"
            }
    
    @classmethod
    def verify_payment(cls, payment_id):
        """Verify a payment status"""
        try:
            payment = Payment.objects.get(payment_id=payment_id)
            paypal_service = PayPalService()
            
            if not payment.paypal_transaction_id:
                return {
                    'success': False,
                    'error': 'No PayPal transaction ID found'
                }
            
            verification_result = paypal_service.verify_payment(payment.paypal_transaction_id)
            
            if verification_result['success']:
                # Update payment status
                payment.status = verification_result['status']
                if verification_result['status'] == 'completed':
                    payment.completed_at = timezone.now()
                payment.save()
                
                return {
                    'success': True,
                    'payment': payment,
                    'gateway_response': verification_result
                }
            else:
                return {
                    'success': False,
                    'payment': payment,
                    'error': verification_result['error']
                }
        
        except Payment.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Payment verification error: {str(e)}"
            } 