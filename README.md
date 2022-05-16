# 本地环境开发

```
$ mkdir build
$ python3 -m venv build
$ pip3 install -r requirements.txt
$ export DJANGO_SETTINGS_MODULE=djentry.settings.development
$ export DJANGO_SECRET_KEY='qe187p7jy6w%hrxdly6t=rq%2izaq@owxtefa=sc(gpnialsa!'
$ python3 manage.py runserver
```

你可以通过 http://localhost:8000 访问这个应用

# 代码必须要通过 pylint 检测

The implementation is expected to pass the pylint test.

# 返回 code 码自定义列表
| code码 | 含义 |
| ---- | ---- |
| 200 | 请求或操作数据成功 |
| 403 | 请求或操作数据没有权限 |
| 404 | 请求的 url 不存在 |
| 10001 | 需要创建的资源已存在 |
| 10002 | 需要操作的资源不存在[修改,删除] |
| 10003 | 需要携带的参数不对[缺失或未传] |
| 10004 | 需要操作的资源还有依赖，不能删除或修改 |
| 10005 | 参数值不能为空 |

# uvicorn 使用
```shell
$ uvicorn djentry.asgi:application --host 0.0.0.0 --port 8000
```
# celery 使用
```shell
# 启动 beat
$ celery -A djentry beat
# 启动 worker
$ celery -A djentry worker -l info --uid 1000
```
# test
```
just for test.
```