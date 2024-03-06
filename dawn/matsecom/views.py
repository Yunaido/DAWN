from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, FormView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .forms import SubscriberForm, SessionForm, InvoiceForm

from .models import Subscriber, Session, Invoice, Service, Subscription


# Create your views here.

class SubscriberListView(ListView):
    model = Subscriber
    template_name = 'subscribers/subscriber_list.html' # Specify your template location
    context_object_name = 'subscribers' # Name for the list as a template variable

class HomeTemplateView(TemplateView):
    template_name = 'home.html'

class SessionView(CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'session/simulate_session.html'

class AddSubscriberView(CreateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/add_subscriber.html'
    success_url = reverse_lazy('subscriber_list')

class InvoiceView(CreateView):
    template_name = 'invoices/get_invoice.html'


class CreateInvoiceView(FormView):
    template_name = 'invoices/create_invoice.html'
    form_class = InvoiceForm
    success_url = reverse_lazy('invoice_success')

    def form_valid(self, form):
        subscriber_id = form.cleaned_data['subscriber_id']
        surname = subscriber_id.surname
        result = invoice(surname)
        # You can now use the result to render a template or redirect
        return super().form_valid(form)


# simulates a session for a subscriber
# returns a str:
# - "" if session simulation was successful
# - "calling not possible" if the subscriber's terminal does not support voice calls
# - "not enough bandwidth" if the throughput is not sufficient for the service
# - "not enough data volume" if the subscriber's subscription does not include enough data volume
def simulate_session(surname: str, service: Service, duration: int) -> str:
    subscriber = Subscriber.objects.get(surname=surname)
    data_volume = 0
    call_minutes = 0

    if service.name == 'VC':
        calling_possible = False
        for t in subscriber.terminal_type.supported_technologies.all():
            if t.voice_call_support:
                calling_possible = True
                break
        if not calling_possible:
            return "calling not possible"
        call_minutes = _get_call_minutes_from_seconds(duration)
    else:
        sessions = Session.objects.filter(subscriber=subscriber)
        (used_data_volume, used_call_minutes, charges) = _sum_sessions(sessions, subscriber.subscription)

        throughput_percentages = _get_random_throughput_percentage_for_terminal_technologies(subscriber.terminal_type)
        fastest_throughput = throughput_percentages[0]
        for t in throughput_percentages:
            if t[0].maximum_throughput * t[1] > fastest_throughput[0].maximum_throughput * fastest_throughput[1]:
                fastest_throughput = t
        if service.required_data_rate > fastest_throughput[0].maximum_throughput * fastest_throughput[1]:
            return "not enough bandwidth"
        data_volume = fastest_throughput[0].maximum_throughput * fastest_throughput[1] * duration
        if used_data_volume + data_volume > subscriber.subscription.data_volume_3g_4g:
            return "not enough data volume"

    Session.objects.create(
        subscriber=subscriber,
        service=service,
        timestamp=timezone.now(),
        duration=duration,
        data_volume=data_volume,
        call_minutes=call_minutes,
        paid=False
    )
    return ""


# generates invoice for a subscriber
# returns (surname, dataVolume, minutes, charges)
def invoice(surname: str) -> (str, int, int, int):
    subscriber = Subscriber.objects.get(surname=surname)
    sessions = Session.objects.filter(subscriber=subscriber, paid=False)
    for session in sessions:
        session.paid = True
        session.save()
    (data_volume, minutes, charges) = _sum_sessions(sessions, subscriber.subscription)
    return subscriber.surname, data_volume, minutes, charges


# returns (dataVolume, minutes, charges)
# does not check if used data exceeds the included data volume
def _sum_sessions(sessions: list, subscription: Subscription) -> (int, int, int):
    data_volume = 0
    minutes = 0
    for session in sessions:
        data_volume += session.data_volume
        minutes += session.call_minutes
    charges = subscription.basic_fee
    if minutes > subscription.minutes_included:
        charges += (minutes - subscription.minutes_included) * subscription.price_per_extra_minute
    return data_volume, minutes, charges


# returns a list of tuples (technology, throughput_percentage), choosing a random throughput percentage for each
# technology
def _get_random_throughput_percentage_for_terminal_technologies(terminal):
    throughput_percentages = []
    for technology in terminal.supported_technologies.all():
        throughput_percentages.append(
            (technology, technology.achievable_throughput_percentages.all().order_by('?').first()))
    return throughput_percentages


# returns the number of call minutes for a given duration in seconds
# rounds up to the next minute
def _get_call_minutes_from_seconds(sec: int) -> int:
    return (sec // 60) + 1
