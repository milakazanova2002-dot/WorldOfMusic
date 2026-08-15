from django.urls import path

from .views import (
    AssignmentCreateView,
    AssignmentUpdateView,
    AssignmentDeleteView,
    AssignmentDetailView,
    AssignmentListView,
    LessonDeleteView,
    LessonDetailView,
    LessonListView,
    LessonCreateView,
    LessonMaterialCreateView,
    LessonUpdateView,
    PerformanceCommentCreateView,
    PerformanceDeleteView,
    PerformanceDetailView,
    PerformanceListView,
    PerformanceCreateView,
    PerformanceMaterialUpdateView,
    PerformanceUpdateView,
    StudentDashboardView,
    StudentDetailView,
    TeacherDashboardView,
    TeacherDetailView,
    TeacherPublicListView,
    TeacherPublicDetailView,
    add_performance_comment,
)

app_name = "education"

urlpatterns = [
    path("teachers/", TeacherPublicListView.as_view(), name="teacher_public_list"),
    path("teachers/<int:pk>/", TeacherPublicDetailView.as_view(), name="teacher_public_detail"),

    path("student/<int:pk>/", StudentDetailView.as_view(), name="student_detail"),

    path("teacher/<int:pk>/", TeacherDetailView.as_view(), name="teacher_detail"),

    path("assignments/", AssignmentListView.as_view(), name="assignment_list"),
    path("assignments/create/", AssignmentCreateView.as_view(), name="assignment_create"),
    path("assignments/<int:pk>/", AssignmentDetailView.as_view(), name="assignment_detail"),
    path("assignments/<int:pk>/edit/", AssignmentUpdateView.as_view(), name="assignment_edit"),
    path("assignments/<int:pk>/delete/", AssignmentDeleteView.as_view(), name="assignment_delete"),

    path("lessons/", LessonListView.as_view(), name="lesson_list"),
    path("lesson/<int:pk>/", LessonDetailView.as_view(), name="lesson_detail"),
    path("lesson/<int:pk>/edit/", LessonUpdateView.as_view(), name="lesson_update"),
    path("lesson/<int:pk>/delete/", LessonDeleteView.as_view(), name="lesson_delete"),
    path("lesson/<int:lesson_id>/material/add/",LessonMaterialCreateView.as_view(), name="lesson_material_add"),
    path("lessons/create/<int:assignment_id>/", LessonCreateView.as_view(), name="lesson_create"),

    path("performances/", PerformanceListView.as_view(), name="performance_list"),
    path("performances/<int:pk>/", PerformanceDetailView.as_view(), name="performance_detail"),
    path("performances/create/<int:assignment_id>/", PerformanceCreateView.as_view(), name="performance_create"),
    path("performances/<int:pk>/materials/", PerformanceMaterialUpdateView.as_view(), name="performance_materials"),
    path("performances/<int:pk>/edit/", PerformanceUpdateView.as_view(), name="performance_edit"),
    path("performances/<int:pk>/delete/", PerformanceDeleteView.as_view(), name="performance_delete"),
    path("performance/<int:pk>/comment/", add_performance_comment, name="performance_comment"),
    path("performance/<int:performance_id>/comment/add/", PerformanceCommentCreateView.as_view(), name="performance_comment_add"),

    path("dashboard/student/", StudentDashboardView.as_view(), name="student_dashboard"),
    path("dashboard/teacher/", TeacherDashboardView.as_view(), name="teacher_dashboard"),
]
