from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock
from .models import Payment
from .serializers import PaymentCreateSerializer


class PaymentModelTest(TestCase):
    """Test cases for Payment model"""
    
    def setUp(self):
        self.payment_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'amount': Decimal('50.00'),
            'currency': 'USD',
            'description': 'Test payment'
        }
    
    def test_payment_creation(self):
        """Test creating a payment record"""
        payment = Payment.objects.create(**self.payment_data)
        self.assertEqual(payment.customer_name, 'John Doe')
        self.assertEqual(payment.customer_email, 'john@example.com')
        self.assertEqual(payment.amount, Decimal('50.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertTrue(payment.payment_id.startswith('PAY-'))
    
    def test_payment_string_representation(self):
        """Test payment string representation"""
        payment = Payment.objects.create(**self.payment_data)
        expected = f"Payment {payment.payment_id} - John Doe - 50.00 USD"
        self.assertEqual(str(payment), expected)
    
    def test_payment_properties(self):
        """Test payment status properties"""
        payment = Payment.objects.create(**self.payment_data)
        
        # Test pending status
        self.assertTrue(payment.is_pending)
        self.assertFalse(payment.is_completed)
        self.assertFalse(payment.is_failed)
        
        # Test completed status
        payment.status = 'completed'
        payment.save()
        self.assertTrue(payment.is_completed)
        self.assertFalse(payment.is_pending)
        self.assertFalse(payment.is_failed)
        
        # Test failed status
        payment.status = 'failed'
        payment.save()
        self.assertTrue(payment.is_failed)
        self.assertFalse(payment.is_completed)
        self.assertFalse(payment.is_pending)


class PaymentSerializerTest(TestCase):
    """Test cases for Payment serializers"""
    
    def test_payment_create_serializer_valid_data(self):
        """Test PaymentCreateSerializer with valid data"""
        data = {
            'customer_name': 'Jane Smith',
            'customer_email': 'jane@example.com',
            'amount': '75.50',
            'currency': 'EUR',
            'description': 'Test payment description'
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['customer_name'], 'Jane Smith')
        self.assertEqual(serializer.validated_data['customer_email'], 'jane@example.com')
        self.assertEqual(serializer.validated_data['amount'], Decimal('75.50'))
    
    def test_payment_create_serializer_invalid_amount(self):
        """Test PaymentCreateSerializer with invalid amount"""
        data = {
            'customer_name': 'Jane Smith',
            'customer_email': 'jane@example.com',
            'amount': '-10.00',
            'currency': 'USD'
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_payment_create_serializer_invalid_email(self):
        """Test PaymentCreateSerializer with invalid email"""
        data = {
            'customer_name': 'Jane Smith',
            'customer_email': 'invalid-email',
            'amount': '50.00',
            'currency': 'USD'
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('customer_email', serializer.errors)
    
    def test_payment_create_serializer_missing_required_fields(self):
        """Test PaymentCreateSerializer with missing required fields"""
        data = {
            'customer_name': 'Jane Smith',
            'amount': '50.00'
        }
        serializer = PaymentCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('customer_email', serializer.errors)


class PaymentAPITest(APITestCase):
    """Test cases for Payment API endpoints"""
    
    def setUp(self):
        self.payment_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'amount': '50.00',
            'currency': 'USD',
            'description': 'Test payment'
        }
        self.payment = Payment.objects.create(
            customer_name='Jane Smith',
            customer_email='jane@example.com',
            amount=Decimal('75.50'),
            currency='EUR',
            status='completed'
        )
    
    @patch('payments.services.PaymentService.create_payment')
    def test_initiate_payment_success(self, mock_create_payment):
        """Test successful payment initiation"""
        # Mock successful payment creation
        mock_create_payment.return_value = {
            'success': True,
            'payment': self.payment,
            'gateway_response': {
                'transaction_id': 'TXN123',
                'approval_url': 'https://paypal.com/approve'
            }
        }
        url = reverse('initiate_payment')
        response = self.client.post(url, self.payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('payment', response.data)
        self.assertIn('paypal_info', response.data)
    
    @patch('payments.services.PaymentService.create_payment')
    def test_initiate_payment_failure(self, mock_create_payment):
        """Test failed payment initiation"""
        # Mock failed payment creation
        mock_create_payment.return_value = {
            'success': False,
            'error': 'PayPal error'
        }
        url = reverse('initiate_payment')
        response = self.client.post(url, self.payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('error', response.data)
    
    def test_initiate_payment_invalid_data(self):
        """Test payment initiation with invalid data"""
        invalid_data = {
            'customer_name': 'John Doe',
            'customer_email': 'invalid-email',
            'amount': '-10.00'
        }
        url = reverse('initiate_payment')
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('errors', response.data)
    
    def test_get_payment_status_success(self):
        """Test successful payment status retrieval"""
        url = reverse('get_payment_status', kwargs={'payment_id': self.payment.payment_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('payment', response.data)
        self.assertEqual(response.data['payment']['payment_id'], self.payment.payment_id)
    
    def test_get_payment_status_not_found(self):
        """Test payment status retrieval for non-existent payment"""
        url = reverse('get_payment_status', kwargs={'payment_id': 'NONEXISTENT'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 'error')
    
    def test_list_payments(self):
        """Test listing all payments"""
        url = reverse('list_payments')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('payments', response.data)
        self.assertEqual(response.data['count'], 1)
    
    @patch('payments.services.PaymentService.verify_payment')
    def test_verify_payment_success(self, mock_verify_payment):
        """Test successful payment verification"""
        # Mock successful verification
        mock_verify_payment.return_value = {
            'success': True,
            'payment': self.payment
        }
        url = reverse('verify_payment', kwargs={'payment_id': self.payment.payment_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('payment', response.data)
    
    @patch('payments.services.PaymentService.verify_payment')
    def test_verify_payment_failure(self, mock_verify_payment):
        """Test failed payment verification"""
        # Mock failed verification
        mock_verify_payment.return_value = {
            'success': False,
            'error': 'Verification failed'
        }
        url = reverse('verify_payment', kwargs={'payment_id': self.payment.payment_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('error', response.data)
    
    @patch('payments.services.PaymentService.verify_payment')
    def test_payment_success_redirect(self, mock_verify_payment):
        """Test payment success redirect handling"""
        # Mock successful verification
        mock_verify_payment.return_value = {
            'success': True,
            'payment': self.payment
        }
        url = '/api/v1/payments/success/'
        print('DEBUG payment_success URL:', url)
        response = self.client.get(url, {'paymentId': self.payment.payment_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
    
    def test_payment_cancel_redirect(self):
        """Test payment cancel redirect handling"""
        url = '/api/v1/payments/cancel/'
        print('DEBUG payment_cancel URL:', url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')


class PaymentServiceTest(TestCase):
    """Test cases for PaymentService"""
    
    def setUp(self):
        self.payment_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'amount': Decimal('50.00'),
            'currency': 'USD',
            'description': 'Test payment'
        }
    
    @patch('payments.services.PayPalService')
    def test_create_payment_success(self, mock_paypal_service):
        """Test successful payment creation"""
        from payments.services import PaymentService
        
        # Mock PayPal service
        mock_service_instance = MagicMock()
        mock_paypal_service.return_value = mock_service_instance
        mock_service_instance.create_payment.return_value = {
            'success': True,
            'transaction_id': 'TXN123',
            'approval_url': 'https://paypal.com/approve'
        }
        
        result = PaymentService.create_payment(self.payment_data)
        
        self.assertTrue(result['success'])
        self.assertIn('payment', result)
        self.assertIn('gateway_response', result)
    
    @patch('payments.services.PayPalService')
    def test_create_payment_failure(self, mock_paypal_service):
        """Test failed payment creation"""
        from payments.services import PaymentService
        
        # Mock PayPal service
        mock_service_instance = MagicMock()
        mock_paypal_service.return_value = mock_service_instance
        mock_service_instance.create_payment.return_value = {
            'success': False,
            'error': 'PayPal error'
        }
        
        result = PaymentService.create_payment(self.payment_data)
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_verify_payment_not_found(self):
        """Test payment verification for non-existent payment"""
        from payments.services import PaymentService
        
        result = PaymentService.verify_payment('NONEXISTENT')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Payment not found')
