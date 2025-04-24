from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    SupportTicket, StampOrder, Inquiry, Order, AdvocateProfile, 
    Advocate, StampApplication, AuditLog, Notification, 
    AdminSetting, Product, UserProfile
)
from .serializers import (
    SupportTicketSerializer, StampOrderSerializer, InquirySerializer, 
    OrderSerializer, AdvocateProfileSerializer, AdvocateSerializer, 
    StampApplicationSerializer, AuditLogSerializer, NotificationSerializer, 
    AdminSettingSerializer, ProductSerializer, UserProfileSerializer,
    UserSerializer
)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=user)

class StampOrderViewSet(viewsets.ModelViewSet):
    serializer_class = StampOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'stamp_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return StampOrder.objects.all()
        return StampOrder.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        stamp_order = self.get_object()
        if 'status' not in request.data:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not request.user.is_staff:
            return Response({'error': 'Only staff can update status'}, status=status.HTTP_403_FORBIDDEN)
            
        stamp_order.status = request.data['status']
        stamp_order.save()
        serializer = self.get_serializer(stamp_order)
        return Response(serializer.data)

class InquiryViewSet(viewsets.ModelViewSet):
    queryset = Inquiry.objects.all().order_by('-submitted_at')
    serializer_class = InquirySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'email', 'subject']
    ordering_fields = ['submitted_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'color_type', 'payment_method']
    ordering_fields = ['created']
    ordering = ['-created']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        if 'status' not in request.data:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not request.user.is_staff:
            return Response({'error': 'Only staff can update status'}, status=status.HTTP_403_FORBIDDEN)
            
        order.status = request.data['status']
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

class AdvocateProfileViewSet(viewsets.ModelViewSet):
    serializer_class = AdvocateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AdvocateProfile.objects.all()
        return AdvocateProfile.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        profile = get_object_or_404(AdvocateProfile, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

class AdvocateViewSet(viewsets.ModelViewSet):
    serializer_class = AdvocateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_verified', 'chapter']
    search_fields = ['tls_id', 'user__username', 'user__email']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Advocate.objects.all()
        return Advocate.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_advocate_profile(self, request):
        advocate = get_object_or_404(Advocate, user=request.user)
        serializer = self.get_serializer(advocate)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        advocate = self.get_object()
        if not request.user.is_staff:
            return Response({'error': 'Only staff can verify advocates'}, status=status.HTTP_403_FORBIDDEN)
            
        advocate.is_verified = True
        advocate.save()
        serializer = self.get_serializer(advocate)
        return Response(serializer.data)

class StampApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = StampApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'stamp_type', 'payment_verified']
    ordering_fields = ['application_date', 'last_updated']
    ordering = ['-application_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return StampApplication.objects.all()
        try:
            advocate = Advocate.objects.get(user=user)
            return StampApplication.objects.filter(advocate=advocate)
        except Advocate.DoesNotExist:
            return StampApplication.objects.none()
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        application = self.get_object()
        if 'status' not in request.data:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not request.user.is_staff:
            return Response({'error': 'Only staff can update status'}, status=status.HTTP_403_FORBIDDEN)
            
        application.status = request.data['status']
        if application.status == 'rejected' and 'rejection_reason' in request.data:
            application.rejection_reason = request.data['rejection_reason']
            
        application.save()
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        application = self.get_object()
        if not request.user.is_staff:
            return Response({'error': 'Only staff can verify payments'}, status=status.HTTP_403_FORBIDDEN)
            
        application.payment_verified = True
        application.status = 'production'
        application.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='payment_verify',
            details=f'Payment verified for application #{application.id}',
            affected_application=application,
            ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0')
        )
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        application = self.get_object()
        if not request.user.is_staff:
            return Response({'error': 'Only staff can generate QR codes'}, status=status.HTTP_403_FORBIDDEN)
            
        application.generate_qr_hash()
        serializer = self.get_serializer(application)
        return Response(serializer.data)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = AuditLog.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'user']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_sent', 'read']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(recipient=user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        queryset.update(read=True)
        return Response({'status': 'All notifications marked as read'})

class AdminSettingViewSet(viewsets.ModelViewSet):
    queryset = AdminSetting.objects.all()
    serializer_class = AdminSettingSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['key', 'description']
    
    @action(detail=False, methods=['get'])
    def get_setting(self, request):
        if 'key' not in request.query_params:
            return Response({'error': 'Key parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        key = request.query_params['key']
        default = request.query_params.get('default', None)
        
        value = AdminSetting.get_setting(key, default)
        return Response({'key': key, 'value': value})

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['created', 'price_tzs']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'tls_id', 'region', 'district']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)