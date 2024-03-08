from django import forms

from .models import Invoice, Subscriber, Session


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['forename', 'surname', 'imsi', 'terminal_type', 'subscription_type']
        widgets = {
            'forename': forms.TextInput(attrs={'maxlength': 100}),
            'surname': forms.TextInput(attrs={'maxlength': 100}),
            'imsi': forms.NumberInput(attrs={
                'min': 262010000000000,
                'max': 262099999999999,
            }),
        }
        
class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['subscriber']

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['subscriber', 'service', 'duration']
        widgets = {
            'duration': forms.NumberInput(attrs={
                'min': 1,
                'max': 2500000,
            }),
        }

class UploadCSVForm(forms.Form):
    csv_file = forms.FileField()