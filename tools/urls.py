from django.urls import path
from tools.apis import alarm, meat_menus, article, flow, process, promote, res


urlpatterns = [
    path('v1/res', res.ResChangeView.as_view(), name='res'),
    path('v1/promote', promote.PromoteClockView.as_view(), name='promote'),
    path('v1/alarm', alarm.AlarmClockView.as_view(), name='alarm'),
    path('v1/meat-menus', meat_menus.MeatMenusView.as_view(), name='meat-menus'),
    path('v1/articles', article.ArticlesView.as_view(), name='articles'),
    path('v1/article-down', article.ArticleDownView.as_view(), name='article-down'),
    path('v1/flow', flow.FlowView.as_view(), name='flows'),
    path('v1/process', process.JobsProcessView.as_view(), name='process'),
    path('v1/process-history', process.JobsProcessHistoryView.as_view(),
         name='process-history'),
]
