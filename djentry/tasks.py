app = Celery("djentry")


@app.task()
def test2():
    pass