
#-----rest_framework imports-----#
from rest_framework.views import APIView
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from core.models import Order, AdminSetting, UserProfile, Notification, Product, StampApplication, SupportTicket, Inquiry, StampOrder, AuditLog  # Import the Order, AdminSetting, UserProfile, Notification, Product, StampApplication, SupportTicket, Inquiry, StampOrder, and AuditLog models
import qrcode
from io import BytesIO
import base64
import hashlib
from django.core.files.base import ContentFile

#------serializers------#

from core.serializers import (
    UserSerializer, AdvocateSerializer, StampApplicationSerializer,
    OrderSerializer, SupportTicketSerializer, InquirySerializer,
    StampOrderSerializer, ProductSerializer, AuditLogSerializer,
    NotificationSerializer, AdminSettingSerializer, UserProfileSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]  # Or IsAdminUser if you want only admins to create

    def perform_create(self, serializer):
        serializer.save()  # No need to assign user here, product doesn't belong to user


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]



class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        If the user is an admin, return all orders.
        Otherwise, return only the orders for the current user.
        """
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class StampApplicationViewSet(viewsets.ModelViewSet):
    queryset = StampApplication.objects.all()
    serializer_class = StampApplicationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Admins can see all applications, others only their own.
        """
        if self.request.user.is_staff:
            return StampApplication.objects.all()
        return StampApplication.objects.filter(advocate__user=self.request.user)

    def perform_create(self, serializer):
        """
        Create a new stamp application.
        """
        advocate = self.request.user.advocate  # Get the advocate instance
        serializer.save(advocate=advocate, status='payment')  # Set advocate and initial status
        instance = serializer.instance

        # Generate QR code and hash
        qr_data = "\n".join([
            f"Wakili Stamp: {instance.id}",
            f"Advocate: {instance.advocate.tls_id}",
            f"Type: {instance.get_stamp_type_display()}",
            f"Office: {instance.collection_office}",
            f"Date: {instance.application_date.strftime('%Y-%m-%d')}"
        ])
        qr = qrcode.make(qr_data)
        qr_io = BytesIO()
        qr.save(qr_io, format='PNG')
        qr_image_base64 = base64.b64encode(qr_io.getvalue()).decode()
        qr_hash = hashlib.sha256(qr_data.encode()).hexdigest()

        # Save QR code image and hash to the model instance
        instance.qr_code.save(f"qr_code_{instance.id}.png", ContentFile(qr_io.getvalue()), save=False)
        instance.qr_hash = qr_hash
        instance.save()  # Save again after generating QR code and hash

    @action(detail=True, methods=['POST'], url_path='approve', permission_classes=[IsAdminUser])
    def approve_application(self, request, pk=None):
        """Approve a stamp application."""
        application = self.get_object()
        application.status = 'ready'  # Or whatever your "approved" status is
        application.save()
        return Response({'status': 'approved', 'application_id': application.id})

    @action(detail=True, methods=['POST'], url_path='decline', permission_classes=[IsAdminUser])
    def decline_application(self, request, pk=None):
        """Decline a stamp application."""
        application = self.get_object()
        reason = request.data.get('rejection_reason')  # Get reason from request
        if not reason:
            return Response({'error': 'Rejection reason is required.'}, status=status.HTTP_400_BAD_REQUEST)
        application.status = 'rejected'  # Or whatever your "rejected" status is
        application.rejection_reason = reason
        application.save()
        return Response({'status': 'declined', 'application_id': application.id})



class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Regular users only see their own tickets. Staff can see all.
        """
        if self.request.user.is_staff:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_staff=False) #set the user and is_staff



class InquiryViewSet(viewsets.ModelViewSet):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    authentication_classes = [TokenAuthentication] #optional
    permission_classes = [IsAuthenticated] #optional

    def perform_create(self, serializer):
        serializer.save()  # No user association for Inquiries, so no need to set user

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reply(self, request, pk=None):
        """Reply to an inquiry."""
        inquiry = self.get_object()
        reply_text = request.data.get('reply')
        if reply_text:
            inquiry.reply = reply_text
            inquiry.is_answered = True
            inquiry.save()
            return Response({'status': 'replied'})
        else:
            return Response({'error': 'Reply text is required.'}, status=status.HTTP_400_BAD_REQUEST)


class StampOrderViewSet(viewsets.ModelViewSet):
    queryset = StampOrder.objects.all()
    serializer_class = StampOrderSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Users see only their own stamp orders.  Admins see all.
        """
        if self.request.user.is_staff:
            return StampOrder.objects.all()
        return StampOrder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing audit logs.  Read-only, accessible to admins.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]  # Only admins can view logs
    # You might want to add filtering/ordering here



class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notifications.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Users can only see their own notifications.
        """
        return Notification.objects.filter(recipient=self.request.user)

    def perform_create(self, serializer):
        serializer.save(recipient=self.request.user)



class AdminSettingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing admin settings.  Only accessible to admins.
    """
    queryset = AdminSetting.objects.all()
    serializer_class = AdminSettingSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]



class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Override get_object to return the user's own profile
        """
        queryset = self.filter_queryset(self.get_queryset())
        # Make sure to catch any lookup errors
        try:
            obj = queryset.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            raise Http404  # Or return a 404 response
        return obj

    def perform_create(self, serializer):
        serializer.save(user=self.request.user) #associate the user

class AdminOrderViewSet(viewsets.ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=True, methods=['post'])
    def update_status(self, request, order_id=None):
        try:
            order = Order.objects.get(pk=order_id)
            new_status = request.data.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                serializer = OrderSerializer(order)  # Use the serializer
                return Response(serializer.data)
            else:
                return Response({'error': 'Invalid status provided.'}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
#====================================================================

#------------------- END OF API VIEWS ------------------- #

#====================================================================

