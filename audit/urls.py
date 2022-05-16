from django.urls import path
from audit.apis import audit

urlpatterns = [
    path('v1/audit', audit.AuditHistoryView.as_view(), name="audit")
]
