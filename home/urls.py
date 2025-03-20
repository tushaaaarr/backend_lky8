from django.urls import path
from .views import userinfo_with_orders, user_orders
from . import views

urlpatterns = [
    path("packages/", views.get_packages, name="get_packages"),
    path('create-order/', userinfo_with_orders, name='userinfo_with_orders'),
    path('orders/<str:id>/', user_orders, name='user_orders'), 
]
