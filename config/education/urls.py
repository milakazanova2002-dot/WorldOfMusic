from django.urls import path

from .views import (
    AssignmentListView,
    LessonListView,
    LessonCreateView,
    PerformanceDeleteView,
    PerformanceDetailView,
    PerformanceListView,
    PerformanceCreateView,
    PerformanceMaterialUpdateView,
    PerformanceUpdateView,
)

urlpatterns = [
    path("assignments/", AssignmentListView.as_view(), name="assignment_list"),
    path("lessons/", LessonListView.as_view(), name="lesson_list"),
    path("lessons/create/<int:assignment_id>/", LessonCreateView.as_view(), name="lesson_create"),

    path("performances/", PerformanceListView.as_view(), name="performance_list"),
    path("performances/<int:pk>/", PerformanceDetailView.as_view(), name="performance_detail"),
    path("performances/create/<int:assignment_id>/", PerformanceCreateView.as_view(), name="performance_create"),
    path("performances/<int:pk>/materials/", PerformanceMaterialUpdateView.as_view(), name="performance_materials"),
    path("performances/<int:pk>/edit/", PerformanceUpdateView.as_view(), name="performance_edit"),
    path("performances/<int:pk>/delete/", PerformanceDeleteView.as_view(), name="performance_delete"),
]
