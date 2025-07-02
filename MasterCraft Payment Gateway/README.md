# MasterCraft Payment Gateway API

A simple, production-ready payment gateway API built with Django and integrated with PayPal. This API allows you to initiate payments, check payment status, and manage transactions without requiring user authentication.
## Features

- **Real PayPal Integration**: Direct integration with PayPal payment gateway (sandbox and live)
- **RESTful API**: Clean, versioned API endpoints following REST principles
- **No Authentication Required**: Simple integration without user authentication
- **Comprehensive Testing**: Automated tests for all API endpoints
- **Admin Interface**: Django admin for payment management
- **Error Handling**: Robust error handling and validation
- **Production Ready**: Ready for deployment with proper error handling
- **User-Friendly Testing**: Web interface and Postman collection for easy testing

## API Endpoints

### Version 1 (`/api/v1/`)

#### 1. Initiate Payment
- **Endpoint**: `POST /api/v1/payments/initiate/`
- **Description**: Creates a new payment transaction using PayPal
- **Request Body**:
```json
{
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "amount": 50.00,
    "currency": "USD",
    "description": "Payment for services"
}
```
- **Response**:
```json
{
    "status": "success",
    "message": "Payment initiated successfully",
    "payment": {
        "id": "uuid",
        "payment_id": "PAY-12345678",
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "amount": "50.00",
        "currency": "USD",
        "status": "processing",
        "created_at": "2024-01-01T12:00:00Z"
    },
    "paypal_info": {
        "transaction_id": "PAYID-12345678",
        "approval_url": "https://www.sandbox.paypal.com/checkout/..."
    }
}
```

#### 2. Get Payment Status
- **Endpoint**: `GET /api/v1/payments/{payment_id}/`
- **Description**: Retrieves the status of a specific payment
- **Response**:
```json
{
    "status": "success",
    "message": "Payment details retrieved successfully",
    "payment": {
        "id": "uuid",
        "payment_id": "PAY-12345678",
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "amount": "50.00",
        "currency": "USD",
        "status": "completed",
        "paypal_transaction_id": "PAYID-12345678",
        "created_at": "2024-01-01T12:00:00Z",
        "completed_at": "2024-01-01T12:05:00Z"
    }
}
```

#### 3. List Payments
- **Endpoint**: `GET /api/v1/payments/`
- **Description**: Lists all payments (for admin/monitoring)
- **Response**:
```json
{
    "status": "success",
    "message": "Payments retrieved successfully",
    "payments": [...],
    "count": 10
}
```

#### 4. Verify Payment
- **Endpoint**: `POST /api/v1/payments/{payment_id}/verify/`
- **Description**: Manually verify a payment status
- **Response**: Same as Get Payment Status

#### 5. Payment Success Redirect
- **Endpoint**: `GET /api/v1/payments/success/`
- **Description**: Handles successful payment redirects from PayPal

#### 6. Payment Cancel Redirect
- **Endpoint**: `GET /api/v1/payments/cancel/`
- **Description**: Handles cancelled payment redirects from PayPal

## Setup Instructions

### Prerequisites
- Python 3.9+
- pip
- Git
- PayPal Developer Account

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd MasterCraft-Payment-Gateway
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure PayPal settings**
Edit `payment_gateway/settings.py` and update the PayPal configuration:
```python
PAYPAL_CLIENT_ID = 'your-paypal-client-id'
PAYPAL_CLIENT_SECRET = 'your-paypal-client-secret'
PAYPAL_MODE = 'sandbox'  # sandbox or live
```

5. **Run database migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser (optional)**
```bash
python manage.py createsuperuser
```

7. **Run the development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`

## PayPal Setup

1. Create a PayPal Developer account at https://developer.paypal.com/
2. Create a new Business app in the PayPal Developer Dashboard
3. Get your Client ID and Client Secret from the Sandbox section
4. Set `PAYPAL_MODE=sandbox` for testing, `live` for production
5. Update the settings in `payment_gateway/settings.py`

## Testing

### Run Automated Tests
```bash
python manage.py test
```

### Test the API

#### Option 1: Web Interface (Recommended)
Access the user-friendly test interface at: http://localhost:8000/
- Fill out the payment form
- Click "Initiate Payment"
- View real-time responses
- No coding required

#### Option 2: Postman Collection
1. Download and install [Postman](https://www.postman.com/downloads/)
2. Import the collection: `MasterCraft_Payment_Gateway.postman_collection.json`
3. Test all API endpoints with pre-configured requests

#### Option 3: Django Admin
1. Create a superuser: `python manage.py createsuperuser`
2. Access admin at: http://localhost:8000/admin/
3. View and manage all payment transactions

#### Option 4: cURL Commands
Use the examples below in your terminal

## API Usage Examples

### Using cURL

#### Initiate a Payment
```bash
curl -X POST http://localhost:8000/api/v1/payments/initiate/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "amount": 50.00,
    "currency": "USD",
    "description": "Payment for services"
  }'
```

#### Get Payment Status
```bash
curl -X GET http://localhost:8000/api/v1/payments/PAY-12345678/
```

### Using JavaScript/Fetch

#### Initiate a Payment
```javascript
const response = await fetch('http://localhost:8000/api/v1/payments/initiate/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    customer_name: 'John Doe',
    customer_email: 'john@example.com',
    amount: 50.00,
    currency: 'USD',
    description: 'Payment for services'
  })
});

const data = await response.json();
console.log(data);

// Use the approval_url to redirect user to PayPal
if (data.paypal_info && data.paypal_info.approval_url) {
  window.location.href = data.paypal_info.approval_url;
}
```

#### Get Payment Status
```javascript
const response = await fetch('http://localhost:8000/api/v1/payments/PAY-12345678/');
const data = await response.json();
console.log(data);
```

## Payment Flow

1. **Initiate Payment**: Call the initiate endpoint with customer details
2. **Redirect to PayPal**: Use the returned `approval_url` to redirect customer to PayPal
3. **Customer Completes Payment**: Customer logs in and completes payment on PayPal
4. **Payment Verification**: PayPal redirects back to your success/cancel URLs
5. **Check Status**: Use the API to check payment status and update your system

## CI/CD Pipeline

The project includes a GitHub Actions workflow that:
- Runs tests on Python 3.9
- Installs dependencies
- Validates the application

## Production Deployment

To deploy to production:

1. **Update PayPal settings**:
   ```python
   PAYPAL_MODE = 'live'
   PAYPAL_CLIENT_ID = 'your-live-client-id'
   PAYPAL_CLIENT_SECRET = 'your-live-client-secret'
   ```

2. **Update Django settings**:
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   SECRET_KEY = 'your-production-secret-key'
   ```

3. **Deploy to your preferred platform** (Heroku, AWS, DigitalOcean, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team

## Changelog

### Version 1.0.0
- Initial release
- Real PayPal payment gateway integration
- RESTful API with versioning
- Comprehensive testing suite
- Basic CI/CD pipeline
- Web interface for testing
- Postman collection for API testing
- Django admin for payment management
- Production-ready deployment configuration 