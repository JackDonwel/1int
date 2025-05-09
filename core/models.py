import uuid
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

#---------------------------USER PROFILE---------------------------#

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    message = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='support_images/', blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return f"{'Staff' if self.is_staff else self.user.username} - {self.get_status_display()} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class StampOrder(models.Model):
    STAMP_TYPES = [
        ('official', 'Official'),
        ('personal', 'Personal'),
        ('corporate', 'Corporate'),
    ]

    stamp_type = models.CharField(max_length=20, choices=STAMP_TYPES)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stamp_type} order by {self.user.username}"


class Inquiry(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.subject}"

class Order(models.Model):
    """Ink order details for a user."""
    COLOR_CHOICES = [('blue1', 'Blue Type 1')]
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('processing', 'Processing'),
        ('delivered', 'Delivered'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
 

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    color_type = models.CharField(max_length=10, choices=COLOR_CHOICES)
    quantity = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    delivery_address = models.TextField()
    created = models.DateTimeField(auto_now_add=True)  # 👈 this is the real field
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='processing')

    class Meta:
        ordering = ['-created']
        verbose_name = "Ink Order"
        verbose_name_plural = "Ink Orders"

    def __str__(self):
        return f"Order #{self.id} - {self.get_color_type_display()}"


class AdvocateProfile(models.Model):
    """Profile for each advocate user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advocate_profile'
    )
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_advocate_profile(sender, instance, created, **kwargs):
    if created:
        AdvocateProfile.objects.create(user=instance)


class Advocate(models.Model):
    """Detailed advocate record for official registration."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advocate'
    )
    tls_id = models.CharField(max_length=50, unique=True)
    chapter = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    is_verified = models.BooleanField(default=False)
    date_registered = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Advocate"
        verbose_name_plural = "Advocates"
        ordering = ['-date_registered']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.tls_id})"


class StampApplication(models.Model):
    """Application model for stamp services."""
    STAMP_TYPES = [
        ('certification', 'Certification'),
        ('notarization', 'Notarization'),
    ]
    APPLICATION_STATUS = [
        ('pending', 'Pending'),
        ('payment', 'Awaiting Payment'),
        ('production', 'In Production'),
        ('ready', 'Ready for Collection'),
        ('rejected', 'Rejected'),
        ('collected', 'Collected'),
    ]

    advocate = models.ForeignKey(
        'Advocate',
        on_delete=models.CASCADE,
        related_name='stamp_applications'
    )
    
    
    stamp_type = models.CharField(
        max_length=50,
        choices=STAMP_TYPES,
        default='certification',
        validators=[
            RegexValidator(
                regex='^(certification|notarization)$',
                message='Invalid stamp type'
            )
        ]
    )
    size = models.CharField(max_length=50)
    collection_office = models.CharField(max_length=100)
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=APPLICATION_STATUS, default='pending')
    payment_verified = models.BooleanField(default=False)
    control_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)
    qr_metadata = models.JSONField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stamp Application"
        verbose_name_plural = "Stamp Applications"
        ordering = ['-application_date']
        indexes = [models.Index(fields=['status', 'application_date'])]

    def __str__(self):
        return f"{self.advocate.tls_id} - {self.get_stamp_type_display()}"

    def generate_qr_hash(self):
        """Generate a unique SHA-256 hash for the QR code."""
        raw = f"{self.id}-{self.advocate.id}-{timezone.now().timestamp()}"
        self.qr_hash = hashlib.sha256(raw.encode()).hexdigest()
        self.save()





class AuditLog(models.Model):
    """Track important user or admin actions."""
    ACTION_TYPES = [
        ('login', 'User Login'),
        ('application', 'Application Submitted'),
        ('status_change', 'Status Changed'),
        ('payment_verify', 'Payment Verified'),
        ('admin_action', 'Admin Action'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(default='0.0.0.0')
    affected_application = models.ForeignKey(
        StampApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"{self.timestamp} - {self.get_action_display()}"


class Notification(models.Model):
    """User notification logs and message details."""
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    related_application = models.ForeignKey(
        StampApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.notification_type} to {self.recipient}: {self.subject}"



# # Admin settings for the application
import json
#---------------------------ADMIN SETTINGS---------------------------#

class AdminSetting(models.Model):
    SETTING_TYPES = (
        ('background_image', 'Background Image'),
        ('logo', 'Logo'),
        ('primary_color', 'Primary Color'),
        ('secondary_color', 'Secondary Color'),
        ('custom_css', 'Custom CSS'),
        ('custom_js', 'Custom JavaScript'),
    )
    setting_name = models.CharField(max_length=100)
    setting_value = models.TextField(blank=True, null=True)
    setting_type = models.CharField(max_length=50, choices=SETTING_TYPES, unique=True)
    value = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.get_setting_type_display()
    #------------------ Product Model ------------------#

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('law_book', 'Law Book'),
        ('journal', 'Law Journal'),
        ('stationery', 'Legal Stationery'),
        ('service', 'Legal Service'),
        ('tool', 'Legal Tool'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_tzs = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True) 
    
    
    def __str__(self):
        return self.name
    
    #------------------ User Profile Model ------------------#
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ward = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    law_firm = models.CharField(max_length=100, blank=True)
    chapters = models.CharField(max_length=100, blank=True)
    advocate_chapter = models.CharField(max_length=100, blank=True)
    advocate_title = models.CharField(max_length=100, blank=True)
    practicing_law = models.BooleanField(default=False)
    practicing_status = models.CharField(max_length=100, blank=True)
    id_type = models.CharField(max_length=100, blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    id_expiry_date = models.DateField(blank=True, null=True)
    id_image = models.ImageField(upload_to='id_images/', blank=True, null=True)
    tls_id = models.CharField(max_length=100, blank=True)
    
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
