from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid
import logging

from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
from .chapa_service import ChapaPaymentService
from .tasks import send_payment_confirmation_email, send_payment_failure_email

logger = logging.getLogger(__name__)

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Create booking and prepare for payment"""
        booking = serializer.save(user=self.request.user)
        
        # Calculate total price
        nights = (booking.end_date - booking.start_date).days
        total_price = booking.listing.price_per_night * nights
        booking.total_price = total_price
        booking.save()

    @action(detail=True, methods=['post'])
    def initiate_payment(self, request, pk=None):
        """
        Initiate payment for a booking
        """
        booking = self.get_object()
        
        # Check if payment already exists
        if hasattr(booking, 'payment'):
            return Response(
                {'error': 'Payment already exists for this booking'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            currency='ETB'
        )
        
        # Prepare Chapa payment data
        payment_data = {
            'amount': str(booking.total_price),
            'currency': 'ETB',
            'email': request.user.email,
            'first_name': request.user.first_name or request.user.username,
            'last_name': request.user.last_name or '',
            'phone_number': request.data.get('phone_number', ''),
            'tx_ref': str(payment.booking_reference),
            'callback_url': request.data.get('callback_url', ''),
            'return_url': request.data.get('return_url', ''),
            'description': f'Payment for booking {booking.listing.name}',
            'meta': {
                'booking_id': booking.id,
                'user_id': request.user.id
            }
        }
        
        # Initialize payment with Chapa
        chapa_service = ChapaPaymentService()
        result = chapa_service.initiate_payment(payment_data)
        
        if result['success']:
            chapa_data = result['data']
            payment.chapa_transaction_reference = chapa_data.get('data', {}).get('tx_ref')
            payment.save()
            
            return Response({
                'payment_id': payment.id,
                'checkout_url': chapa_data.get('data', {}).get('checkout_url'),
                'tx_ref': chapa_data.get('data', {}).get('tx_ref'),
                'message': 'Payment initiated successfully'
            }, status=status.HTTP_200_OK)
        else:
            payment.status = 'failed'
            payment.save()
            return Response(
                {'error': f'Payment initiation failed: {result["error"]}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter payments by user"""
        return Payment.objects.filter(booking__user=self.request.user)

    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        """
        Verify payment status with Chapa
        """
        payment = self.get_object()
        
        if not payment.chapa_transaction_reference:
            return Response(
                {'error': 'No Chapa transaction reference found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        chapa_service = ChapaPaymentService()
        result = chapa_service.verify_payment(payment.chapa_transaction_reference)
        
        if result['success']:
            chapa_data = result['data']
            payment_status = chapa_data.get('status', '').lower()
            
            # Update payment status
            old_status = payment.status
            if payment_status == 'success':
                payment.status = 'completed'
                payment.transaction_id = chapa_data.get('reference')
                payment.payment_method = chapa_data.get('method')
            elif payment_status == 'failed':
                payment.status = 'failed'
            elif payment_status == 'cancelled':
                payment.status = 'cancelled'
            
            payment.save()
            
            # Send email notifications if status changed
            if old_status != payment.status:
                if payment.status == 'completed':
                    send_payment_confirmation_email.delay(payment.id)
                elif payment.status == 'failed':
                    send_payment_failure_email.delay(payment.id)
            
            return Response({
                'payment_status': payment.status,
                'transaction_id': payment.transaction_id,
                'verification_data': chapa_data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': f'Payment verification failed: {result["error"]}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def webhook(self, request):
        """
        Handle Chapa webhook notifications
        """
        try:
            webhook_data = request.data
            tx_ref = webhook_data.get('tx_ref')
            
            if not tx_ref:
                return Response(
                    {'error': 'Transaction reference not provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find payment by transaction reference
            try:
                payment = Payment.objects.get(booking_reference=tx_ref)
            except Payment.DoesNotExist:
                logger.error(f"Payment with tx_ref {tx_ref} not found")
                return Response(
                    {'error': 'Payment not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update payment status based on webhook data
            webhook_status = webhook_data.get('status', '').lower()
            old_status = payment.status
            
            if webhook_status == 'success':
                payment.status = 'completed'
                payment.transaction_id = webhook_data.get('reference')
                payment.payment_method = webhook_data.get('method')
            elif webhook_status == 'failed':
                payment.status = 'failed'
            elif webhook_status == 'cancelled':
                payment.status = 'cancelled'
            
            payment.save()
            
            # Send email notifications if status changed
            if old_status != payment.status:
                if payment.status == 'completed':
                    send_payment_confirmation_email.delay(payment.id)
                elif payment.status == 'failed':
                    send_payment_failure_email.delay(payment.id)
            
            logger.info(f"Webhook processed for payment {payment.id}, status: {payment.status}")
            
            return Response({'message': 'Webhook processed successfully'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return Response(
                {'error': 'Webhook processing failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

