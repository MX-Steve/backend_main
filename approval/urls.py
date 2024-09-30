from django.urls import path
from approval.apis import approval
urlpatterns = [
     path('v2/approval', approval.BusinessProject.as_view(), name='approval'),
]
