from django.urls import path
from manages.apis import roles

urlpatterns = [
    path('v1/role', roles.RoleView.as_view(), name='role'),
]
