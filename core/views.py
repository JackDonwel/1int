# -*- coding: utf-8 -*-
import base64
import logging
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import requests
from .models import AuditLog

from django.db.models import Count, Q, Sum, Avg, F
from datetime import timedelta
from django.db.models.functions import TruncDay
import qrcode
from .utils import get_client_ip
import hashlib

from .models import (
    Advocate, StampApplication, AuditLog, Notification, Order, SupportTicket, Inquiry, StampOrder, Product, AuditLog
)
from .forms import StampApplicationForm, SupportTicketForm, StampOrderForm
from .utils import apply_stamp_to_pdf




logger = logging.getLogger(__name__)







#------------------- PAYMENT VIEWS ------------------- #

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def initiate_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        email = request.POST.get('email')
        full_name = request.POST.get('name')

        headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            "tx_ref": f"stamp-{email}-{request.user.id}",
            "amount": amount,
            "currency": "TZS",
            "redirect_url": request.build_absolute_uri('/payment/complete/'),
            "payment_options": "card,mpesa,banktransfer",
            "customer": {
                "email": email,
                "name": full_name
            },
            "customizations": {
                "title": "Wakili Stamp Payment",
                "description": "Online Stamp Payment",
                "logo": "https://yourdomain.com/static/logo.png"
            }
        }

        response = requests.post('https://api.flutterwave.com/v3/payments', headers=headers, json=data)
        res_data = response.json()

        if res_data.get('status') == 'success':
            return redirect(res_data['data']['link'])
        else:
            return render(request, 'error.html', {"error": res_data.get("message")})
    return render(request, 'payment/payment_form.html')


@csrf_exempt

@login_required
def payment_complete(request):
    status = request.GET.get('status')  # check from Flutterwave query string
    app_id = request.session.pop('app_id', None)

    if status == 'successful' and app_id:
        application = get_object_or_404(StampApplication, id=app_id)
        application.status = 'production'
        application.payment_verified = True
        application.save()

        # Generate QR
        qr_data = "\n".join([
            f"Wakili Stamp: {application.id}",
            f"Advocate: {application.advocate.tls_id}",
            f"Type: {application.get_stamp_type_display()}",
            f"Office: {application.collection_office}",
            f"Date: {application.application_date.strftime('%Y-%m-%d')}"
        ])
        qr = qrcode.make(qr_data)
        qr_io = BytesIO()
        qr.save(qr_io, format='PNG')
        qr_image_base64 = f"data:image/png;base64,{base64.b64encode(qr_io.getvalue()).decode()}"

        return render(request, 'qr_result.html', {
            'qr_image': qr_image_base64,
            'application': application
        })

    messages.error(request, "Payment failed or canceled.")
    return redirect('apply_stamp')


# ------------------- USER VIEWS ------------------- #
@login_required
def home(request):
    products = Product.objects.all()
    profile, created = UserProfile.objects.get_or_create(user=request.user) if request.user.is_authenticated else (None, False)
    form = ProfileForm(instance=profile) if request.user.is_authenticated else None

    return render(request, 'index.html', {
        'products': products,
        'form': form
    })

@login_required
def apply_stamp(request):
    qr_image_base64 = None

    if request.method == 'POST':
        form = StampApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            
            # Get the Advocate instance related to the current user
            advocate = request.user.advocate_profile.advocate
            
            # Assign the Advocate instance to the application
            application.advocate = advocate
            application.status = 'payment'
            application.save()

            # Save app ID in session for use after payment
            request.session['app_id'] = application.id

            # Redirect to Flutterwave
            return redirect('initiate_payment')
    else:
        form = StampApplicationForm()

    return render(request, 'apply_stamp.html', {'form': form, 'qr_image': qr_image_base64})


@login_required
def application_status(request, application_id=None):
    """User can view the status of their application with a QR code"""
    if request.method == 'POST':
        application_id = request.POST.get('application_id')

    application = get_object_or_404(
        StampApplication,
        id=application_id,
        advocate__user=request.user
    )

    context = {
        'application': application,
        'qr_code_url': application.qr_code.url if application.qr_code else None,
        'verification_url': f"{settings.DOMAIN}/verify-stamp/{application.qr_hash}/"
    }
    return render(request, 'application_status.html', context)


@login_required
def order_ink(request):
    """Render order ink page (details can be expanded later)"""
    if request.method == 'POST':
        # Example only — should be expanded based on business rules
        order = Order.objects.create(user=request.user)
        return render(request, 'order_confirmation.html', {'order': order})
    return render(request, 'order_ink.html')


@login_required
def order_status(request, order_id):
    """Check status of an order"""
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'order_status.html', {'order': order})


@login_required
def user_chat(request):
    """User submits support tickets and views responses"""
    tickets = SupportTicket.objects.filter(user=request.user).order_by('timestamp')
    form = SupportTicketForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.user = request.user
        ticket.is_staff = False
        ticket.save()
        return redirect('user_chat')
    return render(request, 'support/user_chat.html', {'form': form, 'tickets': tickets})

@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """Logout view with audit logging"""
    if request.method == 'POST':
        logout(request)
        return redirect('home')
    return render(request, 'logout.html')



@login_required
@require_http_methods(["POST"])
def custom_logout(request):
    logout(request)
    return redirect('home')

@require_http_methods(["GET"])
@login_required
def immediate_logout(request):
    logout(request)
    return redirect('login')


def verify_stamp(request, qr_hash):
    """Public endpoint to verify QR code"""
    application = get_object_or_404(StampApplication, qr_hash=qr_hash)
    return render(request, 'verify_stamp.html', {
        'valid': application.status in ['ready', 'collected'],
        'application': application,
        'advocate': application.advocate,
        'verification_date': timezone.now()
    })



def custom_login_view(request):
    """Login with audit logging and admin redirection"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        ip = get_client_ip(request)

        if user:
            auth_login(request, user)
            AuditLog.objects.create(user=user, action='login', details='Successful login', ip_address=ip)

            if user.is_staff or user.is_superuser:
                return redirect('custom_dashboard')  # make sure this is a valid named URL
            return redirect('/')  # non-admin users

        else:
            AuditLog.objects.create(
                user=None,
                action='failed_login',
                details=f"Username: {username}",
                ip_address=ip
            )
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})

    return render(request, 'registration/login.html')

def signup(request):
    if request.method == 'POST':
        username, email, password = request.POST.get('username'), request.POST.get('email'), request.POST.get('password')
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists'})

        user = User.objects.create_user(username=username, email=email, password=password)
        Advocate.objects.create(user=user, tls_id=f"TEMP-{user.id}", chapter="Pending Assignment", phone_number="+255000000000")
        auth_login(request, user)
        return redirect('/')
    return render(request, 'registration/signup.html')


def error(request):
    return render(request, 'error.html')






def submit_support_ticket(request):
    if request.method == 'POST':
        # Process the form here
        return redirect('core:user_chat')  
    return redirect('core:error')


# ------------------- ADMIN/STAFF VIEWS ------------------- #

@staff_member_required
def admin_orders(request):
    """Admin can update order statuses"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=request.POST.get('order_id'))
            order.status = request.POST.get('status')
            order.save()
            messages.success(request, "Order status updated.")
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
    orders = Order.objects.all().order_by('-created')
    return render(request, 'admin/admin_orders.html', {'orders': orders})


@staff_member_required
def admin_queue(request):
    """Admin sees all stamp applications"""
    applications = StampApplication.objects.all().order_by('-application_date')
    return render(request, 'admin/admin_queue.html', {'applications': applications})


@staff_member_required
def view_tickets(request):
    """Admin views all support tickets"""
    tickets = SupportTicket.objects.all().order_by('-timestamp')
    return render(request, 'admin/inquiries.html', {'tickets': tickets})


@staff_member_required
def reply_ticket(request, ticket_id):
    """Admin replies to a user ticket"""
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    if request.method == 'POST':
        reply = request.POST.get('reply', '').strip()
        if reply:
            ticket.reply = reply
            ticket.is_answered = True
            ticket.save()
            messages.success(request, 'Reply sent.')
    return render(request, 'admin/reply_inquiry.html', {'ticket': ticket})


@staff_member_required
def staff_chat(request, user_id):
    """Chat-based support system for admin and users"""
    user = get_object_or_404(User, id=user_id)
    tickets = SupportTicket.objects.filter(user=user).order_by('timestamp')
    form = SupportTicketForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.user = user
        ticket.is_staff = True
        ticket.save()
        return redirect('staff_chat', user_id=user_id)
    return render(request, 'support/staff_chat.html', {'form': form, 'tickets': tickets, 'chat_user': user})


# ------------------- UTILITIES ------------------- #

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

from django.shortcuts import render

@login_required
def create_stamp_order(request):
    if request.method == 'POST':
        form = StampOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            return redirect('order_list')
    else:
        form = StampOrderForm()
    return render(request, 'create_order.html', {'form': form})

@login_required
def order_list(request):
    orders = StampOrder.objects.filter(user=request.user)
    return render(request, 'order_list.html', {'orders': orders})

def stamp_chart_data(request):
    data = (
        StampOrder.objects.values('stamp_type')
        .annotate(total=Count('id'))
        .order_by('stamp_type')
    )
    chart_data = {
        "labels": [d["stamp_type"] for d in data],
        "values": [d["total"] for d in data],
    }
    return JsonResponse(chart_data)

def view_inquiries(request):
    inquiries = Inquiry.objects.all()
    return render(request, 'admin/inquiries.html', {'inquiries': inquiries})



def view_inquiries(request):
    inquiries = Inquiry.objects.all()
    return render(request, 'admin/inquiries.html', {'inquiries': inquiries})

def reply_inquiry(request, ticket_id):
    ticket = get_object_or_404(Inquiry, id=ticket_id)
    if request.method == 'POST':
        reply = request.POST.get('reply', '').strip()
        if reply:
            ticket.reply = reply
            ticket.is_answered = True
            ticket.save()
            messages.success(request, 'Reply sent successfully.')
    return render(request, 'admin/reply_inquiry.html', {'ticket': ticket})
def inquiry_list(request):
    inquiries = Inquiry.objects.all()
    return render(request, 'admin/inquiries.html', {'inquiries': inquiries})

#--------------------- ADMIN SETTINGS ---------------------#


from .models import AdminSetting
from .forms import AdminSettingForm
from django.forms import modelformset_factory
#--------------------- ADMIN SETTINGS ---------------------#


@staff_member_required
def admin_settings(request):
    SettingsFormSet = modelformset_factory(
        AdminSetting,
        form=AdminSettingForm,
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        formset = SettingsFormSet(request.POST, request.FILES, queryset=AdminSetting.objects.all())
        if formset.is_valid():
            formset.save()
            return redirect('admin_settings')
    else:
        formset = SettingsFormSet(queryset=AdminSetting.objects.all())

    return render(request, 'admin/settings.html', {'formset': formset})

#--------------------- product views ---------------------
from .forms import ProductForm

@staff_member_required
def custom_dashboard(request):
    products = Product.objects.all().order_by('-created') 
    total_users = User.objects.count()
    recent_logins = AuditLog.objects.filter(
        action='login',
        timestamp__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()

    stamp_stats = StampApplication.objects.aggregate(
        total_orders=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        approved=Count('id', filter=Q(status='ready')),
        rejected=Count('id', filter=Q(status='rejected')),
    )

    # Product form logic
    if request.method == 'POST':
        name = request.POST['name']
        category = request.POST['category']
        price_tzs = request.POST['price_tzs']
        description = request.POST.get('description', '')
        image = request.FILES.get('image')

        Product.objects.create(
            name=name,
            category=category,
            price_tzs=price_tzs,
            description=description,
            image=image
        )
        return redirect('custom_dashboard')

    else:
        form = ProductForm(request.POST or None, request.FILES or None)
        if request.method == 'POST' or request.FILES:
            if form.is_valid():
                form.save()
                return redirect('custom_dashboard')
        
    context = {
        'total_users': total_users,
        'recent_logins': recent_logins,
        'total_orders': stamp_stats['total_orders'],
        'pending_orders': stamp_stats['pending'],
        'approved_orders': stamp_stats['approved'],
        'rejected_orders': stamp_stats['rejected'],
        'stamp_types': StampApplication.objects.values('stamp_type').annotate(total=Count('id')),
        'notifications': Notification.objects.order_by('-sent_at')[:5],
        'button_url': '/admin/some_page/',
        'form': form,
        'products': Product.objects.all()
    }
    profile_image_url = request.user.profile.image.url if hasattr(request.user, 'profile') and request.user.profile.image else None
    return render(request, 'admin/custom_dashboard.html', { 'profile_image_url' : profile_image_url, **context })



@staff_member_required
def admin_statistics(request):
    # Main stats
    stats = {
        "total_users": User.objects.count(),
        "support_tickets": {
            "total": SupportTicket.objects.count(),
            "open": SupportTicket.objects.filter(is_staff=True).count(),
            "in_progress": SupportTicket.objects.filter(status='in_progress').count(),
            "resolved": SupportTicket.objects.filter(status='resolved').count(),
        },
        "stamp_orders": {
            "total": StampOrder.objects.count(),
            "pending": StampOrder.objects.filter(status='pending').count(),
            "approved": StampOrder.objects.filter(status='approved').count(),
            "rejected": StampOrder.objects.filter(status='rejected').count(),
        },
        "inquiries": Inquiry.objects.count(),
        "ink_orders": {
            "total": Order.objects.count(),
            "pending": Order.objects.filter(status='pending').count(),
            "accepted": Order.objects.filter(status='accepted').count(),
            "delivered": Order.objects.filter(status='delivered').count(),
        },
        "advocates": {
            "total": Advocate.objects.count(),
            "verified": Advocate.objects.filter(is_verified=True).count(),
            "unverified": Advocate.objects.filter(is_verified=False).count(),
        },
        "stamp_applications": {
            "total": StampApplication.objects.count(),
            "collected": StampApplication.objects.filter(status='collected').count(),
            "pending": StampApplication.objects.filter(status='pending').count(),
            "payment_verified": StampApplication.objects.filter(payment_verified=True).count(),
        },
        "audit_logs": AuditLog.objects.count(),
        "notifications": {
            "total": Notification.objects.count(),
            "sent": Notification.objects.filter(is_sent=True).count(),
            "unread": Notification.objects.filter(read=False).count(),
        },
        "products": Product.objects.count(),
        "admin_settings": AdminSetting.objects.count(),
    }

    # User signups over last 30 days
    signup_data = (
        User.objects
        .filter(date_joined__gte=timezone.now() - timedelta(days=30))
        .annotate(signup_date=TruncDay('date_joined'))
        .values('signup_date')
        .annotate(count=Count('id'))
        .order_by('signup_date')
    )
    signup_labels = [item['signup_date'].strftime('%Y-%m-%d') for item in signup_data]
    signup_counts = [item['count'] for item in signup_data]

    # Support tickets over last 30 days
    ticket_data = (
        SupportTicket.objects
        .filter(timestamp__gte=timezone.now() - timedelta(days=30))
        .annotate(ticket_date=TruncDay('timestamp'))
        .values('ticket_date')
        .annotate(count=Count('id'))
        .order_by('ticket_date')
    )
    ticket_labels = [item['ticket_date'].strftime('%Y-%m-%d') for item in ticket_data]
    ticket_counts = [item['count'] for item in ticket_data]

    context = {
        "stats": stats,
        "signup_labels": signup_labels,
        "signup_counts": signup_counts,
        "ticket_labels": ticket_labels,
        "ticket_counts": ticket_counts,
    }

    return render(request, 'admin/statistics.html', context)



@staff_member_required
def admin_products(request):
    products = Product.objects.all().order_by('-created')
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('admin_products')
    return render(request, 'admin/products.html', {'form': form, 'products': products})

@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('admin_products')
    return render(request, 'admin/delete_product.html', {'product': product})
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_stamps(request):
    """Admin can manage stamps"""
    applications = StampApplication.objects.all().order_by('-application_date')
    return render(request, 'admin/admin_stamps.html', {'applications': applications})




@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('custom_dashboard')


@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('custom_dashboard')
    return render(request, 'admin/edit_product.html', {'form': form, 'product': product})


@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    return redirect('custom_dashboard')

#--------------------- Profile Views ---------------------#

from .forms import ProfileForm
from .models import UserProfile


@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('home')  # Or any success page
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})

#--------------------- Cart and Checkout ---------------------#

from .models import Product, Order

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Save product to user session or a cart model (depends on your cart logic)
    cart = request.session.get('cart', [])
    cart.append(product_id)
    request.session['cart'] = cart
    return redirect('home')

@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Create a quick order
    order = Order.objects.create(user=request.user, product=product, status='Pending')
    return redirect('checkout', order_id=order.id)