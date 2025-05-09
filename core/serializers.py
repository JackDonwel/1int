from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Advocate, AdvocateProfile, StampApplication, Order,
    SupportTicket, Inquiry, StampOrder, Product, AuditLog,
    Notification, AdminSetting, UserProfile
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class AdvocateSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Advocate
        fields = '__all__'

class AdvocateProfileSerializer(serializers.ModelSerializer):
   class Meta:
       model = AdvocateProfile
       fields = '__all__'

class StampApplicationSerializer(serializers.ModelSerializer):
    advocate = AdvocateSerializer()  # Use AdvocateSerializer for nested representation
    class Meta:
        model = StampApplication
        fields = '__all__'
        read_only_fields = ['id', 'application_date', 'status', 'qr_hash'] #important

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created']

class SupportTicketSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = '__all__'
        read_only_fields = ['id', 'submitted_at']

class StampOrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = StampOrder
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created']

class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(allow_null=True)
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']

class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer()
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'sent_at']

class AdminSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminSetting
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
   user = UserSerializer()
   class Meta:
       model = UserProfile
       fields = '__all__'
