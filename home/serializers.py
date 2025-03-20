from rest_framework import serializers
from .models import *


# class OrderSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Order
#         fields = [
#             'user',  
#             'package',  # ✅ Ensure package is included
#             'entries',  # ✅ Use 'entries' instead of 'total_entries'
#             'crypto_currency', 
#             'crypto_amount', 
#             'fiat_currency',  
#             'fiat_amount'
#         ]

#     def validate(self, validated_data):
#         """
#         Ensure the pricing details match the selected package.
#         """
#         package = validated_data.get("package")
#         if not package:
#             raise serializers.ValidationError({"package": "A valid package must be selected."})

#         # Assign pricing and entries from the package
#         validated_data["crypto_amount"] = package.crypto_amount
#         validated_data["fiat_amount"] = package.fiat_amount
#         validated_data["crypto_currency"] = package.crypto_currency
#         validated_data["fiat_currency"] = package.fiat_currency
#         validated_data["entries"] = package.entries  # ✅ Use 'entries' instead of 'total_entries'

#         return validated_data

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'  # ✅ This includes all package fields

from rest_framework import serializers
from .models import Order, UserInfo, Package

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'


class UserInfoMinimalSerializer(serializers.ModelSerializer):
    """Avoids recursion by including only basic user details"""
    class Meta:
        model = UserInfo
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    package = PackageSerializer()  # ✅ Full package details
    user = UserInfoMinimalSerializer()  # ✅ Prevents recursion

    class Meta:
        model = Order
        fields = [
            'order_id',  
            'user',  
            'package',  
            'entries',  
            'crypto_currency', 
            'crypto_amount',  
            'fiat_currency',  
            'fiat_amount',  
            'status',  
            'date_and_time'  
        ]


class UserInfoSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)  # ✅ Fetch related orders

    class Meta:
        model = UserInfo
        fields = '__all__'



class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"