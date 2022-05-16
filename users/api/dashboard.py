import datetime
from django.http import JsonResponse
from utils import baseview
from users.models import User


class DashboardView(baseview.BaseView):
    """获取用户首页数据"""
    def get(self, request, args=None):
        pageNo = int(request.GET.get('page_no', 1))
        pageSize = int(request.GET.get('page_size', 10))
        start = (datetime.datetime.now() -
                 datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        users = User.objects.filter(last_login__gte=start,
                                    is_active=True).order_by("-last_login")
        data = []
        total = len(users)
        objs = users[(pageNo - 1) * pageSize:pageNo * pageSize]
        for user in objs:
            un = user.last_name.strip() + user.first_name.strip()
            if un:
                data.append({
                    "username": un,
                    "last_login": user.last_login,
                    "email": user.email
                })
            else:
                data.append({
                    "username": user.username,
                    "last_login": user.last_login,
                    "email": user.email
                })
        msg = {
            "code": 200,
            "data": {
                "users": data,
                "total": total
            },
            "msg": "获取首页数据成功"
        }
        return JsonResponse(msg)

