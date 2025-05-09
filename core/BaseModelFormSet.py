from django.forms.models import BaseModelFormSet
from django import forms
from django.forms import modelformset_factory
from .models import AdminSetting  # Replace with the correct path to your AdminSetting model
from .forms import AdminSettingForm  # Replace with the correct path to your AdminSettingForm

class CustomAdminSettingsFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        # Example: ensure primary_color and secondary_color are not the same
        colors = {}
        for form in self.forms:
            if hasattr(form, 'cleaned_data') and form.cleaned_data:
                key = form.instance.setting_type
                val = form.cleaned_data.get('value')
                if key in ['primary_color', 'secondary_color']:
                    colors[key] = val
        if colors.get('primary_color') == colors.get('secondary_color'):
            raise forms.ValidationError("Primary and secondary colors must be different.")

# Then use it in your formset definition:
AdminSettingsFormSet = modelformset_factory(
    AdminSetting,
    form=AdminSettingForm,
    formset=CustomAdminSettingsFormSet,
    extra=0
)
