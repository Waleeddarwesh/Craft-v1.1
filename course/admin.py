from django.contrib import admin
from .models import Course, CourseVideo, Enrollment

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'rating', 'is_completed', 'from_date', 'to_date', 'price', 'supplier')
    search_fields = ('title', 'category__title', 'supplier__user__first_name', 'supplier__user__last_name')
    list_filter = ('category', 'rating', 'is_completed', 'from_date', 'to_date')
    ordering = ('-rating',)

class CourseVideosAdmin(admin.ModelAdmin):
    list_display = ('lecture_title', 'course', 'video_number')
    search_fields = ('lecture_title', 'course__title')
    list_filter = ('course',)
    ordering = ('course', 'video_number')

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'enrolled_user', 'enrollment_date')
    search_fields = ('course__title', 'enrolled_user__first_name', 'enrolled_user__last_name')
    list_filter = ('course', 'enrollment_date')
    ordering = ('-enrollment_date',)

admin.site.register(Course, CourseAdmin)
admin.site.register(CourseVideo, CourseVideosAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)