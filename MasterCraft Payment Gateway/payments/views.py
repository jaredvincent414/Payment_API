from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Payment
from .serializers import (
    PaymentCreateSerializer, 
    PaymentResponseSerializer, 
    PaymentStatusSerializer,
    PaymentListSerializer
)
from .services import PaymentService


@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_payment(request):
    """
    Initiate a payment transaction using PayPal
    
    POST /api/v1/payments/initiate/
    """
    try:
        # Validate request data
        serializer = PaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create payment using PayPal service
        payment_data = serializer.validated_data
        result = PaymentService.create_payment(payment_data)
        
        if result['success']:
            payment = result['payment']
            response_serializer = PaymentResponseSerializer(payment)
            
            return Response({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'payment': response_serializer.data,
                'paypal_info': {
                    'transaction_id': result['gateway_response']['transaction_id'],
                    'approval_url': result['gateway_response']['approval_url']
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 'error',
                'message': 'Failed to initiate payment',
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_payment_status(request, payment_id):
    """
    Retrieve payment status by payment ID
    
    GET /api/v1/payments/{payment_id}/
    """
    try:
        # Get payment by ID
        payment = get_object_or_404(Payment, payment_id=payment_id)
        
        # Verify payment with PayPal if status is pending or processing
        if payment.status in ['pending', 'processing']:
            verification_result = PaymentService.verify_payment(payment_id)
            if verification_result['success']:
                payment = verification_result['payment']
        
        # Serialize response
        serializer = PaymentStatusSerializer(payment)
        
        return Response({
            'status': 'success',
            'message': 'Payment details retrieved successfully',
            'payment': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        # If the exception is Http404, return 404, else 500
        from django.http import Http404
        if isinstance(e, Http404):
            return Response({
                'status': 'error',
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_payments(request):
    """
    List all payments (for admin/monitoring purposes)
    
    GET /api/v1/payments/
    """
    try:
        payments = Payment.objects.all()
        serializer = PaymentListSerializer(payments, many=True)
        
        return Response({
            'status': 'success',
            'message': 'Payments retrieved successfully',
            'payments': serializer.data,
            'count': len(serializer.data)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_payment(request, payment_id):
    """
    Manually verify a payment status
    
    POST /api/v1/payments/{payment_id}/verify/
    """
    try:
        result = PaymentService.verify_payment(payment_id)
        
        if result['success']:
            payment = result['payment']
            serializer = PaymentStatusSerializer(payment)
            
            return Response({
                'status': 'success',
                'message': 'Payment verified successfully',
                'payment': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': 'Payment verification failed',
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'Internal server error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_success(request):
    """
    Handle successful payment redirect from PayPal
    
    GET /api/v1/payments/success/
    """
    payment_id = request.GET.get('paymentId')
    
    if payment_id:
        try:
            result = PaymentService.verify_payment(payment_id)
            if result['success']:
                payment = result['payment']
                return Response({
                    'status': 'success',
                    'message': 'Payment completed successfully',
                    'payment_id': payment.payment_id,
                    'amount': str(payment.amount),
                    'currency': payment.currency
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Payment verification failed',
                    'error': result.get('error', 'Unknown error')
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'status': 'error',
        'message': 'Payment verification failed'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_cancel(request):
    """
    Handle cancelled payment redirect from PayPal
    
    GET /api/v1/payments/cancel/
    """
    return Response({
        'status': 'cancelled',
        'message': 'Payment was cancelled by the user'
    }, status=status.HTTP_200_OK)
