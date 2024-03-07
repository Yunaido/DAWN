from django import forms

from .models import Subscriber, Session


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['forename', 'surname', 'imsi', 'terminal_type', 'subscription_type']
        
class InvoiceForm(forms.Form):
    subscriber_id = forms.ModelChoiceField(queryset=Subscriber.objects.all(), label="Select Subscriber")

class SessionForm(forms.ModelForm):
    # subscriber = forms.ModelChoiceField(queryset=Subscriber.objects.all(), label="Select Subscriber")
    # service = forms.ModelChoiceField(queryset=Service.objects.all(), label="Select Service")
    # duration = forms.IntegerField(label="Select Duration")
    
    class Meta:
        model = Session
        fields = ['subscriber', 'service', 'duration']

class UploadCSVForm(forms.Form):
    csv_file = forms.FileField()