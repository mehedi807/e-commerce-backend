from django.db import models

class PaymentProvider(models.TextChoices):
    STRIPE = 'stripe', 'Stripe'
    BKASH = 'bkash', 'bKash'

class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SUCCESS = 'success', 'Success'
    FAILED = 'failed', 'Failed'

BKASH_TOKEN_CACHE_KEY = 'bkash_id_token'
BKASH_TOKEN_CACHE_TTL = 3300

