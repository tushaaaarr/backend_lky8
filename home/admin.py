from django.contrib import admin
from .models import *

admin.site.register(UserInfo)
admin.site.register(Order)
admin.site.register(CryptoPayment)
admin.site.register(Package)
