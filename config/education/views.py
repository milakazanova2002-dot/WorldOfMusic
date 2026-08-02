from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy


from .forms import PerformanceMaterialForm
from .models import Lesson, Performance, TeachingAssignment


class LessonListView(ListView):
    model = Lesson
    template_name = "education/lesson_list.html"
    context_object_name = "lessons"

    def get_queryset(self):
        user = self.request.user

        # Если педагог
        if hasattr(user, "teacher_profile"):
            return Lesson.objects.filter(
                assignment__teacher=user.teacher_profile
            ).order_by("-date")

        # Если ученик
        if hasattr(user, "student_profile"):
            return Lesson.objects.filter(
                assignment__student=user.student_profile
            ).order_by("-date")

        return Lesson.objects.none()

class LessonCreateView(CreateView):
    model = Lesson
    fields = ["date", "instrument", "piece", "homework", "comment"]
    template_name = "education/lesson_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.assignment = get_object_or_404(
            TeachingAssignment,
            id=kwargs["assignment_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.assignment = self.assignment
        form.instance.student = self.assignment.student
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("lesson_list")


class AssignmentListView(ListView):
    model = TeachingAssignment
    template_name = "education/assignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self):
        user = self.request.user

        # Если педагог
        if hasattr(user, "teacher_profile"):
            return TeachingAssignment.objects.filter(
                teacher=user.teacher_profile,
                is_active=True
            )

        # Если ученик
        if hasattr(user, "student_profile"):
            return TeachingAssignment.objects.filter(
                student=user.student_profile,
                is_active=True
            )

        return TeachingAssignment.objects.none()


class PerformanceListView(ListView):
    model = Performance
    template_name = "education/performance_list.html"
    context_object_name = "performances"

    def get_queryset(self):
        user = self.request.user

        # Если педагог
        if hasattr(user, "teacher_profile"):
            return Performance.objects.filter(
                assignment__teacher=user.teacher_profile
            ).order_by("-created_at")

        # Если ученик
        if hasattr(user, "student_profile"):
            return Performance.objects.filter(
                assignment__student=user.student_profile
            ).order_by("-created_at")

        return Performance.objects.none()

class PerformanceCreateView(CreateView):
    model = Performance
    fields = ["piece", "video", "score"]
    template_name = "education/performance_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.assignment = get_object_or_404(
            TeachingAssignment,
            id=kwargs["assignment_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.assignment = self.assignment
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("performance_list")


class PerformanceMaterialUpdateView(UpdateView):
    model = Performance
    form_class = PerformanceMaterialForm
    template_name = "education/performance_material_form.html"

    def get_success_url(self):
        return reverse_lazy("performance_detail", kwargs={"pk": self.object.id})


class PerformanceDetailView(DetailView):
    model = Performance
    template_name = "education/performance_detail.html"
    context_object_name = "performance"


class PerformanceUpdateView(UpdateView):
    model = Performance
    fields = ["piece", "video", "score"]
    template_name = "education/performance_form.html"

    def get_success_url(self):
        return reverse_lazy("performance_detail", kwargs={"pk": self.object.id})


class PerformanceDeleteView(DeleteView):
    model = Performance
    template_name = "education/performance_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("performance_list")


