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
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from matsecom.views import HomeTemplateView, SubscriberListView, SubscriberDetailView, AddSubscriberView, SubscriberDeleteView, CreateInvoiceView, InvoiceDetailView, SessionListView, SimulateSessionView

urlpatterns = [
    path('', HomeTemplateView.as_view(), name='home'),
    path('login/', LoginView.as_view(next_page='/'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path("admin/", admin.site.urls),
    path('subscribers/', SubscriberListView.as_view(), name='subscriber_list'),
    path('subscribers/<int:pk>/', SubscriberDetailView.as_view(), name='subscriber_detail'),
    path('subscribers/add/', AddSubscriberView.as_view(), name='add_subscriber'),
    path('subscribers/delete/<int:pk>/', SubscriberDeleteView.as_view(), name='subscriber_delete'),
    path('invoice/', CreateInvoiceView.as_view(), name='invoice'),
    path('invoice/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_details'),
    path('sessions/', SessionListView.as_view(), name='session_list'),
    path('sessions/simulate', SimulateSessionView.as_view(), name='session_simulation'),
]
