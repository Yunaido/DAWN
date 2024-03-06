from django.contrib import admin

from .models import Service, Subscriber, Subscription, Technology, Terminal, ThroughputPercentage

# Register your models here.

admin.site.register(ThroughputPercentage)
admin.site.register(Technology)
admin.site.register(Terminal)
admin.site.register(Subscription)
admin.site.register(Subscriber)
admin.site.register(Service)
