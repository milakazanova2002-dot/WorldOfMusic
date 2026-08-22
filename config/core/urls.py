from django.urls import path

from .views import HomeView, NotificationListView, notification_mark_read, SupportRequestCreateView, FAQView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("notifications/", NotificationListView.as_view(), name="notification_list"),
    path("notifications/<int:pk>/read/", notification_mark_read, name="notification_mark_read"),
    path("support/", SupportRequestCreateView.as_view(), name="support"),
    path("faq/", FAQView.as_view(), name="faq"),
]