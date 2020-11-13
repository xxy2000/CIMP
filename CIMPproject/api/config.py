from django.http import JsonResponse
import json
from api.models import News, Notification, Paper
from django.db.models import Q, F
from django.views.decorators.cache import cache_page


def dispatcher(request):
    if request.method == 'GET':
        request.params = request.GET
    if request.method in ['POST', 'DELETE', 'PUT']:
        request.params = json.loads(request.body)
    action = request.params['action']
    if action == 'gethomepagebyconfig':
        return gethomepagebyconfig(request)
    elif 'REQUIRED_FIELDS' not in request.session:
        return JsonResponse({'ret': 302, 'msg': '用户未登录', 'redirect': '/api/sign'}, status=302)
    elif request.session['REQUIRED_FIELDS'][0] != (1 or 1000):
        return JsonResponse({'ret': 302, 'msg': '用户非管理员', 'redirect': '/api/sign'}, status=302)
    elif action == 'set':
        return setconfig(request)
    elif action == 'get':
        return getconfig(request)
    else:
        return JsonResponse({'ret': 1, 'msg': '没有这类型的http'})


def setconfig(request):
    # 设置首页显示的文献
    try:
        value = request.params.get('value', None)
        if value:
            f = open('./config.txt', 'w')
            f.write(value)
            f.close()
        return JsonResponse({'ret': 0})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})


def getconfig(request):
    # 获取首页显示的文献
    try:
        f = open('./config.txt', 'r')
        value = f.read()
        f.close()
        return JsonResponse({'ret': 0, 'value': value})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})


@cache_page(60 * 5)
# 由于首页经常访问，设置一个5min的缓存
def gethomepagebyconfig(request):
    # 首页显示信息
    try:
        f = open('./config.txt', 'r')
        value = json.loads(f.read())
        f.close()
        info, query = {}, Q()
        if 'news' in value:
            for id in value['news']:
                query |= Q(id__contains=id)
            data = News.objects.filter(query).annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'status')if query else[]
            # 只有status为发布状态的才可以显示在首页
            data = data.filter(status=1)
            info.update({"news": list(data)})
        if 'notice' in value:
            query = Q()
            for id in value['notice']:
                query |= Q(id__contains=id)
            data = Notification.objects.filter(query).annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'status')if query else[]
            # 只有status为发布状态的才可以显示在首页
            data = data.filter(status=1)
            info.update({"notice": list(data)})

        if 'paper' in value:
            query = Q()
            for id in value['paper']:
                query |= Q(id__contains=id)
            data = Paper.objects.filter(query).annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'status')if query else[]
            # 只有status为发布状态的才可以显示在首页
            data = data.filter(status=1)
            info.update({"paper": list(data)})
        return JsonResponse({'ret': 0, 'info': info})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})
