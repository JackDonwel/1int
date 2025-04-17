# -*- coding: utf-8 -*-
import os
import io
import base64
import qrcode
import logging
from io import BytesIO
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from django.db import models
from .forms import StampApplicationForm, SupportTicketForm
from .models import Advocate, StampApplication, AuditLog, Notification, AuditLog, Order, SupportTicket
from .utils import apply_stamp_to_pdf
from django.contrib import messages



logger = logging.getLogger(__name__)

@login_required
def apply_stamp(request):
    qr_image_base64 = None
    if request.method == 'POST':
        form = StampApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the stamp application
            application = form.save(commit=False)
            application.advocate = request.user.advocate_profile
            application.save()

            # Create ink order if checkbox is checked
            if request.POST.get('include_ink'):
                Order.objects.create(
                    user=request.user,
                    color_type='blue1',
                    quantity=1,  # Default quantity
                    payment_method='mpesa',  # Default payment method
                    delivery_address=form.cleaned_data['collection_office'],
                    status='processing'
                )

            # Generate QR code data
            qr_data = "\n".join([
                f"Wakili Stamp: {application.id}",
                f"Advocate: {application.advocate.tls_id}",
                f"Type: {application.get_stamp_type_display()}",
                f"Office: {application.collection_office}",
                f"Date: {application.application_date.strftime('%Y-%m-%d')}"
            ])

            # Generate QR code
            qr = qrcode.make(qr_data)
            qr_io = BytesIO()
            qr.save(qr_io, format='PNG')
            qr_io.seek(0)

            # Convert to base64 and add to context
            qr_base64 = base64.b64encode(qr_io.read()).decode('utf-8')
            qr_image_base64 = f'data:image/png;base64,{qr_base64}'

            # Send notifications
            messages.success(request, "Application submitted successfully!")
            return render(request, 'qr_result.html', {
                'qr_image': qr_image_base64,
                'application': application
            })
    else:
        form = StampApplicationForm()

    return render(request, 'apply_stamp.html', {
        'form': form,
        'qr_image': qr_image_base64
    })

@login_required
def submit_support_ticket(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            SupportTicket.objects.create(
                user=request.user,
                message=message
            )
    return redirect('/')

@login_required
def application_status(request, application_id=None):
    """View application status with QR code verification"""
    if request.method == 'POST':
        application_id = request.POST.get('application_id')
    
    application = get_object_or_404(
        StampApplication,
        id=application_id,
        advocate__user=request.user  # Ensure user owns the application
    )
    
    context = {
        'application': application,
        'qr_code_url': application.qr_code.url if application.qr_code else None,
        'verification_url': f"{settings.DOMAIN}/verify-stamp/{application.qr_hash}/"
    }
    
    return render(request, 'application_status.html', context)

                
def error(request):
    return render(request, 'error.html')

def verify_stamp(request, qr_hash):
    """Public verification endpoint for QR codes"""
    application = get_object_or_404(StampApplication, qr_hash=qr_hash)
    
    context = {
        'valid': application.status in ['ready', 'collected'],
        'application': application,
        'advocate': application.advocate,
        'verification_date': timezone.now()
    }
    
    return render(request, 'verify_stamp.html', context)


@login_required
def home(request):
    """Dashboard view with recent applications and orders"""
    # Get recent stamp applications
    applications = StampApplication.objects.filter(
        advocate__user=request.user
    ).order_by('-application_date')[:5]
    
    # Get recent ink orders
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created')[:10]
    
    # Get recent support tickets
    support_tickets = SupportTicket.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:5]
    
    context = {
        'applications': applications,
        'orders': orders,
        'support_tickets': support_tickets
    }
    
    return render(request, 'index.html', context)



def login(request):
    """Enhanced login with logging"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            auth_login(request, user)
            AuditLog.objects.create(
                user=user,
                action='login',
                details='Successful login',
                ip_address=get_client_ip(request)
            )
            return redirect('/')
            
        AuditLog.objects.create(
            user=None,
            action='failed_login',
            details=f"Failed login attempt for username: {username}",
            ip_address=get_client_ip(request)
        )
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')

def order_ink(request):
    if request.method == 'POST':
        # Process form data
        # Create order object
        order = Order.objects.create(
            # Add appropriate fields and values for the Order model
        )
        return render(request, 'order_confirmation.html', {'order': order})
    return render(request, 'order_ink.html')

def order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'order_status.html', {'order': order})

def is_admin(user):
    return user.is_authenticated and user.is_staff


#--- Custom admin-like views
@login_required

@staff_member_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')
        try:
            order = Order.objects.get(id=order_id)
            order.status = status
            order.save()
            messages.success(request, "Order status updated successfully!")
        except ObjectDoesNotExist:
            messages.error(request, "Order not found.")
    return render(request, 'admin/admin_orders.html', {'orders': orders})

@login_required
@staff_member_required
def admin_queue(request):
    applications = StampApplication.objects.all().order_by('-application_date')
    return render(request, 'admin/admin_queue.html', {'applications': applications})


@staff_member_required
def view_inquiries(request):
    tickets = SupportTicket.objects.all().order_by('-timestamp')
    return render(request, 'admin/view_inquiries.html', {'tickets': tickets})




@staff_member_required
def reply_inquiry(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    if request.method == 'POST':
        reply = request.POST.get('reply', '').strip()
        if reply:
            ticket.reply = reply
            ticket.is_answered = True
            ticket.save()
            messages.success(request, 'Reply sent successfully.')

    return render(request, 'admin/reply_inquiry.html', {'ticket': ticket})


#  -------- end of custom admin-like views --------

@login_required
def my_inquiries(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'my_inquiries.html', {'tickets': tickets})


@login_required
def user_chat(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by('timestamp')

    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.is_staff = False
            ticket.save()
            return redirect('user_chat')
    else:
        form = SupportTicketForm()

    return render(request, 'support/user_chat.html', {'form': form, 'tickets': tickets})


@user_passes_test(lambda u: u.is_staff)
def staff_chat(request, user_id):
    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)
    tickets = SupportTicket.objects.filter(user=user).order_by('timestamp')

    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = user
            ticket.is_staff = True
            ticket.save()
            return redirect('staff_chat', user_id=user_id)
    else:
        form = SupportTicketForm()

    return render(request, 'support/staff_chat.html', {'form': form, 'tickets': tickets, 'chat_user': user})




@login_required
@require_http_methods(["POST"])
def custom_logout(request):
    """Handle secure logout with POST requests only"""
    logout(request)
    return redirect('home')

def logout_confirmation(request):
    """Display logout confirmation page"""
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'logout_confirm.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists'})

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Create advocate profile with default values
        Advocate.objects.create(
            user=user,
            tls_id=f"TEMP-{user.id}",  # You can modify this format
            chapter="Pending Assignment",
            phone_number="+255000000000"  # Default number
        )
        
        auth_login(request, user)
        return redirect('/')

    return render(request, 'signup.html')

def get_client_ip(request):
    """Utility function for getting client IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')