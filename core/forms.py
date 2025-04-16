from django import forms
from .models import StampApplication
from .models import SupportTicket


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