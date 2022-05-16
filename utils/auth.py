from functools import wraps
from django.http import JsonResponse
from manages.models import Role


def has_perms(user, codes):
    page_perms_ids = user.roles.strip('[').strip(']').split(',')
    page_perms = []
    for r_id in page_perms_ids:
        if r_id != "":
            r = Role.objects.filter(id=r_id).first()
            perms = r.page_perms.strip('[').strip(']').split(',')
            for p in perms:
                if p not in page_perms:
                    page_perms.append(p)
    result = set(page_perms).intersection(set(codes))
    return len(result) > 0


def auth(perm_list):
    def decorate(view_func):
        codes = perm_list.split('|')
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = None
            for item in args[:2]:
                if hasattr(item, 'user'):
                    user = item.user
                    break
            if user and has_perms(user, codes):
                return view_func(*args, **kwargs)
            return JsonResponse({"code": 403, "data": {}, "msg": "权限拒绝"})

        return wrapper

    return decorate
