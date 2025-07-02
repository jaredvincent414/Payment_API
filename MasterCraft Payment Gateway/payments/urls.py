from django.urls import path
from . import views

urlpatterns = [
    # Payment endpoints
    path('', views.list_payments, name='list_payments'),
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    
    # Payment redirect endpoints (must come before dynamic patterns)
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Dynamic payment endpoints (must come after specific patterns)
    path('<str:payment_id>/', views.get_payment_status, name='get_payment_status'),
    path('<str:payment_id>/verify/', views.verify_payment, name='verify_payment'),
] 