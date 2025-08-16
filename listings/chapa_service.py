import requests
import json
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ChapaPaymentService:
    """Service class for handling Chapa payment integration"""
    
    def __init__(self):
        self.base_url = settings.CHAPA_BASE_URL
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initiate_payment(self, payment_data):
        """
        Initiate a payment with Chapa
        
        Args:
            payment_data (dict): Payment information including amount, email, etc.
            
        Returns:
            dict: Chapa API response
        """
        url = f"{self.base_url}transaction/initialize"
        
        try:
            response = requests.post(
                url, 
                headers=self.headers, 
                data=json.dumps(payment_data),
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa payment initiation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, transaction_id):
        """
        Verify a payment with Chapa
        
        Args:
            transaction_id (str): Transaction ID to verify
            
        Returns:
            dict: Verification response
        """
        url = f"{self.base_url}transaction/verify/{transaction_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_status(self, transaction_reference):
        """
        Get payment status from Chapa
        
        Args:
            transaction_reference (str): Chapa transaction reference
            
        Returns:
            str: Payment status (completed, failed, pending)
        """
        verification_result = self.verify_payment(transaction_reference)
        
        if verification_result['success']:
            chapa_status = verification_result['data'].get('status', '').lower()
            
            # Map Chapa status to our internal status
            status_mapping = {
                'success': 'completed',
                'failed': 'failed',
                'pending': 'pending',
                'cancelled': 'cancelled'
            }
            
            return status_mapping.get(chapa_status, 'pending')
        
        return 'failed'
