from django.http import JsonResponse
import json
from api.models import User
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage


def dispatcher(request, n):
    # 新闻/通知处理函数，n表示新闻/通知model
    # 获取request 具体内容
    if request.method == 'GET':
        request.params = request.GET
    if request.method in ['POST', 'PUT', 'DELETE']:
        request.params = json.loads(request.body)
    action = request.params['action']
    # 根据action的不同，返回对应的函数
    if action == 'listbypage':
        return listbrpage(request, n)
    elif action == 'getone':
        return getone(request, n)
    # 判断是否登录/管理员，后面的方法都只有管理员才能使用
    elif 'REQUIRED_FIELDS' not in request.session:
        return JsonResponse({'ret': 302, 'msg': '用户未登录', 'redirect': '/api/sign'}, status=302)
    elif request.session['REQUIRED_FIELDS'][0] != (1 or 1000):
        return JsonResponse({'ret': 302, 'msg': '用户非管理员', 'redirect': '/api/sign'}, status=302)
    elif action == 'listbypage_allstate':
        return listbypage_allstate(request, n)
    elif action == 'addone':
        return addone(request, n)
    elif action == 'modifyone':
        return modifyone(request, n)
    elif action == 'banone':
        return banone(request, n)
    elif action == 'publishone':
        return publishone(request, n)
    elif action == 'deleteone':
        return deleteone(request, n)
    else:
        return JsonResponse({'ret': 1, 'msg': '没有这类型的http'})


def listbrpage(request, n):
    # 用来列出系统中处于发布状态的通知
    try:
        # 如果withoutcontent为true就不需要传content信息，节省流量
        withoutcontent = request.params.get('withoutcontent', None)
        if withoutcontent:
            qs = n.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'status')
        else:
            qs = n.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'content', 'status')
        # 只有status=1，处于发布状态的通知才会发布
        qs = qs.filter(status=1)
        # 分页处理
        pagesize = request.params['pagesize']
        pagenum = request.params['pagenum']
        # 关键词查询处理
        keywords = request.params.get('keywords', None)
        if keywords:
            contains = [Q(title__contains=one) for one in keywords.split(' ')if one]
            query = Q()
            for contain in contains:
                query &= contain
            qs = qs.filter(query)
        total = qs.count()
        pgnt = Paginator(qs, pagesize)
        items = list(pgnt.page(pagenum))
        return JsonResponse({'ret': 0, 'items': items, 'total': total, 'keywords': keywords})
    except EmptyPage:
        return JsonResponse({'ret': 0, 'items': [], 'total': 0, 'keywords': ""})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '发生了未知错误'})


def listbypage_allstate(request, n):
    # 用来列出系统中 所有的 通知。 包括非发布状态的通知 发出该 API 只能是管理员用户。后端要根据session校验
    try:
        # 几乎和上个方法一模一样，除了不需要status=1的筛选
        withoutcontent = request.params.get('withoutcontent', None)
        if withoutcontent:
            qs = n.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'status')
        else:
            qs = n.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'content', 'status')
        qs = n.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
        'author', 'author__realname', 'title', 'content', 'status')
        pagesize = request.params['pagesize']
        pagenum = request.params['pagenum']
        keywords = request.params.get('keywords', None)
        if keywords:
            contains = [Q(title__contains=one) for one in keywords.split(' ')if one]
            query = Q()
            for contain in contains:
                query &= contain
            qs = qs.filter(query)
        total = qs.count()
        pgnt = Paginator(qs, pagesize)
        items = list(pgnt.page(pagenum))
        return JsonResponse({'ret': 0, 'items': items, 'total': total, 'keywords': keywords})
    except EmptyPage:
        return JsonResponse({'ret': 0, 'items': [], 'total': 0, 'keywords': ""})
    except:
        return JsonResponse({'ret': 1, 'msg': '发生了未知错误'})


def getone(request, n):
    # 用来查看一条通知的内容。
    nid = request.params['id']
    try:
        one = n.objects.filter(id=nid).annotate(author=F('user__id'), author__realname=F('user__realname')).values('id',
        'pubdate', 'author', 'author__realname', 'title', 'content', 'status')
        return JsonResponse({'ret': 0, 'rec': list(one)[0]})
    except n.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该通知不存在'})


def addone(request, n):
    # 用来添加一条通知，发出该 API 只能是管理员用户。后端要根据session校验
    data = request.params['data']
    user = User.objects.get(id=request.session['REQUIRED_FIELDS'][1])
    new = n.objects.create(
        title=data['title'],
        content=data['content'],
        user=user,
        status=1
    )
    return JsonResponse({'ret': 0, 'id': new.id})


def modifyone(request, n):
    # 发出该 API 只能是管理员用户。后端要根据session校验
    nid = request.params['id']
    newdata = request.params['newdata']
    try:
        one = n.objects.get(id=nid)
    except n.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该通知不存在'})
    if 'title' in newdata:
        one.title = newdata['title']
    if 'content' in newdata:
        one.content = newdata['content']
    one.status = 1
    one.save()
    return JsonResponse({'ret': 0})


def banone(request, n):
    # 用来封禁一条通知。封禁后的通知，对学生、老师、未登录账号不可见，发出该 API 只能是管理员用户。后端要根据session校验。
    nid = request.params['id']
    try:
        one = n.objects.get(id=nid)
    except n.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该通知不存在'})
    # 封禁通知只需要将status改为3
    one.status = 3
    one.save()
    return JsonResponse({'ret': 0, 'status': one.status})


def publishone(request, n):
    nid = request.params['id']
    try:
        one = n.objects.get(id=nid)
    except n.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该通知不存在'})
    one.status = 1
    one.save()
    return JsonResponse({'ret': 0, 'status': one.status})


def deleteone(request, n):
    # 用来删除一条通知，发出该 API 只能是管理员用户。后端要根据session校验。
    nid = request.params['id']
    try:
        one = n.objects.get(id=nid)
    except n.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该通知不存在'})
    one.delete()
    return JsonResponse({'ret': 0})
