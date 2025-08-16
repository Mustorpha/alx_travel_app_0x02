from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Payment, Booking
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_payment_confirmation_email(payment_id):
    """
    Send payment confirmation email to user
    
    Args:
        payment_id (int): Payment ID
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        user = booking.user
        
        subject = f'Payment Confirmation - Booking #{booking.id}'
        message = f"""
        Dear {user.first_name or user.username},
        
        Your payment has been successfully processed!
        
        Booking Details:
        - Booking Reference: {payment.booking_reference}
        - Listing: {booking.listing.name}
        - Check-in: {booking.start_date}
        - Check-out: {booking.end_date}
        - Amount Paid: {payment.amount} {payment.currency}
        - Transaction ID: {payment.transaction_id}
        
        Thank you for choosing our service!
        
        Best regards,
        ALX Travel App Team
        """
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Payment confirmation email sent for payment {payment_id}")
        
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")

@shared_task
def send_payment_failure_email(payment_id):
    """
    Send payment failure notification email to user
    
    Args:
        payment_id (int): Payment ID
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        user = booking.user
        
        subject = f'Payment Failed - Booking #{booking.id}'
        message = f"""
        Dear {user.first_name or user.username},
        
        Unfortunately, your payment could not be processed.
        
        Booking Details:
        - Booking Reference: {payment.booking_reference}
        - Listing: {booking.listing.name}
        - Amount: {payment.amount} {payment.currency}
        
        Please try again or contact our support team for assistance.
        
        Best regards,
        ALX Travel App Team
        """
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Payment failure email sent for payment {payment_id}")
        
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
    except Exception as e:
        logger.error(f"Failed to send payment failure email: {str(e)}")
