from django.urls import path
from .views import userinfo_with_orders
from . import views

urlpatterns = [
    path("packages/", views.get_packages, name="get_packages"),
    path('create-order/', userinfo_with_orders, name='userinfo_with_orders'),
    path('orders/<str:order_id>/', views.get_order_details, name='get_order_details'), 


    path('lky8/webhook/check-payment-status/', views.payment_webhook, name='payment_webhook'),
]
