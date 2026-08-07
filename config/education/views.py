from django.http import HttpResponseForbidden
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


from .forms import AssignmentForm, PerformanceCommentForm, PerformanceMaterialForm
from .models import Lesson, Performance, TeachingAssignment
from accounts.mixins import TeacherRequiredMixin, StudentRequiredMixin, teacher_required



class LessonListView(LoginRequiredMixin, ListView):
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

class LessonCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
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


class AssignmentListView(LoginRequiredMixin, ListView):
    model = TeachingAssignment
    template_name = "education/assignment_list.html"
    context_object_name = "assignments"

class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = TeachingAssignment
    template_name = "education/assignment_detail.html"
    context_object_name = "assignment"


class AssignmentCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
    model = TeachingAssignment
    form_class = AssignmentForm
    template_name = "education/assignment_form.html"

    def get_success_url(self):
        return reverse("assignment_detail", args=[self.object.pk])

class AssignmentDeleteView(LoginRequiredMixin, TeacherRequiredMixin, DeleteView):
    model = TeachingAssignment
    template_name = "education/assignment_confirm_delete.html"
    success_url = reverse_lazy("assignment_list")


class PerformanceListView(LoginRequiredMixin, ListView):
    model = Performance
    template_name = "education/performance_list.html"
    context_object_name = "performances"

    def get_queryset(self):
        user = self.request.user

        # Админ видит всё
        if user.is_superuser:
            return Performance.objects.all().order_by("-created_at")

        # Педагог
        if hasattr(user, "teacher_profile"):
            return Performance.objects.filter(
                assignment__teacher=user.teacher_profile
            ).order_by("-created_at")

        # Ученик
        if hasattr(user, "student_profile"):
            return Performance.objects.filter(
                assignment__student=user.student_profile
            ).order_by("-created_at")

        # Остальные — ничего
        return Performance.objects.none()


class PerformanceCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
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


class PerformanceMaterialUpdateView(LoginRequiredMixin, TeacherRequiredMixin, UpdateView):
    model = Performance
    form_class = PerformanceMaterialForm
    template_name = "education/performance_material_form.html"

    def get_success_url(self):
        return reverse_lazy("performance_detail", kwargs={"pk": self.object.id})


class PerformanceDetailView(LoginRequiredMixin, DetailView):
    model = Performance
    template_name = "education/performance_detail.html"
    context_object_name = "performance"


class PerformanceUpdateView(LoginRequiredMixin, TeacherRequiredMixin, UpdateView):
    model = Performance
    fields = ["piece", "video", "score"]
    template_name = "education/performance_form.html"

    def get_success_url(self):
        return reverse_lazy("performance_detail", kwargs={"pk": self.object.id})


class PerformanceDeleteView(LoginRequiredMixin, TeacherRequiredMixin, DeleteView):
    model = Performance
    template_name = "education/performance_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("performance_list")


@login_required
@teacher_required
def add_performance_comment(request, pk):
    performance = get_object_or_404(Performance, pk=pk)

    if request.method == "POST":
        form = PerformanceCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.performance = performance
            comment.author = request.user.teacher_profile
            comment.save()
            return redirect("performance_detail", pk=pk)
    else:
        form = PerformanceCommentForm()

    return render(
        request,
        "education/performance_comment_form.html",
        {"form": form, "performance": performance}
    )





