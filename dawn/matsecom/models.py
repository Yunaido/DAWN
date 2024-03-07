from django.db import models
from django.utils.translation import gettext_lazy
from django.forms import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

from encrypted_model_fields.fields import EncryptedCharField

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
    basic_fee = models.PositiveIntegerField(null=False, blank=False)
    minutes_included = models.PositiveIntegerField()
    price_per_extra_minute = models.PositiveIntegerField(null=False, blank=False)
    data_volume_3g_4g = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.name}"
    
class Subscriber(models.Model):
    forename = EncryptedCharField(max_length=100, null=False)
    surname = EncryptedCharField(max_length=100, null=False)
    imsi = EncryptedCharField(max_length=100, unique=True, null=False)
    terminal_type = models.ForeignKey(Terminal, on_delete=models.PROTECT)
    subscription_type = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    
    def clean(self):
        super().clean()
        
        # Validate names
        self.validate_name(self.forename, 'forename')
        self.validate_name(self.surname, 'surname')
        
        # Check if IMSI is 15 digits long
        imsi = self.imsi
        if not imsi.isdigit() or len(imsi) != 15:
            raise ValidationError({
                'imsi': gettext_lazy("IMSI must be exactly 15 digits long.")
            })
        mcc = imsi[:3]
        mnc = imsi[3:5]
        if mcc != '262' or mnc not in ['01', '02', '03', '04', '05', '06', '07', '08', '09']:
            raise ValidationError({
                'imsi': gettext_lazy("IMSI must be a German IMSI.")
            })

    def validate_name(self, name, field_name):
        # Ensure the name only contains valid characters
        if not name.isalpha():
            raise ValidationError({
                field_name: gettext_lazy("Names must only contain alphabetic characters.")
            })

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
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='sessions')
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField(validators=[
            MaxValueValidator(2500000),
            MinValueValidator(1)
        ])
    data_volume = models.PositiveIntegerField()
    call_seconds = models.PositiveIntegerField()
    paid = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.subscriber} | {self.service} | {self.timestamp}"

class Invoice(models.Model):
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    data_volume = models.PositiveIntegerField()
    call_minutes = models.PositiveIntegerField()
    charges = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.subscriber} | {self.timestamp}"
