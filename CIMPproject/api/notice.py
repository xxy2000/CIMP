from api import notice_news, models


def dispatcher(request):
    return notice_news.dispatcher(request, models.Notification)