from django.http import HttpResponseForbidden
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


from .forms import AssignmentForm, LessonMaterialForm, PerformanceCommentForm, PerformanceMaterialForm
from .models import Lesson, LessonMaterial, Performance, PerformanceComment, StudentProfile, TeacherProfile, TeachingAssignment
from accounts.mixins import TeacherRequiredMixin, StudentRequiredMixin, teacher_required



class TeacherPublicListView(ListView):
    """Публичный список педагогов — доступен без авторизации."""
    model = TeacherProfile
    template_name = "education/teacher_public_list.html"
    context_object_name = "teachers"

    def get_queryset(self):
        return TeacherProfile.objects.filter(user__is_approved=True).select_related("user")


class TeacherPublicDetailView(DetailView):
    """Публичная страница педагога — только общедоступные данные, без списка учеников."""
    model = TeacherProfile
    template_name = "education/teacher_public_detail.html"
    context_object_name = "teacher"

    def get_queryset(self):
        return TeacherProfile.objects.filter(user__is_approved=True)


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = StudentProfile
    template_name = "education/student_detail.html"
    context_object_name = "student"

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Ученик может смотреть только свой профиль
        if hasattr(user, "student_profile") and user.student_profile.id == kwargs["pk"]:
            return super().dispatch(request, *args, **kwargs)

        # Педагог может смотреть профиль своего ученика
        if hasattr(user, "teacher_profile"):
            student = StudentProfile.objects.get(pk=kwargs["pk"])
            is_my_student = TeachingAssignment.objects.filter(
                teacher=user.teacher_profile,
                student=student
            ).exists()

            if is_my_student:
                return super().dispatch(request, *args, **kwargs)

        # Остальные — нет доступа
        return HttpResponseForbidden("У вас нет доступа к этому профилю.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        context["assignments"] = TeachingAssignment.objects.filter(student=student)
        context["lessons"] = Lesson.objects.filter(
            assignment__student=student
        ).order_by("-date")

        context["performances"] = Performance.objects.filter(
            assignment__student=student
        ).order_by("-created_at")

        return context


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = TeacherProfile
    template_name = "education/teacher_detail.html"
    context_object_name = "teacher"

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Сам педагог может смотреть свой профиль
        if hasattr(user, "teacher_profile") and user.teacher_profile.id == kwargs["pk"]:
            return super().dispatch(request, *args, **kwargs)

        # Ученик может смотреть профиль своего педагога
        if hasattr(user, "student_profile"):
            teacher = TeacherProfile.objects.get(pk=kwargs["pk"])
            is_my_teacher = TeachingAssignment.objects.filter(
                teacher=teacher,
                student=user.student_profile
            ).exists()

            if is_my_teacher:
                return super().dispatch(request, *args, **kwargs)

        # Остальные — нет доступа
        return HttpResponseForbidden("У вас нет доступа к этому профилю.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.object

        context["assignments"] = TeachingAssignment.objects.filter(teacher=teacher)
        context["students"] = [a.student for a in context["assignments"]]
        context["lessons"] = Lesson.objects.filter(
            assignment__teacher=teacher
        ).order_by("-date")
        context["performances"] = Performance.objects.filter(
            assignment__teacher=teacher
        ).order_by("-created_at")

        return context

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


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = "education/lesson_detail.html"
    context_object_name = "lesson"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        lesson = self.get_object()

        # Ученик может смотреть только свои уроки
        if hasattr(user, "student_profile"):
            if lesson.assignment.student == user.student_profile:
                return super().dispatch(request, *args, **kwargs)

        # Педагог может смотреть только свои уроки
        if hasattr(user, "teacher_profile"):
            if lesson.assignment.teacher == user.teacher_profile:
                return super().dispatch(request, *args, **kwargs)

        return HttpResponseForbidden("У вас нет доступа к этому уроку.")


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
        return reverse_lazy("education:lesson_list")


class LessonUpdateView(LoginRequiredMixin, TeacherRequiredMixin, UpdateView):
    model = Lesson
    fields = ["date", "instrument", "piece", "homework", "comment"]
    template_name = "education/lesson_form.html"

    def get_success_url(self):
        return reverse_lazy("education:lesson_detail", kwargs={"pk": self.object.id})


class LessonDeleteView(LoginRequiredMixin, TeacherRequiredMixin, DeleteView):
    model = Lesson
    template_name = "education/lesson_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("education:lesson_list")


class LessonMaterialCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
    model = LessonMaterial
    form_class = LessonMaterialForm
    template_name = "education/lesson_material_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.lesson = get_object_or_404(Lesson, pk=kwargs["lesson_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.lesson = self.lesson
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("education:lesson_detail", kwargs={"pk": self.lesson.id})


class AssignmentListView(LoginRequiredMixin, ListView):
    model = TeachingAssignment
    template_name = "education/assignment_list.html"
    context_object_name = "assignments"

    def get_queryset(self): 
        user = self.request.user
        if hasattr(user, "teacher_profile"):
            return TeachingAssignment.objects.filter(teacher=user.teacher_profile)
        return TeachingAssignment.objects.none()


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = TeachingAssignment
    template_name = "education/assignment_detail.html"
    context_object_name = "assignment"


class AssignmentCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
    model = TeachingAssignment
    form_class = AssignmentForm
    template_name = "education/assignment_form.html"
    success_url = reverse_lazy("education:assignment_list")

    def form_valid(self, form):
        form.instance.teacher = self.request.user.teacher_profile
        return super().form_valid(form)


class AssignmentUpdateView(LoginRequiredMixin, TeacherRequiredMixin, UpdateView):
    model = TeachingAssignment
    form_class = AssignmentForm
    template_name = "education/assignment_form.html"

    def get_success_url(self):
        return reverse("education:assignment_detail", args=[self.object.pk])



class AssignmentDeleteView(LoginRequiredMixin, TeacherRequiredMixin, DeleteView):
    model = TeachingAssignment
    template_name = "education/assignment_confirm_delete.html"
    success_url = reverse_lazy("education:assignment_list")


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


class PerformanceDetailView(LoginRequiredMixin, DetailView):
    model = Performance
    template_name = "education/performance_detail.html"
    context_object_name = "performance"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        performance = self.get_object()

        # Админ видит всё
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Ученик может смотреть только свои исполнения
        if hasattr(user, "student_profile"):
            if performance.assignment.student == user.student_profile:
                return super().dispatch(request, *args, **kwargs)

        # Педагог может смотреть исполнения своих учеников
        if hasattr(user, "teacher_profile"):
            if performance.assignment.teacher == user.teacher_profile:
                return super().dispatch(request, *args, **kwargs)

        return HttpResponseForbidden("У вас нет доступа к этому исполнению.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.all().order_by("-created_at")
        return context


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
        return reverse_lazy("education:performance_list")


class PerformanceMaterialUpdateView(LoginRequiredMixin, TeacherRequiredMixin, UpdateView):
    model = Performance
    form_class = PerformanceMaterialForm
    template_name = "education/performance_material_form.html"

    def get_success_url(self):
        return reverse_lazy("education:performance_detail", kwargs={"pk": self.object.id})


class PerformanceCommentCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
    model = PerformanceComment
    form_class = PerformanceCommentForm
    template_name = "education/performance_comment_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.performance = get_object_or_404(Performance, pk=kwargs["performance_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.performance = self.performance
        form.instance.teacher = self.request.user.teacher_profile
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("education:performance_detail", kwargs={"pk": self.performance.id})


class PerformanceUpdateView(LoginRequiredMixin, TeacherRequiredMixin, UpdateView):
    model = Performance
    fields = ["piece", "video", "score"]
    template_name = "education/performance_form.html"

    def get_success_url(self):
        return reverse_lazy("education:performance_detail", kwargs={"pk": self.object.id})


class PerformanceDeleteView(LoginRequiredMixin, TeacherRequiredMixin, DeleteView):
    model = Performance
    template_name = "education/performance_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("education:performance_list")


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    template_name = "education/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.student_profile

        context["lessons"] = Lesson.objects.filter(
            assignment__student=student
        ).order_by("-date")[:5]

        context["assignments"] = TeachingAssignment.objects.filter(
            student=student
        )[:5]

        context["performances"] = Performance.objects.filter(
            assignment__student=student
        ).order_by("-created_at")[:5]

        return context

class TeacherDashboardView(LoginRequiredMixin, TeacherRequiredMixin, TemplateView):
    template_name = "education/teacher_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile

        context["assignments"] = TeachingAssignment.objects.filter(
            teacher=teacher
        )[:5]

        context["lessons"] = Lesson.objects.filter(
            assignment__teacher=teacher
        ).order_by("-date")[:5]

        context["performances"] = Performance.objects.filter(
            assignment__teacher=teacher
        ).order_by("-created_at")[:5]

        context["students"] = [
            assignment.student for assignment in TeachingAssignment.objects.filter(teacher=teacher)
        ]

        return context


@login_required
@teacher_required
def add_performance_comment(request, pk):
    performance = get_object_or_404(Performance, pk=pk)

    if request.method == "POST":
        form = PerformanceCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.performance = performance
            comment.teacher = request.user.teacher_profile
            comment.save()
            return redirect("education:performance_detail", pk=pk)
    else:
        form = PerformanceCommentForm()

    return render(
        request,
        "education/performance_comment_form.html",
        {"form": form, "performance": performance}
    )








