from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView 
from django.views.generic.edit import CreateView

from .forms import SubscriberForm

from .models import Subscriber

# Create your views here.

class SubscriberListView(ListView):
    model = Subscriber
    template_name = 'subscribers/subscriber_list.html' # Specify your template location
    context_object_name = 'subscribers' # Name for the list as a template variable
    
class AddSubscriberView(CreateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/add_subscriber.html'
    success_url = reverse_lazy('subscriber_list')