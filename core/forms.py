from django import forms
from .models import StampApplication
from .models import SupportTicket
from .models import StampOrder
from .models import AdminSetting

# If you're not using STAMP_TYPES and STAMP_SIZES from the model, define them here
STAMP_TYPES = [
    ('certification', 'Certification'),
    ('notarization', 'Notarization'),
]

STAMP_SIZES = [
    ('small', 'Small'),
    ('medium', 'Medium'),
    ('large', 'Large'),
]

class StampApplicationForm(forms.ModelForm):
    stamp_type = forms.ChoiceField(
        choices=STAMP_TYPES,
        label='Stamp Type',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    stamp_size = forms.ChoiceField(
        choices=STAMP_SIZES,
        label='Stamp Size',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    collection_office = forms.CharField(
        max_length=100,
        label='Collection Office',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    payment_receipt = forms.FileField(
        label='Payment Receipt',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = StampApplication
        fields = ['stamp_type', 'stamp_size', 'collection_office', 'payment_receipt']


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['message', 'image']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Type your message...'}),
        }
        
class StampOrderForm(forms.ModelForm):
    class Meta:
        model = StampOrder
        fields = ['stamp_type', 'description', 'quantity']
        
        
        # Admin settings
        
class AdminSettingForm(forms.ModelForm):
    class Meta:
        model = AdminSetting
        fields = ['key', 'value', 'data_type', 'description']

class AdminSettingsFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = AdminSetting.objects.all().order_by('key')     
        
        
    #---------- product forms ----------- 
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price_tzs', 'description', 'image']  # Make sure field names match
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }
##---------- user profile forms -----------


from .models import UserProfile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'ward', 'district', 'region', 'country', 'law_firm', 'chapters',
            'advocate_chapter', 'advocate_title', 'practicing_law',
            'practicing_status', 'id_type', 'id_number', 'id_expiry_date',
            'id_image', 'tls_id'
        ]
        widgets = {
            'id_expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
