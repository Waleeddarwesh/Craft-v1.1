from django.db import transaction
from django.db.models import Q, F, Max
from rest_framework import generics, permissions, serializers, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound, MethodNotAllowed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Course, CourseVideo, Enrollment, Supplier
from .serializers import (
    CourseSerializer,
    CourseVideoSerializer,
    SimpleCoursesSerializer,
    OwnCourseSerializer,
    EnrollmentSerializer,
)
from .permissions import IsSupplier, IsCustomer
import uuid

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class CoursePermissionMixin:
    def _ensure_course_owner(self, course):
        if course.supplier.user.id != self.request.user.id:
            raise PermissionDenied("You are not allowed to modify this course.")

    def _ensure_video_owner(self, video):
        if video.course.supplier.user.id != self.request.user.id:
            raise PermissionDenied("You are not allowed to perform this action on this video.")

class CourseViewSet(viewsets.ModelViewSet, CoursePermissionMixin):
    queryset = Course.objects.all().select_related('supplier__user').prefetch_related('category')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsSupplier]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description"]

    def get_serializer_class(self):
        if self.action == 'list_own_courses':
            return OwnCourseSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        supplier = self.request.user.supplier_profile
        course_title = (serializer.validated_data.get("title") or "").strip()

        if Course.objects.filter(supplier=supplier, title__iexact=course_title).exists():
            raise serializers.ValidationError({"title": "You already have a course with this name."})
        
        serializer.save(supplier=supplier)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Course created successfully"}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._ensure_course_owner(instance)
        return super().partial_update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self._ensure_course_owner(instance)
        instance.delete()

    @action(detail=False, methods=["get"], url_path="my-courses")
    def list_own_courses(self, request):
        supplier = request.user.supplier_profile
        queryset = self.get_queryset().filter(supplier=supplier).order_by("-id")

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class CourseVideoViewSet(viewsets.ModelViewSet, CoursePermissionMixin):
    serializer_class = CourseVideoSerializer
    permission_classes = [IsAuthenticated, IsSupplier]
    queryset = CourseVideo.objects.select_related("course__supplier__user")
    filter_backends = [filters.SearchFilter]
    search_fields = ["lecture_title", "description"]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        course_id = self.request.query_params.get("course_id")
        if course_id:
            try:
                # Use the UUID field for filtering
                uuid.UUID(course_id)
                queryset = queryset.filter(course__id=course_id)
            except ValueError:
                raise NotFound("Invalid course ID format.")
        return queryset

    def perform_create(self, serializer):
        course = serializer.validated_data.get("course")
        if course.supplier.user.id != self.request.user.id:
            raise PermissionDenied("You are not allowed to create videos for this course.")

        max_video_no = CourseVideo.objects.filter(course=course).aggregate(Max('video_number'))['video_number__max']
        new_video_no = (max_video_no or 0) + 1
        
        with transaction.atomic():
            serializer.save(video_number=new_video_no)
            Course.objects.filter(pk=course.pk).update(number_of_uploaded_lectures=F("number_of_uploaded_lectures") + 1)
        
    def perform_update(self, serializer):
        self._ensure_video_owner(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_video_owner(instance)
        course_id = instance.course.id
        with transaction.atomic():
            instance.delete()
            Course.objects.filter(pk=course_id).update(number_of_uploaded_lectures=F("number_of_uploaded_lectures") - 1)

class SimpleCoursesListAPIView(generics.ListAPIView):
    serializer_class = SimpleCoursesSerializer
    filter_backends = [filters.SearchFilter]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    search_fields = [
        "title",
        "description",
        "supplier__user__first_name",
        "supplier__user__last_name",
    ]

    def get_queryset(self):
        queryset = Course.objects.all().select_related('supplier__user')
        if hasattr(self.request.user, "supplier_profile"):
            queryset = queryset.exclude(supplier=self.request.user.supplier_profile)
        return queryset

class CourseDetailAPIView(generics.RetrieveAPIView):
    queryset = Course.objects.all().select_related('supplier__user').prefetch_related('videos')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        course = self.get_object()

        is_enrolled = Enrollment.objects.filter(course=course, enrolled_user=request.user).exists()
        is_owner = hasattr(request.user, "supplier_profile") and (course.supplier.id == request.user.supplier_profile.id)

        if not (is_enrolled or is_owner):
            raise PermissionDenied("You are not allowed to access this course.")

        serializer = self.get_serializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EnrolledCoursesListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Course.objects.filter(enrollments__enrolled_user=self.request.user).select_related("supplier")

class EnrollmentCreateAPIView(generics.CreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsCustomer]