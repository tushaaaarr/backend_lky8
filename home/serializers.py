from rest_framework import serializers
from .models import *


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'user',  
            'package',  # ✅ Ensure package is included
            'entries',  # ✅ Use 'entries' instead of 'total_entries'
            'crypto_currency', 
            'crypto_amount', 
            'fiat_currency',  
            'fiat_amount'
        ]

    def validate(self, validated_data):
        """
        Ensure the pricing details match the selected package.
        """
        package = validated_data.get("package")
        if not package:
            raise serializers.ValidationError({"package": "A valid package must be selected."})

        # Assign pricing and entries from the package
        validated_data["crypto_amount"] = package.crypto_amount
        validated_data["fiat_amount"] = package.fiat_amount
        validated_data["crypto_currency"] = package.crypto_currency
        validated_data["fiat_currency"] = package.fiat_currency
        validated_data["entries"] = package.entries  # ✅ Use 'entries' instead of 'total_entries'

        return validated_data


class UserInfoSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)  # Fetch related orders

    class Meta:
        model = UserInfo
        fields = '__all__'



class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"