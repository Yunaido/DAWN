from django import forms

from .models import Service, Subscriber, Session, Invoice


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['forename', 'surname', 'imsi', 'terminal_type', 'subscription_type']
        
class InvoiceForm(forms.Form):
    subscriber_id = forms.ModelChoiceField(queryset=Subscriber.objects.all(), label="Select Subscriber")

class SessionForm(forms.Form):
    subscriber_id = forms.ModelChoiceField(queryset=Subscriber.objects.all(), label="Select Subscriber")
    service_id = forms.ModelChoiceField(queryset=Service.objects.all(), label="Select Service")
    duration = forms.IntegerField(label="Select Duration")