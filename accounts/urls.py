from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterViewforCustomer, VerifyUserEmail, RegisterViewforSupplier, 
    RegisterViewforDelivery, LoginUserView, PasswordResetRequestView, 
    SetNewPasswordView, LogoutApiView, CustomerProfileAPIView, 
    SupplierProfileAPIView, DeliveryProfileAPIView, SuppliersList, 
    SupplierDetail, FollowSupplier, TrendingSuppliersAPIView, 
    AddressViewSet, SupplierDocumentViewSet, DeliveryDocumentViewSet, 
    ResendOtpView, CheckOTPValidity,
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'supplier-documents', SupplierDocumentViewSet, basename='supplier-documents')
router.register(r'delivery-documents', DeliveryDocumentViewSet, basename='delivery-documents')

urlpatterns = [
    path('register/customer/', RegisterViewforCustomer.as_view(), name='register_customer'),
    path('register/supplier/', RegisterViewforSupplier.as_view(), name='register_supplier'),
    path('register/delivery/', RegisterViewforDelivery.as_view(), name='register_delivery'),
    path('auth/verify-email/', VerifyUserEmail.as_view(), name='verify_email'),
    path('auth/resend-otp/', ResendOtpView.as_view(), name='resend_otp'),
    path('auth/login/', LoginUserView.as_view(), name='login'),
    path('auth/token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/check-otp/', CheckOTPValidity.as_view(), name='check_otp'),
    path('auth/set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('auth/logout/', LogoutApiView.as_view(), name='logout'),
    path('profile/customer/', CustomerProfileAPIView.as_view(), name='customer-profile'),
    path('profile/supplier/', SupplierProfileAPIView.as_view(), name='supplier-profile'),
    path('profile/delivery/', DeliveryProfileAPIView.as_view(), name='delivery-profile'),
    path('suppliers/', SuppliersList.as_view(), name='suppliers-list'),
    path('suppliers/<uuid:pk>/', SupplierDetail.as_view(), name='supplier-detail'),
    path('suppliers/<uuid:supplier_id>/follow/', FollowSupplier.as_view(), name='follow-supplier'),
    path('suppliers/trending/', TrendingSuppliersAPIView.as_view(), name='trending-suppliers'),
    path('', include(router.urls)),
]