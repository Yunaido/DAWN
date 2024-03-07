from django.test import TestCase

from .models import Subscriber, Subscription, Service, Terminal, Technology, ThroughputPercentage
from .views import _simulate_session


def _maximum_throughput_chooser(terminal: Terminal):
    throughput_percentages = []
    for technology in terminal.supported_technologies.all():
        if technology.maximum_throughput is None or technology.achievable_throughput_percentages.count() == 0:
            continue
        throughput_percentages.append(
            (technology, technology.achievable_throughput_percentages.all().order_by('percentage').last()))
    return throughput_percentages


def _minimum_throughput_chooser(terminal: Terminal):
    throughput_percentages = []
    for technology in terminal.supported_technologies.all():
        if technology.maximum_throughput is None or technology.achievable_throughput_percentages.count() == 0:
            continue
        throughput_percentages.append(
            (technology, technology.achievable_throughput_percentages.all().order_by('percentage').first()))
    return throughput_percentages


def _10_percent_throughput_chooser(terminal: Terminal):
    throughput_percentages = []
    for technology in terminal.supported_technologies.all():
        if technology.maximum_throughput is None or technology.achievable_throughput_percentages.count() == 0:
            continue
        throughput_percentages.append(
            (technology, technology.achievable_throughput_percentages.all().order_by('percentage')[1]))
    return throughput_percentages


def _25_percent_throughput_chooser(terminal: Terminal):
    throughput_percentages = []
    for technology in terminal.supported_technologies.all():
        if technology.maximum_throughput is None or technology.achievable_throughput_percentages.count() == 0:
            continue
        throughput_percentages.append(
            (technology, technology.achievable_throughput_percentages.all().order_by('percentage')[2]))
    return throughput_percentages


# run with env variable DJANGO_SETTINGS_MODULE=dawn.settings
class SimulateSessionTest(TestCase):
    def setUp(self):
        # throughput percentages
        ThroughputPercentage.objects.create(signal_quality='G', percentage=0.5)
        ThroughputPercentage.objects.create(signal_quality='M', percentage=0.25)
        ThroughputPercentage.objects.create(signal_quality='L', percentage=0.1)
        ThroughputPercentage.objects.create(signal_quality='N/A', percentage=0.0)
        self.achievable_throughput_percentages = ThroughputPercentage.objects.all()

        # technologies
        self.technology_2g = Technology.objects.create(name='2G', voice_call_support=True)
        self.technology_3g = Technology.objects.create(
            name='3G',
            voice_call_support=False,
            maximum_throughput=20
        )
        self.technology_3g.achievable_throughput_percentages.set(self.achievable_throughput_percentages)
        self.technology_3g.save()
        self.technology_4g = Technology.objects.create(
            name='4G',
            voice_call_support=False,
            maximum_throughput=300
        )
        self.technology_4g.achievable_throughput_percentages.set(self.achievable_throughput_percentages)
        self.technology_4g.save()

        # terminals
        self.phair_phone = Terminal.objects.create(
            name='PhairPhone'
        )
        self.phair_phone.supported_technologies.set([self.technology_2g, self.technology_3g])
        self.phair_phone.save()

        self.pear_aphone_4s = Terminal.objects.create(
            name='Pear APhone 4S'
        )
        self.pear_aphone_4s.supported_technologies.set([self.technology_2g, self.technology_3g])
        self.pear_aphone_4s.save()

        self.s24plus = Terminal.objects.create(
            name='Samsung S42plus'
        )
        self.s24plus.supported_technologies.set([self.technology_2g, self.technology_3g, self.technology_4g])
        self.s24plus.save()

        self.gs_subscription = Subscription.objects.create(
            name='GS',
            basic_fee=800,
            minutes_included=0,
            price_per_extra_minute=8,
            data_volume_3g_4g=500
        )
        self.gm_subscription = Subscription.objects.create(
            name='GM',
            basic_fee=2200,
            minutes_included=100,
            price_per_extra_minute=6,
            data_volume_3g_4g=2000
        )
        self.gl_subscription = Subscription.objects.create(
            name='GL',
            basic_fee=4200,
            minutes_included=150,
            price_per_extra_minute=4,
            data_volume_3g_4g=5000
        )

        self.service_vc = Service.objects.create(
            name='VC',
            ran_technologies='2G',
            required_data_rate=0
        )
        self.service_bn = Service.objects.create(
            name='BN',
            ran_technologies='3G or 4G',
            required_data_rate=2
        )
        self.service_ad = Service.objects.create(
            name='AD',
            ran_technologies='3G4G',
            required_data_rate=10
        )
        self.service_av = Service.objects.create(
            name='AV',
            ran_technologies='3G4G',
            required_data_rate=75
        )

        i = 0
        for terminal in Terminal.objects.all():
            for subscription in Subscription.objects.all():
                Subscriber.objects.create(
                    forename='Test',
                    surname=f'Dummy {i}',
                    imsi=f'{262010000000000 + i}',
                    terminal_type=terminal,
                    subscription_type=subscription
                )

    def test_simulate_session_vc_maximum(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_vc, 1, _maximum_throughput_chooser)
            self.assertEqual(result, "")

    def test_simulate_session_bn_maximum(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_bn, 1, _maximum_throughput_chooser)
            self.assertEqual(result, "")

    def test_simulate_session_bn_25(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_bn, 1, _25_percent_throughput_chooser)
            self.assertEqual(result, "")

    def test_simulate_session_bn_10(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_bn, 1, _10_percent_throughput_chooser)
            self.assertEqual(result, "")

    def test_simulate_session_bn_minimum(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_bn, 1, _minimum_throughput_chooser)
            self.assertEqual(result, "not enough bandwidth")


    def test_simulate_session_ad_maximum(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_ad, 1, _maximum_throughput_chooser)
            self.assertEqual(result, "")

    def test_simulate_session_ad_25(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_ad, 1, _25_percent_throughput_chooser)
            if subscriber.terminal_type.name == 'Samsung S42plus':
                self.assertEqual(result, "")
            else:
                self.assertEqual(result, "not enough bandwidth")

    def test_simulate_session_ad_10(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_ad, 1, _25_percent_throughput_chooser)
            if subscriber.terminal_type.name == 'Samsung S42plus':
                self.assertEqual(result, "")
            else:
                self.assertEqual(result, "not enough bandwidth")

    def test_simulate_session_ad_minimum(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_ad, 1, _minimum_throughput_chooser)
            self.assertEqual(result, "not enough bandwidth")

    def test_simulate_session_av_maximum(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_av, 1, _maximum_throughput_chooser)
            if subscriber.terminal_type.name == 'Samsung S42plus':
                self.assertEqual(result, "")
            else:
                self.assertEqual(result, "not enough bandwidth")

    def test_simulate_session_av_25(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_av, 1, _25_percent_throughput_chooser)
            if subscriber.terminal_type.name == 'Samsung S42plus':
                self.assertEqual(result, "")
            else:
                self.assertEqual(result, "not enough bandwidth")

    def test_simulate_session_av_10(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_av, 1, _10_percent_throughput_chooser)
            self.assertEqual(result, "not enough bandwidth")

    def test_simulate_session_av_minimum(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_av, 1, _minimum_throughput_chooser)
            self.assertEqual(result, "not enough bandwidth")

    def test_simulate_session_volume_exceeded(self):
        for subscriber in Subscriber.objects.all():
            result = _simulate_session(subscriber, self.service_ad, int(subscriber.subscription_type.data_volume_3g_4g.real / 10 + 1), _maximum_throughput_chooser)
            self.assertEqual(result, "not enough data volume")
