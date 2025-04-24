from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    SupportTicket, StampOrder, Inquiry, Order, AdvocateProfile, 
    Advocate, StampApplication, AuditLog, Notification, 
    AdminSetting, Product, UserProfile
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class SupportTicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = '__all__'
        
    def create(self, validated_data):
        # Get the user from the context
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class StampOrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StampOrder
        fields = '__all__'
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class InquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class AdvocateProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AdvocateProfile
        fields = '__all__'

class AdvocateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Advocate
        fields = '__all__'
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class StampApplicationSerializer(serializers.ModelSerializer):
    advocate = AdvocateSerializer(read_only=True)
    
    class Meta:
        model = StampApplication
        fields = '__all__'
        
    def create(self, validated_data):
        # Get the advocate from the context
        user = self.context['request'].user
        advocate = Advocate.objects.get(user=user)
        validated_data['advocate'] = advocate
        return super().create(validated_data)

class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'

class AdminSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminSetting
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add the typed value to the representation
        representation['typed_value'] = instance.get_typed_value()
        return representation

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)