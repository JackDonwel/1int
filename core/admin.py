# admin.py
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from django.db.models import Count, Q
from django.urls import path
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.sites import NotRegistered
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
import json
from .models import Order

from .models import Advocate, StampApplication, AuditLog, Notification, Order, SupportTicket

# ------ Custom Admin Site ------
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_header = "TLS Admin"
    site_title = "TLS Admin"
    index_title = "Dashboard"
    site_url = None

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(custom_dashboard), name='custom_dashboard'),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = 'myadmin:custom_dashboard'
        return super().index(request, extra_context)

custom_admin = CustomAdminSite(name='myadmin')


# ------ ADMIN VIEWS ------
def is_admin(user):
    return user.is_staff or user.is_superuser
@staff_member_required
@user_passes_test(is_admin)
def admin_statistics(request):
   
    context = {
        'total_users': User.objects.count(),
        'total_advocates': Advocate.objects.count(),
        'total_applications': StampApplication.objects.count(),
        'application_status_counts': json.dumps(
            dict(
                StampApplication.objects.values('status')
                .annotate(count=models.Count('id'))
                .values_list('status', 'count')
            ),
            cls=DjangoJSONEncoder
        ),
        'recent_applications': StampApplication.objects.select_related('advocate__user').order_by('-application_date')[:10],
    }

    return render(request, 'admin/admin_statistics.html', context)


@staff_member_required
def admin_statistics(request):
    # More we'll add detailed statistics
    order_stats = {
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
    }
    
    application_stats = {
        'pending': StampApplication.objects.filter(status='pending').count(),
        'payment': StampApplication.objects.filter(status='payment').count(),
        'production': StampApplication.objects.filter(status='production').count(),
        'ready': StampApplication.objects.filter(status='ready').count(),
    }
    
    return render(request, 'admin/statistics.html', {
        'order_stats': order_stats,
        'application_stats': application_stats
    })
    

def is_admin(user):
    return user.is_superuser

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'quantity', 'status', 'created']
    ordering = ['-created']
    
admin.site.register(Order, OrderAdmin)

@staff_member_required
def admin_orders(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {new_status}")
        return redirect('orders')
    orders = Order.objects.all().order_by('-created')
    return render(request, 'admin/orders.html', {'orders': orders})

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



@staff_member_required
def admin_queue(request):
    pending_applications = StampApplication.objects.filter(status='pending')
    return render(request, 'admin/queue.html', {
        'applications': pending_applications
    })  

@staff_member_required
def custom_dashboard(request):
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

    context = {
        'total_users': total_users,
        'recent_logins': recent_logins,
        'total_orders': stamp_stats['total_orders'],
        'pending_orders': stamp_stats['pending'],
        'approved_orders': stamp_stats['approved'],
        'rejected_orders': stamp_stats['rejected'],
        'stamp_types': StampApplication.objects.values('stamp_type').annotate(total=Count('id')),
        'notifications': Notification.objects.order_by('-sent_at')[:5],
        'button_url': '/admin/some_page/'  # Button URL or any path
    }
    return render(request, 'admin/custom_dashboard.html', context)

# ------ Advocate Inline & Admin ------
class AdvocateInline(admin.StackedInline):
    model = Advocate
    can_delete = False
    verbose_name_plural = 'Advocate Details'
    fields = ('tls_id', 'chapter', 'phone_number', 'is_verified')
    classes = ('collapse',)
    extra = 0


class ChapterFilter(admin.SimpleListFilter):
    title = 'Chapter'
    parameter_name = 'chapter'

    def lookups(self, request, model_admin):
        chapters = Advocate.objects.values_list('chapter', flat=True).distinct()
        return [(chapter, chapter) for chapter in chapters]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(advocate_profile__chapter=self.value())
        return queryset


class CustomUserAdmin(UserAdmin):
    inlines = (AdvocateInline,)
    list_display = ('username', 'email', 'full_name', 'is_staff', 'tls_badge', 'chapter')
    list_filter = ('is_staff', 'is_superuser', 'is_active', ChapterFilter)
    search_fields = ('username', 'email', 'advocate_profile__tls_id')

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'

    def tls_badge(self, obj):
        if hasattr(obj, 'advocate_profile'):
            return format_html(
                '<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">{}</span>',
                obj.advocate_profile.tls_id
            )
        return "-"
    tls_badge.short_description = 'TLS ID'

    def chapter(self, obj):
        return getattr(obj.advocate_profile, 'chapter', '-')
    chapter.short_description = 'Chapter'


class AdvocateAdmin(admin.ModelAdmin):
    list_display = ('user', 'tls_id', 'chapter', 'is_verified', 'date_registered')
    search_fields = ('tls_id', 'user__username', 'chapter', 'phone_number')
    list_filter = ('is_verified', 'chapter', 'date_registered')
    autocomplete_fields = ('user',)
    readonly_fields = ('date_registered',)
    fieldsets = (
        (None, {'fields': ('user', 'tls_id', 'chapter')}),
        ('Contact Info', {'fields': ('phone_number', 'email')}),
        ('Verification', {'fields': ('is_verified', 'date_registered')}),
    )


# Register all to custom_admin
try:
    admin.site.unregister(User)
except NotRegistered:
    pass

custom_admin.register(User, CustomUserAdmin)
custom_admin.register(Advocate, AdvocateAdmin)
custom_admin.register(StampApplication)
custom_admin.register(AuditLog)
custom_admin.register(Notification)

admin.site = custom_admin