import string

from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.list import ListView 
from django.views.generic.edit import CreateView

from .forms import SubscriberForm

from .models import Subscriber

# Create your views here.

class SubscriberListView(ListView):
    model = Subscriber
    template_name = 'subscribers/subscriber_list.html' # Specify your template location
    context_object_name = 'subscribers' # Name for the list as a template variable

class HomeTemplateView(TemplateView):
    template_name = 'home.html'


class AddSubscriberView(CreateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/add_subscriber.html'
    success_url = reverse_lazy('subscriber_list')

"""
simulates a session for a subscriber
"""
def simulateSession(surname : string, serviceType : string, duration : int):
    pass


"""
generates invoice for a subscriber
returns (surname, dataVolume, minutes, charges)
"""
def invoice(surname : string) -> (string, int, int, int):
    pass
