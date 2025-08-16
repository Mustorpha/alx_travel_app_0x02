# ALX Travel App 0x02 - Chapa Payment Integration

A Django REST API application for travel bookings with integrated Chapa payment processing.

## Features

- **Travel Listings Management**: Create, read, update, and delete travel listings
- **Booking System**: Users can book listings with date validation
- **Chapa Payment Integration**: Secure payment processing using Chapa API
- **Payment Verification**: Automatic payment status verification
- **Email Notifications**: Automated email confirmations for successful/failed payments
- **Background Tasks**: Celery integration for handling email notifications
- **API Documentation**: Swagger UI for API documentation

## Payment Integration Features

### Chapa API Integration
- Payment initiation through Chapa API
- Real-time payment verification
- Webhook support for payment status updates
- Secure transaction handling
- Support for multiple payment methods

### Payment Workflow
1. User creates a booking
2. Payment is initiated through Chapa API
3. User completes payment via Chapa checkout
4. Payment status is verified automatically
5. Email confirmation is sent upon successful payment
6. Payment failures are handled gracefully with user notifications

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL/MariaDB
- Redis (for Celery)
- Chapa Developer Account

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd alx_travel_app_0x02
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r alx_travel_app/requirement.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your configurations:
   - Database credentials
   - Chapa API secret key (from https://developer.chapa.co/)
   - Email settings
   - Redis configuration

5. **Database Migration**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

8. **Start Celery Worker** (in a separate terminal)
   ```bash
   celery -A alx_travel_app worker --loglevel=info
   ```

## API Endpoints

### Bookings
- `GET /api/bookings/` - List all bookings
- `POST /api/bookings/` - Create a new booking
- `GET /api/bookings/{id}/` - Get booking details
- `POST /api/bookings/{id}/initiate_payment/` - Initiate payment for booking

### Payments
- `GET /api/payments/` - List user payments
- `GET /api/payments/{id}/` - Get payment details
- `POST /api/payments/{id}/verify_payment/` - Verify payment status
- `POST /api/payments/webhook/` - Chapa webhook endpoint

### Listings
- `GET /api/listings/` - List all listings
- `POST /api/listings/` - Create a new listing
- `GET /api/listings/{id}/` - Get listing details

## Payment Integration Usage

### 1. Create a Booking
```json
POST /api/bookings/
{
    "listing": 1,
    "start_date": "2024-08-20",
    "end_date": "2024-08-25"
}
```

### 2. Initiate Payment
```json
POST /api/bookings/{booking_id}/initiate_payment/
{
    "phone_number": "+251912345678",
    "callback_url": "https://yourapp.com/payment/callback",
    "return_url": "https://yourapp.com/payment/success"
}
```

### 3. Payment Response
```json
{
    "payment_id": 1,
    "checkout_url": "https://checkout.chapa.co/checkout/payment/...",
    "tx_ref": "unique-transaction-reference",
    "message": "Payment initiated successfully"
}
```

### 4. Verify Payment
```json
POST /api/payments/{payment_id}/verify_payment/
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CHAPA_SECRET_KEY` | Chapa API secret key | `CHASECK_TEST-xxx` |
| `DB_NAME` | Database name | `alx_travel_app` |
| `DB_USER` | Database username | `root` |
| `DB_PASSWORD` | Database password | `password` |
| `EMAIL_HOST_USER` | Email sender | `noreply@yourapp.com` |
| `CELERY_BROKER_URL` | Redis URL for Celery | `redis://localhost:6379` |

## Testing

### Chapa Sandbox Testing
1. Use Chapa's sandbox environment for testing
2. Test payment initiation and verification
3. Verify webhook functionality
4. Test email notifications

### Test Payment Flow
```bash
# Create test data
python manage.py shell
from listings.models import Listing, User
from django.contrib.auth.models import User

# Create test user
user = User.objects.create_user('testuser', 'test@example.com', 'password')

# Create test listing
listing = Listing.objects.create(
    name='Test Hotel',
    description='A test hotel',
    price_per_night=100.00
)
```

## Error Handling

- Payment failures are logged and users are notified via email
- Failed payments can be retried
- Webhook failures are logged for debugging
- Network errors are handled gracefully with retries

## Security Features

- API authentication required for payment operations
- Secure storage of Chapa credentials in environment variables
- Transaction reference validation
- Webhook signature verification (recommended for production)

## Production Deployment

1. Set `DEBUG=False` in environment
2. Configure proper email backend (SMTP)
3. Use production Chapa credentials
4. Set up proper logging
5. Configure Redis for production
6. Set up webhook URL in Chapa dashboard

## Support

For issues and support:
- Check Chapa documentation: https://developer.chapa.co/
- Review Django REST Framework docs
- Check Celery documentation for background tasks

## License

MIT License