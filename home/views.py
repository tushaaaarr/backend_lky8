from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import UserInfoSerializer, OrderSerializer, PackageSerializer
from django.db import transaction
import os
import requests
from dotenv import load_dotenv
from django.contrib.auth import get_user_model

load_dotenv()  # Load .env variables

NOWPAYMENTS_APIKEY = os.getenv('NOWPAYMENTS_APIKEY')
NOWPAYMENTS_API_BASE = "https://api.nowpayments.io/v1"
NOWPAYMENTS_SECRET_KEY = os.getenv("NOWPAYMENTS_SECRET_KEY")

import json
import logging
import hmac
import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import time


# Function to convert fiat to cryptocurrency with retry mechanism
def fiat_crypto_nowpayments(amount, currency_from, currency_to, retries=3, delay=2):
    url = "https://api.nowpayments.io/v1/estimate"
    headers = {"x-api-key": NOWPAYMENTS_APIKEY}
    params = {"amount": amount, "currency_from": currency_from, "currency_to": currency_to}
    
    for attempt in range(retries):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("estimated_amount")
        elif response.status_code == 429:  # Too many requests
            time.sleep(delay * (2 ** attempt))  # Exponential backoff
        else:
            raise Exception(f"Error in conversion: {response.status_code} - {response.text}")
    
    raise Exception("Exceeded maximum retries for conversion.")


@api_view(["GET"])
def get_packages(request):
    packages = Package.objects.all()
    serialized_packages = []

    for package in packages:
        try:
            # Fetch real-time crypto amount
            updated_crypto_amount = fiat_crypto_nowpayments(package.fiat_amount, package.fiat_currency, package.crypto_currency)
            package.crypto_amount = updated_crypto_amount  # Update dynamically
            
            # Generate a dynamic message
            message = f"Get {package.entries} entries for just {updated_crypto_amount} {package.crypto_currency}!"
        except Exception as e:
            # Use the stored crypto amount if API fails
            updated_crypto_amount = package.crypto_amount
            message = f"Get {package.entries} entries for just {package.crypto_amount} {package.crypto_currency}!"
        
        # Serialize package data
        package_data = PackageSerializer(package).data
        package_data["crypto_amount"] = updated_crypto_amount  # Ensure crypto amount is updated
        package_data["message"] = message  # Include dynamic message

        serialized_packages.append(package_data)

    return Response(serialized_packages)


@csrf_exempt  # ✅ Disable CSRF protection
@api_view(['POST'])  
def get_order_details(request):
    order_id = request.data.get("order_id")  # ✅ Fetch order_id from request body
    if not order_id:
        return Response({"error": "Order ID is required"}, status=400)

    order = get_object_or_404(Order, order_id=order_id)
    order_serializer = OrderSerializer(order)
    return Response({
        "order": order_serializer.data
    })


def create_nowpayments_crypto_payment(fiat_amount, fiat_currency, crypto_currency, booking_id):
    url = f"{NOWPAYMENTS_API_BASE}/invoice"
    headers = {
        "x-api-key": NOWPAYMENTS_APIKEY,
        "Content-Type": "application/json",
    }
    payload = {
        "price_amount": float(fiat_amount),  # Convert fiat amount to float
        "price_currency": fiat_currency,  # Fiat currency (USD, EUR, etc.)
        "pay_currency": crypto_currency,  # Crypto currency (BTC, ETH, USDT, etc.)
        "ipn_callback_url": "https://api.lky8.win/lky8/webhook/check-payment-status/",
        "success_url": f"https://lky8.win/payment/success/{booking_id}",
        "cancel_url": f"https://lky8.win/payment/failure/",
        "order_id": booking_id,
        "order_description": f"Payment for booking {booking_id}",
        "is_fixed_rate": True  # Ensures exact crypto amount is required
    }

    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    print(response_data)

    if response.status_code != 200 or "invoice_url" not in response_data:
        print(f"NowPayments API Error: {response_data}")  # Debugging
        return None  # Return None to indicate failure
    
    return response_data


# @api_view(['POST'])
# def userinfo_with_orders(request):
#     with transaction.atomic():
#         user_data = request.data.get("user_info", {})
#         user_email = user_data.get("email")

#         if not user_email:
#             return Response({
#                 "status_code": status.HTTP_400_BAD_REQUEST,
#                 "message": "Email is required to process the order.",
#                 "data": {}
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # ✅ Use UserInfo instead of User
#         user, created = UserInfo.objects.get_or_create(email=user_email, defaults=user_data)

#         if not created:
#             # If user exists, update details
#             user_serializer = UserInfoSerializer(user, data=user_data, partial=True)
#             if not user_serializer.is_valid():
#                 return Response({
#                     "status_code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Oops! There was an issue updating your personal details. Please check and try again.",
#                     "data": user_serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
#             user = user_serializer.save()
#         else:
#             # If user is newly created, validate with serializer
#             user_serializer = UserInfoSerializer(user)

#         # ✅ Assign `user.id` from `UserInfo` to the order
#         order_data = request.data.get("order", {})
#         order_data["user"] = user.id
#         print(order_data)
#         order_serializer = OrderSerializer(data=order_data)

#         if not order_serializer.is_valid():
#             return Response({
#                 "status_code": status.HTTP_400_BAD_REQUEST,
#                 "message": "Hmm... Something went wrong with your order details. Please verify and submit again.",
#                 "data": order_serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)

#         order = order_serializer.save()

#         # ✅ Get fiat price and currency from the order
#         fiat_amount = order.fiat_amount  
#         fiat_currency = order.fiat_currency  
#         crypto_currency = order.crypto_currency  

#         # ✅ Continue with payment processing
#         payment_response = create_nowpayments_crypto_payment(
#             fiat_amount=fiat_amount,
#             fiat_currency=fiat_currency,
#             crypto_currency=crypto_currency,
#             booking_id=str(order.id),
#         )

#         if not payment_response:
#             return Response({
#                 "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 "message": "We couldn't process your payment at the moment. Please try again later.",
#                 "data": {}
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # ✅ Extract payment details from NowPayments API response
#         initiated_crypto_amount = payment_response.get("pay_amount")  # Crypto amount user needs to pay
#         price_amount = payment_response.get("price_amount")  # Fiat amount
#         price_currency = payment_response.get("price_currency")  # Fiat currency
#         payment_id = payment_response.get("id")  # Unique payment ID from NowPayments
#         invoice_url = payment_response.get("invoice_url")

#         # ✅ Save the payment details
#         payment = CryptoPayment.objects.create(
#             order_id=order,
#             currency=crypto_currency,
#             initiated_crypto_amount=initiated_crypto_amount,
#             price_amount=price_amount,
#             price_currency=price_currency,
#             invoice_url=invoice_url,
#             success_url=payment_response.get("success_url"),
#             cancel_url=payment_response.get("cancel_url"),
#             status="pending",
#             payment_id=payment_id
#         )

#         return Response({
#             "status_code": status.HTTP_201_CREATED,
#             "message": "✅ Your order has been initiated! You are being redirected to the payment window. Once your payment is completed, your order will be placed successfully.",
#             "data": {
#                 "user_info": user_serializer.data,
#                 "order": order_serializer.data,
#                 "payment_url": str(payment.invoice_url)
#             }
#         }, status=status.HTTP_201_CREATED)



def create_order(user_id, order_data):
    """
    Creates an order, dynamically converting the fiat amount into the selected crypto currency.
    """
    try:
        package_id = order_data.get("package")
        crypto_currency = order_data.get("crypto_currency")  # User-selected crypto currency

        # Ensure package ID is provided
        if not package_id:
            return None, {"package": "A valid package ID must be provided."}

        package = Package.objects.filter(id=package_id).first()
        if not package:
            return None, {"package": "Selected package does not exist."}

        # ✅ Convert fiat to selected cryptocurrency dynamically
        try:
            converted_crypto_amount = fiat_crypto_nowpayments(
                amount=package.fiat_amount, 
                currency_from=package.fiat_currency, 
                currency_to=crypto_currency
            )
        except Exception as e:
            return None, {"crypto_conversion": f"Failed to convert fiat to {crypto_currency}. Error: {str(e)}"}

        # ✅ Create the Order
        order = Order.objects.create(
            user_id=user_id,
            package=package,
            entries=package.entries,
            fiat_amount=package.fiat_amount,
            fiat_currency=package.fiat_currency,
            crypto_amount=converted_crypto_amount,  # Live converted value
            crypto_currency=crypto_currency  # User-selected crypto
        )

        return order, None

    except Exception as e:
        return None, {"error": str(e)}


@csrf_exempt  # ✅ Disable CSRF protection
@api_view(['POST'])
def userinfo_with_orders(request):
    with transaction.atomic():
        user_data = request.data.get("user_info", {})
        user_email = user_data.get("email")

        if not user_email:
            return Response({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Email is required to process the order.",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Fetch or create user
        user, created = UserInfo.objects.get_or_create(email=user_email, defaults=user_data)

        if not created:
            # Update existing user details
            user_serializer = UserInfoSerializer(user, data=user_data, partial=True)
            if not user_serializer.is_valid():
                return Response({
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Oops! There was an issue updating your personal details.",
                    "data": user_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            user = user_serializer.save()
        else:
            user_serializer = UserInfoSerializer(user)

        # ✅ Create the order (Extract price details from Package)
        order_data = request.data.get("order", {})
        order, order_errors = create_order(user.id, order_data)
        order.status = "pending"
        order.save()
        if not order:
            return Response({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Hmm... Something went wrong with your order details.",
                "data": order_errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Process payment with extracted prices from the package
        payment_response = create_nowpayments_crypto_payment(
            fiat_amount=order.fiat_amount,    # Fetched from Package
            fiat_currency=order.fiat_currency, 
            crypto_currency=order.crypto_currency,
            booking_id=str(order.order_id),
        )
        if not payment_response:
            return Response({
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "We couldn't process your payment at the moment.",
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ✅ Save payment details
        payment = CryptoPayment.objects.create(
            order_id=order,
            currency=order.crypto_currency,
            initiated_crypto_amount=order.crypto_amount,
            price_amount=payment_response.get("price_amount"),
            price_currency=payment_response.get("price_currency"),
            invoice_url=payment_response.get("invoice_url"),
            success_url=payment_response.get("success_url"),
            cancel_url=payment_response.get("cancel_url"),
            status="pending",
            payment_id=payment_response.get("id")
        )

        return Response({
            "status_code": status.HTTP_201_CREATED,
            "message": "Your order has been initiated! Redirecting to the payment window...",
            "data": {
                "user_info": user_serializer.data,
                "order_id": order.order_id,
                "payment_url": str(payment.invoice_url)
            }
        }, status=status.HTTP_201_CREATED)













logger = logging.getLogger(__name__)


@csrf_exempt
def payment_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    try:
        payload = json.loads(request.body)
        logger.debug(f"Webhook received: {payload}")

        # Validate the X-NOWPayments-Sig header
        x_signature = request.headers.get("X-NowPayments-Sig")
        if not x_signature:
            logger.debug("Missing signature")
            return JsonResponse({"error": "Missing signature"}, status=400)
        
        # Validate signature
        sorted_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        digest = hmac.new(
            NOWPAYMENTS_SECRET_KEY.encode(),
            sorted_payload.encode(),
            hashlib.sha512,
        ).hexdigest()

        if digest != x_signature:
            logger.debug("Invalid signature")
            return JsonResponse({"error": "Invalid signature"}, status=400)

        # Extract required fields
        order_id = payload.get("order_id")
        payment_status = payload.get("payment_status", "").lower()
        price_amount = payload.get("price_amount")
        price_currency = payload.get("price_currency")
        payin_address = payload.get("payin_address")
        payout_address = payload.get("payout_address")
        payin_tx_hash = payload.get("payin_hash")
        payout_tx_hash = payload.get("payout_hash")
        pay_currency = payload.get("pay_currency")
        pay_amount = payload.get("pay_amount")
        actually_paid = payload.get("actually_paid")
        
        logger.debug(f"Processing payment for order: {order_id}, status: {payment_status}")

        # Fetch Order and Payment Record
        order = Order.objects.filter(order_id=order_id).first()

        if not order:
            logger.debug(f"No order found for order_id: {order_id}")
            return JsonResponse({"error": "Order not found"}, status=404)

        payment = CryptoPayment.objects.filter(order_id=order).first()
        if not payment:
            logger.debug(f"No payment record found for order: {order_id}")
            return JsonResponse({"error": "Payment record not found"}, status=404)

        # Update CryptoPayment record
        payment.payment_id = payload.get("payment_id")
        payment.order_description = payload.get("order_description")
        payment.payin_address = payin_address
        payment.payout_address = payout_address
        payment.payin_tx_hash = payin_tx_hash
        payment.payout_tx_hash = payout_tx_hash
        payment.pay_currency = pay_currency
        payment.status = payment_status
        payment.price_amount = price_amount
        payment.price_currency = price_currency
        payment.paid_crypto_amount = actually_paid
        payment.save()

        # Handle Payment Statuses
        if payment_status == "finished":  # ✅ Successful Payment
            order.status = "completed"
            order.save()
            logger.debug(f"Payment {order_id} completed successfully.")

        elif payment_status in ["failed", "expired"]:  # ❌ Failed Payment
            logger.debug(f"Payment {order_id} failed or expired.")
        elif payment_status in ["waiting", "confirming"]:  # ⏳ Payment Pending
            logger.info(f"Payment {order_id} is still pending: {payment_status}")
        elif payment_status == "refunded":  # 🔄 Refunded Payment
            logger.info(f"Payment {order_id} has been refunded.")
        
        return JsonResponse({"success": True})

    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)



















