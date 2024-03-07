from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, FormView, DetailView, DeleteView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .forms import SubscriberForm, SessionForm, InvoiceForm

from .models import Subscriber, Session, Invoice, Service, Subscription


# Create your views here.

class HomeTemplateView(TemplateView):
    template_name = 'home.html'

class SubscriberListView(ListView):
    model = Subscriber
    template_name = 'subscribers/subscriber_list.html' # Specify your template location
    context_object_name = 'subscribers' # Name for the list as a template variable

class SubscriberDetailView(DetailView):
    model = Subscriber
    template_name = 'subscribers/subscriber_detail.html' # Pfad zur Template-Datei

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Hier können Sie zusätzliche Kontextdaten hinzufügen, falls erforderlich
        return context
    
class SubscriberDeleteView(DeleteView):
    model = Subscriber
    success_url = reverse_lazy('subscriber_list')

class AddSubscriberView(CreateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/add_subscriber.html'
    success_url = reverse_lazy('subscriber_list')

class SessionView(CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'session/simulate_session.html'

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

class SimulateSessionView(FormView):
    template_name = 'session/simulate_session.html'
    form_class = SessionForm
    # success_url = reverse_lazy('invoice_success')

    def form_valid(self, form):
        subscriber = form.cleaned_data['subscriber_id']
        service = form.cleaned_data['service_id']
        duration = form.cleaned_data['duration']
        result = simulate_session(subscriber, service, duration)
        # You can now use the result to render a template or redirect
        return super().form_valid(form)


# simulates a session for a subscriber
# returns a str:
# - "" if session simulation was successful
# - "calling not possible" if the subscriber's terminal does not support voice calls
# - "not enough bandwidth" if the throughput is not sufficient for the service
# - "not enough data volume" if the subscriber's subscription does not include enough data volume
def simulate_session(subscriber: Subscriber, service: Service, duration: int) -> str:
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
        (used_data_volume, used_call_minutes, charges) = _sum_sessions(sessions, subscriber.subscription_type)

        throughput_percentages = _get_random_throughput_percentage_for_terminal_technologies(subscriber.terminal_type)
        fastest_throughput = throughput_percentages[0]
        for t in throughput_percentages:
            if t[0].maximum_throughput * t[1].percentage > fastest_throughput[0].maximum_throughput * fastest_throughput[1].percentage:
                fastest_throughput = t
        if service.required_data_rate > fastest_throughput[0].maximum_throughput * fastest_throughput[1].percentage:
            return "not enough bandwidth"
        data_volume = fastest_throughput[0].maximum_throughput * fastest_throughput[1].percentage * duration
        if used_data_volume + data_volume > subscriber.subscription_type.data_volume_3g_4g:
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
    (data_volume, minutes, charges) = _sum_sessions(sessions, subscriber.subscription_type)
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
        if technology.maximum_throughput is None or technology.achievable_throughput_percentages.count() == 0:
            continue
        throughput_percentages.append(
            (technology, technology.achievable_throughput_percentages.all().order_by('?').first()))
    return throughput_percentages


# returns the number of call minutes for a given duration in seconds
# rounds up to the next minute
def _get_call_minutes_from_seconds(sec: int) -> int:
    return (sec // 60) + 1
