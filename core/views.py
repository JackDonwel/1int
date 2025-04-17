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
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from django.db.models import Count, Q
import qrcode

from .models import (
    Advocate, StampApplication, AuditLog, Notification, Order, SupportTicket, Inquiry, StampOrder, Product, AuditLog
)
from .forms import StampApplicationForm, SupportTicketForm, StampOrderForm
from .utils import apply_stamp_to_pdf

logger = logging.getLogger(__name__)


# ------------------- USER VIEWS ------------------- #

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
    """User submits a stamp application, receives a QR result"""
    qr_image_base64 = None
    if request.method == 'POST':
        form = StampApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.advocate = request.user.advocate_profile
            application.save()

            if request.POST.get('include_ink'):
                Order.objects.create(
                    user=request.user,
                    color_type='blue1',
                    quantity=1,
                    payment_method='mpesa',
                    delivery_address=form.cleaned_data['collection_office'],
                    status='processing'
                )

            # QR Code generation
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

            messages.success(request, "Application submitted successfully!")
            return render(request, 'qr_result.html', {
                'qr_image': qr_image_base64,
                'application': application
            })
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
def custom_logout(request):
    logout(request)
    return redirect('home')

@require_http_methods(["GET"])
@login_required
def immediate_logout(request):
    logout(request)
    return redirect('login')


def logout_confirmation(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'logout_confirm.html')


def verify_stamp(request, qr_hash):
    """Public endpoint to verify QR code"""
    application = get_object_or_404(StampApplication, qr_hash=qr_hash)
    return render(request, 'verify_stamp.html', {
        'valid': application.status in ['ready', 'collected'],
        'application': application,
        'advocate': application.advocate,
        'verification_date': timezone.now()
    })


def login(request):
    """Login with audit logging"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        ip = get_client_ip(request)

        if user:
            auth_login(request, user)
            AuditLog.objects.create(user=user, action='login', details='Successful login', ip_address=ip)
            return redirect('/')
        else:
            AuditLog.objects.create(user=None, action='failed_login', details=f"Username: {username}", ip_address=ip)
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        username, email, password = request.POST.get('username'), request.POST.get('email'), request.POST.get('password')
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists'})

        user = User.objects.create_user(username=username, email=email, password=password)
        Advocate.objects.create(user=user, tls_id=f"TEMP-{user.id}", chapter="Pending Assignment", phone_number="+255000000000")
        auth_login(request, user)
        return redirect('/')
    return render(request, 'signup.html')


def error(request):
    return render(request, 'error.html')


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
        formset = SettingsFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('admin_settings')
    else:
        formset = SettingsFormSet()

    return render(request, 'admin/settings.html', {
        'formset': formset,
        'setting_types': AdminSetting.SETTING_TYPES
    })
    
    
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

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('custom_dashboard')



def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('custom_dashboard')
    return render(request, 'admin/edit_product.html', {'form': form, 'product': product})

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
