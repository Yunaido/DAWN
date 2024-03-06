from django.db import models
from django.utils.translation import gettext_lazy
from django.forms import ValidationError

# Create your models here.

class ThroughputPercentage(models.Model):
    GOOD = 'G'
    MEDIUM = 'M'
    LOW = 'L'
    N_A = 'N'
    SIGNAL_QUALITY_CHOICES = [
        (GOOD, 'Good'),
        (MEDIUM, 'Medium'),
        (LOW, 'Low'),
        (N_A, 'N/A'),
    ]
    signal_quality = models.CharField(max_length=2, choices=SIGNAL_QUALITY_CHOICES)
    percentage = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.signal_quality} ({self.percentage *100}%)"

class Technology(models.Model):
    TYPE_CHOICES = [
        ('2G', '2G (GSM)'),
        ('3G', '3G (HSPA)'),
        ('4G', '4G (LTE)'),
    ]
    name = models.CharField(max_length=50, choices=TYPE_CHOICES)
    maximum_throughput = models.PositiveIntegerField(null=True, blank=True)
    achievable_throughput_percentages = models.ManyToManyField(ThroughputPercentage)
    voice_call_support = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name}"

class Terminal(models.Model):
    name = models.CharField(max_length=100)
    supported_technologies = models.ManyToManyField(Technology)
    
    def __str__(self) -> str:
        return f"{self.name}"

class Subscription(models.Model):
    SUBSCRIPTION_TYPES = [
        ('GS', 'GreenMobil S'),
        ('GM', 'GreenMobil M'),
        ('GL', 'GreenMobil L'),
    ]
    name = models.CharField(max_length=50, choices=SUBSCRIPTION_TYPES)
    basic_fee = models.DecimalField(max_digits=5, decimal_places=2)
    minutes_included = models.PositiveIntegerField()
    price_per_extra_minute = models.DecimalField(max_digits=3, decimal_places=2)
    data_volume_3g_4g = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.name}"
    
class Subscriber(models.Model):
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    imsi = models.CharField(max_length=15, unique=True)
    terminal_type = models.ForeignKey(Terminal, on_delete=models.SET_NULL, null=True)
    subscription_type = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    
    def clean(self):
        super().clean()
        # Check if IMSI is 15 digits long
        if not self.imsi.isdigit() or len(self.imsi) != 15:
            raise ValidationError(gettext_lazy("IMSI must be exactly 15 digits long."))
        # Extract MCC and MNC from IMSI
        mcc = self.imsi[:3]
        mnc = self.imsi[3:5]
        # Check if MCC is for Germany (262) and MNC is common for Germany (01)
        if mcc != '262' or mnc not in ['01', '02', '03', '04', '05', '06', '07', '08', '09']:
            raise ValidationError(gettext_lazy("IMSI must be a German IMSI."))

    def __str__(self) -> str:
        return f"{self.surname} {self.forename} | {self.terminal_type.name} | {self.subscription_type}"

class Service(models.Model):
    SERVICE_TYPES = [
        ('VC', 'Voice call'),
        ('BN', 'Browsing and social networking'),
        ('AD', 'App download'),
        ('AV', 'Adaptive HD video'),
    ]
    RAN_TECHNOLOGIES = [
        ('2G', '2G'),
        ('3G4G', '3G or 4G'),
    ]
    name = models.CharField(max_length=50, choices=SERVICE_TYPES)
    ran_technologies = models.CharField(max_length=5, choices=RAN_TECHNOLOGIES)
    required_data_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name} | {self.ran_technologies} | {self.required_data_rate}"

class Session(models.Model):
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    duration = models.PositiveIntegerField()
    data_volume = models.PositiveIntegerField()
    call_minutes = models.PositiveIntegerField()
