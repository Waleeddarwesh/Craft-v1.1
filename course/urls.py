from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    CourseVideoViewSet,
    SimpleCoursesListAPIView,
    CourseDetailAPIView,
    EnrolledCoursesListAPIView,
    EnrollmentCreateAPIView,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"videos", CourseVideoViewSet, basename="videos")

urlpatterns = [
    path("", include(router.urls)),
    path("courses/public/", SimpleCoursesListAPIView.as_view(), name="course-public-list"),
    path("courses/<uuid:id>/detail/", CourseDetailAPIView.as_view(), name="course-detail"),
    path("enrollments/", EnrolledCoursesListAPIView.as_view(), name="enrolled-courses"),
    path("enrollments/create/", EnrollmentCreateAPIView.as_view(), name="enrollment-create"),
]