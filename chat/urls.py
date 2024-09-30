from django.urls import path
from chat.views import chat_view
from chat.apis import interval

urlpatterns = [
    path('v1/chat', chat_view, name="chat_view"),
    path('v1/beat', interval.CeleryBeatView.as_view(), name="beat"),
    path('v1/intervals', interval.IntervalScheduleView.as_view(), name="intervals"),
    path('v1/tasks', interval.PeriodicTaskView.as_view(), name="tasks"),
    path('v1/results', interval.ResultsTasksView.as_view(), name="results"),
    path('v1/crontab', interval.CrontabScheduleView.as_view(), name="crontab")
]