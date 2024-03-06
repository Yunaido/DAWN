from django import forms

from .models import Subscriber, Session, Invoice


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['forename', 'surname', 'imsi', 'terminal_type', 'subscription_type']
        
class InvoiceForm(forms.Form):
    subscriber_id = forms.ModelChoiceField(queryset=Subscriber.objects.all(), label="Select Subscriber")
    

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['subscriber', 'service', 'duration']