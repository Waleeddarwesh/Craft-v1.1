# accounts/views.py
from django.shortcuts import get_object_or_404
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404, FileResponse
from django.utils.timezone import now, timedelta
from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType
from . import permissions
from .models import User, Supplier, Customer, Delivery, Follow, Address, OneTimePassword
from .serializers import (
    CustomerRegistrationSerializer, SupplierRegistrationSerializer, DeliveryRegistrationSerializer,
    LoginSerializer, SetNewPasswordSerializer, LogoutUserSerializer, AddressSerializer,
    CustomerProfileSerializer, DeliveryProfileSerializer, SupplierProfileSerializer,
    SupplierProfileSummarySerializer, SupplierDocumentSerializer, DeliveryDocumentSerializer,
    EmailVerificationSerializer
)
from .utils import generate_otp_and_send_email, get_tokens_for_user, get_follower_content_type
from rest_framework import serializers

class CheckOTPValiditySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    email = serializers.EmailField()

class ResendOtpView(GenericAPIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        if not User.objects.filter(email=email).exists():
            return Response({'message': 'Email not found.'}, status=status.HTTP_404_NOT_FOUND)

        generate_otp_and_send_email(email)
        return Response({'message': 'OTP sent to your email.'}, status=status.HTTP_200_OK)

class RegisterUserView(GenericAPIView):
    """
    A generic view for user registration.
    """
    def post(self, request, serializer_class, user_type):
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            user_data = serializer.save()
            generate_otp_and_send_email(user_data.email)
            return Response({
                'email': user_data.email,
                'message': 'Thanks for signing up! A passcode has been sent to verify your email.'
            }, status=status.HTTP_201_CREATED)
        
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class RegisterViewforCustomer(RegisterUserView):
    serializer_class = CustomerRegistrationSerializer

    def post(self, request):
        return super().post(request, self.serializer_class, 'customer')

class RegisterViewforSupplier(RegisterUserView):
    serializer_class = SupplierRegistrationSerializer

    def post(self, request):
        return super().post(request, self.serializer_class, 'supplier')

class RegisterViewforDelivery(RegisterUserView):
    serializer_class = DeliveryRegistrationSerializer

    def post(self, request):
        return super().post(request, self.serializer_class, 'delivery')

class VerifyUserEmail(GenericAPIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        otp = request.data.get('otp')
        email = request.data.get('email')

        if not otp or not email:
            return Response({'message': 'Both email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_record = OneTimePassword.objects.get(otp=otp, user__email=email)
        except OneTimePassword.DoesNotExist:
            return Response({'message': 'Invalid OTP or email provided.'}, status=status.HTTP_400_BAD_REQUEST)

        user = otp_record.user
        if user.is_verified:
            return Response({'message': 'User is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_verified = True
        user.save()
        otp_record.delete()
        
        return Response({'message': 'Account email verified successfully.'}, status=status.HTTP_200_OK)

class LoginUserView(GenericAPIView):
    serializer_class = LoginSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class CustomerProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            customer = request.user.customer_profile
            serializer = CustomerProfileSerializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response({'message': 'Customer profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        try:
            customer = request.user.customer_profile
        except Customer.DoesNotExist:
            return Response({'message': 'Customer profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = CustomerProfileSerializer(customer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class SupplierProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            supplier = request.user.supplier_profile
            serializer = SupplierProfileSerializer(supplier)
            return Response(serializer.data)
        except Supplier.DoesNotExist:
            return Response({'message': 'Supplier profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        try:
            supplier = request.user.supplier_profile
        except Supplier.DoesNotExist:
            return Response({'message': 'Supplier profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SupplierProfileSerializer(supplier, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class DeliveryProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            delivery = request.user.delivery_profile
            serializer = DeliveryProfileSerializer(delivery)
            return Response(serializer.data)
        except Delivery.DoesNotExist:
            return Response({'message': 'Delivery profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        try:
            delivery = request.user.delivery_profile
        except Delivery.DoesNotExist:
            return Response({'message': 'Delivery profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DeliveryProfileSerializer(delivery, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SuppliersList(ListAPIView):
    serializer_class = SupplierProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category_title', 'rating', 'experience_years']
    search_fields = ['user__first_name', 'user__last_name']
    ordering_fields = ['user__first_name', 'rating']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Supplier.objects.none()
        return Supplier.objects.filter(user__is_verified=True, user__is_active=True).exclude(user=user).order_by('id')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        serializer = self.get_serializer(page, many=True)
        transformed_data = []

        for supplier_data in serializer.data:
            supplier_id = supplier_data.get('id')
            follower_content_type, follower_object_id = get_follower_content_type(request.user)
            is_followed = False
            if follower_content_type and follower_object_id:
                is_followed = Follow.objects.filter(
                    follower_content_type=follower_content_type,
                    follower_object_id=follower_object_id,
                    supplier__id=supplier_id
                ).exists()

            transformed_data.append({
                "id": supplier_id,
                'full_name': supplier_data['user'].get('full_name', ''),
                'photo': supplier_data.get('photo', ''),
                'category_title': supplier_data.get('category_title', ''),
                'followed_by_user': is_followed,
            })
        
        return self.get_paginated_response(transformed_data)

class TrendingSuppliersAPIView(ListAPIView):
    permission_classes = [permissions.IsCustomerOrSupplier]
    serializer_class = SupplierProfileSummarySerializer

    def get_queryset(self):
        return Supplier.objects.filter(user__is_verified=True, user__is_active=True).order_by('-rating', '-orders_count')[:10]

class SupplierDetail(RetrieveAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierProfileSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, **kwargs):
        pk = self.kwargs.get('pk')
        obj = get_object_or_404(Supplier, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        supplier = self.get_object()
        serializer = self.get_serializer(supplier)
        data = serializer.data
        if not request.user.is_authenticated:
            data['followed_by_user'] = False
            return Response(data)

        follower_content_type, follower_object_id = get_follower_content_type(request.user)
        is_followed = False
        if follower_content_type and follower_object_id:
            is_followed = Follow.objects.filter(
                follower_content_type=follower_content_type,
                follower_object_id=follower_object_id,
                supplier=supplier
            ).exists()

        data['followed_by_user'] = is_followed
        return Response(data)

class FollowSupplier(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, supplier_id):
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            follower_content_type, follower_object_id = get_follower_content_type(request.user)
            
            if not follower_content_type or not follower_object_id:
                return Response({'message': 'User must be a customer or supplier.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if Follow.objects.filter(
                follower_content_type=follower_content_type,
                follower_object_id=follower_object_id,
                supplier=supplier
            ).exists():
                return Response({'message': 'You are already following this supplier.'}, status=status.HTTP_400_BAD_REQUEST)

            Follow.objects.create(
                follower_content_type=follower_content_type,
                follower_object_id=follower_object_id,
                supplier=supplier
            )
            return Response({'message': 'Followed.'}, status=status.HTTP_201_CREATED)

        except Supplier.DoesNotExist:
            return Response({'message': 'Supplier not found.'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, supplier_id):
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            follower_content_type, follower_object_id = get_follower_content_type(request.user)
            
            if not follower_content_type or not follower_object_id:
                return Response({'message': 'User must be a customer or supplier.'}, status=status.HTTP_400_BAD_REQUEST)

            follow_instance = Follow.objects.get(
                follower_content_type=follower_content_type,
                follower_object_id=follower_object_id,
                supplier=supplier
            )
            follow_instance.delete()
            return Response({'message': 'Unfollowed.'}, status=status.HTTP_200_OK)

        except Supplier.DoesNotExist:
            return Response({'message': 'Supplier not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Follow.DoesNotExist:
            return Response({'message': 'You are not following this supplier.'}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(GenericAPIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            if user.last_password_reset_request and (now() - user.last_password_reset_request) < timedelta(minutes=1):
                return Response({'message': 'Please wait 1 minute before attempting another password reset.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except User.DoesNotExist:
            return Response({'message': 'User with that email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        generate_otp_and_send_email(email, is_verification=False)
        user.last_password_reset_request = now()
        user.save()
        return Response({'message': 'OTP sent to your email for password reset.'}, status=status.HTTP_200_OK)

class CheckOTPValidity(GenericAPIView):
    serializer_class = CheckOTPValiditySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']
        email = serializer.validated_data['email']

        if OneTimePassword.objects.filter(otp=otp, user__email=email).exists():
            return Response({'message': 'OTP is valid.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid OTP or email provided.'}, status=status.HTTP_400_BAD_REQUEST)

class SetNewPasswordView(GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            otp_record = OneTimePassword.objects.get(otp=data['otp'])
            user = otp_record.user
            user.set_password(data['new_password'])
            user.save()
            otp_record.delete()
            return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)
        except OneTimePassword.DoesNotExist:
            return Response({'message': 'Invalid OTP or OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutApiView(GenericAPIView):
    serializer_class = LogoutUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Logged Out'}, status=status.HTTP_204_NO_CONTENT)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SupplierDocumentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        file_path = 'contract/contract_temp.pdf'
        try:
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='contract_template.pdf')
        except FileNotFoundError:
            return Response({'message': 'Contract template not found.'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        try:
            supplier = request.user.supplier_profile
        except Supplier.DoesNotExist:
            return Response({'message': 'Supplier profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SupplierDocumentSerializer(supplier, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class DeliveryDocumentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        file_path = 'contract/contract_temp.pdf'
        try:
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='contract_template.pdf')
        except FileNotFoundError:
            return Response({'message': 'Contract template not found.'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        try:
            delivery = request.user.delivery_profile
        except Delivery.DoesNotExist:
            return Response({'message': 'Delivery profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DeliveryDocumentSerializer(delivery, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)