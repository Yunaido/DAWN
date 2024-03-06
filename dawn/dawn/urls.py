"""
URL configuration for dawn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from matsecom.views import HomeTemplateView, AddSubscriberView, SubscriberListView, SessionView, CreateInvoiceView, InvoiceView, SimulateSessionView


urlpatterns = [
    path('', HomeTemplateView.as_view(), name='home'),
    path("admin/", admin.site.urls),
    path('session/', SessionView.as_view(), name='simulate_session'),
    path("invoice/", CreateInvoiceView.as_view(), name='create_invoice'),
    path('invoice/result/', InvoiceView.as_view(), name='get_invoice'),
    path('subscribers/', SubscriberListView.as_view(), name='subscriber_list'),
    path('subscribers/add/', AddSubscriberView.as_view(), name='add_subscriber'),
    path('invoice/', CreateInvoiceView.as_view(), name='invoice'),
    path('simulate_session/', SimulateSessionView.as_view(), name='session_simulation'),
]
