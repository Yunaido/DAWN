from django import forms

from .models import Subscriber, Session


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['forename', 'surname', 'imsi', 'terminal_type', 'subscription_type']

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['subscriber', 'service', 'duration']