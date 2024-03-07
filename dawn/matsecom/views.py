import csv
import io

from django.core.files.storage import default_storage
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.views.generic import View, TemplateView, FormView, DetailView, DeleteView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .forms import SubscriberForm, SessionForm, InvoiceForm, UploadCSVForm
from .models import Invoice, Subscriber, Session, Service, Subscription, Terminal


# Create your views here.

class HomeTemplateView(TemplateView):
    template_name = 'home.html'

class SubscriberListView(ListView):
    model = Subscriber
    template_name = 'subscribers/subscriber_list.html' # Specify your template location
    context_object_name = 'subscribers' # Name for the list as a template variable
    
    def get(self, request, *args, **kwargs):
        action = request.GET.get('action')
        if action == 'download':
            return self.get_csv(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            # Save the file temporarily
            temp_file_path = default_storage.save(csv_file.name, csv_file)
            # Read the file content
            with default_storage.open(temp_file_path, 'r') as f:
                csv_content = f.read()
            # Import subscribers from the CSV content
            load_from_csv(csv_content)
            # Clean up the temporary file
            default_storage.delete(temp_file_path)
            return JsonResponse({'status': 'success', 'message': 'Subscribers imported successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'})
        
    def get_csv(self, request, *args, **kwargs):
        # Generate CSV content
        csv_content = get_all_subscribers_as_csv()
        # Create a response with the CSV content
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
        return response

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

    def form_valid(self, form):
        response = super().form_valid(form)
        # Hier können Sie zusätzliche Logik hinzufügen, falls erforderlich
        return response

class SessionView(CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'session/simulate_session.html'

class CreateInvoiceView(FormView):
    template_name = 'invoices/create_invoice.html'
    form_class = InvoiceForm
    success_url = reverse_lazy('invoice_details')

    def form_valid(self, form):
        subscriber = form.cleaned_data['subscriber_id']
        generated_invoice = invoice(subscriber) # Rufen Sie die invoice-Funktion auf
        # Speichern Sie die Ergebnisse in der Sitzung, um sie im nächsten Schritt zu verwenden
        return HttpResponseRedirect(reverse('invoice_details', args=[generated_invoice.id]))

class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'invoices/invoice_detail.html' # Specify the template name
    context_object_name = 'invoice'

class SessionListView(ListView):
    model = Session
    template_name = 'session/session_list.html' # Specify your template location
    context_object_name = 'sessions' # Name for the list as a template variable

class SimulateSessionView(FormView):
    model = Session
    form_class = SessionForm
    template_name = 'session/simulate_session.html'
    success_url = reverse_lazy('session_list')

    def form_valid(self, form):
        subscriber = form.cleaned_data['subscriber']
        service = form.cleaned_data['service']
        duration = form.cleaned_data['duration']
        result = simulate_session(subscriber, service, duration)
        if result != "":
            form.add_error(None, result) # Add a non-field error
            return self.form_invalid(form) # Redirect to the form with errors
        return super().form_valid(form)

    def form_invalid(self, form):
        # You can add custom logic here if needed, or just pass the form with errors to the template
        return self.render_to_response(self.get_context_data(form=form))


def simulate_session(subscriber: Subscriber, service: Service, duration: int):
    return _simulate_session(subscriber, service, duration, lambda x: _get_random_throughput_percentage_for_terminal_technologies(x))


# simulates a session for a subscriber
# throughput chooser should be a function Terminal -> list of tuples (Technology, ThroughputPercentage)
# default is the random throughput chooser, for testing other throughput choosers can be injected
# returns a str:
# - "" if session simulation was successful
# - "calling not possible" if the subscriber's terminal does not support voice calls
# - "not enough bandwidth" if the throughput is not sufficient for the service
# - "not enough data volume" if the subscriber's subscription does not include enough data volume
def _simulate_session(subscriber: Subscriber, service: Service, duration: int, throughput_chooser) -> str:
    data_volume = 0
    call_seconds = 0

    if service.name == 'VC':
        calling_possible = False
        for t in subscriber.terminal_type.supported_technologies.all():
            if t.voice_call_support:
                calling_possible = True
                break
        if not calling_possible:
            return "calling not possible"
        call_seconds = duration
    else:
        sessions = _my_database_filter(Session.objects.all(), lambda x: x.subscriber == subscriber)
        (used_data_volume, used_call_seconds, charges) = _sum_sessions(sessions, subscriber.subscription_type)

        throughput_percentages = throughput_chooser(subscriber.terminal_type)
        fastest_throughput = throughput_percentages[0]
        for t in throughput_percentages:
            if t[0].maximum_throughput * t[1].percentage > fastest_throughput[0].maximum_throughput * \
                    fastest_throughput[1].percentage:
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
        call_seconds=call_seconds,
        paid=False
    )
    return ""


# generates invoice for a subscriber
# returns (surname, dataVolume, minutes, charges)
def invoice(subscriber: Subscriber) -> Invoice:
    sessions = _my_database_filter(Session.objects.all(), lambda x: x.subscriber == subscriber and not x.paid)
    for session in sessions:
        session.paid = True
        session.save()

    (data_volume, call_minutes, charges) = _sum_sessions(sessions, subscriber.subscription_type)
    return Invoice.objects.create(
        subscriber=subscriber,
        timestamp=timezone.now,
        data_volume=data_volume,
        call_minutes=call_minutes,
        charges=charges
    )


def get_all_subscribers_as_csv():
    subscribers = Subscriber.objects.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['forename', 'surname', 'imsi', 'terminal_type', 'subscription_type'])
    for subscriber in subscribers:
        writer.writerow([subscriber.forename, subscriber.surname, subscriber.imsi, subscriber.terminal_type.name,
                         subscriber.subscription_type.name])
    return output.getvalue()


# returns "" if all subscribers were created
# returns error message otherwise
def load_from_csv(csv_str: str) -> str:
    data = io.StringIO(csv_str)
    reader = csv.reader(data)
    next(reader)
    for row in reader:
        if _my_database_filter(Subscriber.objects.all(), lambda x: x.imsi == row[2]):
            # subscriber already exists
            continue
        if not Terminal.objects.get(name=row[3]):
            return "terminal " + row[3] + " of user " + row[0] + " " + row[1] + " does not exist"
        if not Subscription.objects.get(name=row[4]):
            return "subscription " + row[4] + " of user " + row[0] + " " + row[1] + " does not exist"
        Subscriber.objects.create(
            forename=row[0],
            surname=row[1],
            imsi=row[2],
            terminal_type=Terminal.objects.get(name=row[3]),
            subscription_type=Subscription.objects.get(name=row[4])
        )
    return ""


# returns (dataVolume, minutes, charges)
# does not check if used data exceeds the included data volume
def _sum_sessions(sessions: list, subscription: Subscription) -> (int, int, int):
    data_volume = 0
    call_seconds = 0
    for session in sessions:
        data_volume += session.data_volume
        call_seconds += session.call_seconds
    charges = subscription.basic_fee
    call_minutes = _get_call_minutes_from_seconds(call_seconds)
    if call_minutes > subscription.minutes_included:
        charges += (call_minutes - subscription.minutes_included) * subscription.price_per_extra_minute
    return data_volume, call_seconds, charges


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


# because of encryption, the .filter function used by django doesnt work properly, so we use this function instead
# this is not very performant, but the easiest solution for now. A better solution would be to use something like
# https://github.com/dcwatson/django-pgcrypto , which handles the encryption in the database itself and not in the
# django code and thus keeps SQL filters working
def _my_database_filter(database_list, evaluation_function):
    return [x for x in database_list if evaluation_function(x)]
