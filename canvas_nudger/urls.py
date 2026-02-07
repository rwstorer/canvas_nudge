from django.urls import path
from . import views

urlpatterns = [
    path('', views.StartView.as_view(), name='start'),
    path('courses/confirm/', views.ConfirmCoursesView.as_view(), name='courses_confirm'),
    path('report/', views.WeeklyReportView.as_view(), name='weekly_report'),
    path('messages/preview/', views.MessagePreviewView.as_view(), name='messages_preview'),
    path('messages/send/', views.SendMessagesView.as_view(), name='messages_send'),
    path('templates/', views.MessageTemplateView.as_view(), name='message_templates'),
]
