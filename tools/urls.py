from django.urls import path
from tools.apis import alarm, meat_menus, article


urlpatterns = [
    path('v1/alarm', alarm.AlarmClockView.as_view(), name='alarm'),
    path('v1/meat-menus', meat_menus.MeatMenusView.as_view(), name='meat-menus'),
    path('v1/articles', article.ArticlesView.as_view(), name='articles'),
]
