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
    
    phone_number = forms.CharField(
        max_length=15,
        label='Phone Number',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
 
    class Meta:
        model = StampApplication
        fields = ['stamp_type', 'stamp_size', 'collection_office', 'phone_number']


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

from django import forms
from .models import AdminSetting 

class AdminSettingForm(forms.ModelForm):
    help_texts = {
        'background_image': 'Recommended size: 1920x1080px',
        'logo': 'PNG with transparent background (300x100px)',
        'primary_color': 'Main brand color for headers and buttons',
        'secondary_color': 'Accent color for UI highlights',
        'custom_css': 'Paste custom CSS here',
        'custom_js': 'Paste custom JavaScript here',
    }

    class Meta:
        model = AdminSetting
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.set_dynamic_field()

    def set_dynamic_field(self):
        field_type = self.instance.setting_type

        if field_type in ['logo', 'background_image']:
            self.fields['value'] = forms.ImageField(
                required=False,
                widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
            )
        elif field_type in ['primary_color', 'secondary_color']:
            self.fields['value'] = forms.CharField(
                widget=forms.TextInput(attrs={
                    'type': 'color',
                    'class': 'form-control form-control-color'
                })
            )
        elif field_type == 'custom_css':
            self.fields['value'] = forms.CharField(
                widget=forms.Textarea(attrs={
                    'class': 'code-editor',
                    'rows': 8,
                    'spellcheck': 'false'
                })
            )
        elif field_type == 'custom_js':
            self.fields['value'] = forms.CharField(
                widget=forms.Textarea(attrs={
                    'class': 'code-editor',
                    'rows': 8,
                    'spellcheck': 'false'
                })
            )

        self.fields['value'].help_text = self.help_texts.get(
            field_type,
            'Setting value configuration'
        )


# Admin settings formset
from django.forms import modelformset_factory
from django.forms.models import BaseModelFormSet

AdminSettingsFormSet = modelformset_factory(
    AdminSetting,
    form=AdminSettingForm,
    formset=BaseModelFormSet,
    extra=0
)   
      
      
      

  
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
