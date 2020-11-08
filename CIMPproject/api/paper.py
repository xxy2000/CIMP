from django.http import JsonResponse
import json
from api.models import User, Paper, Like
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage
from django.db import transaction


def dispatcher(request):
    # 论文处理函数，部分与notice_news处理方式一致
    if request.method == 'GET':
        request.params = request.GET
    if request.method in ['POST', 'DELETE', 'PUT']:
        request.params = json.loads(request.body)
    action = request.params['action']
    if action == 'listbypage':
        return listbrpage(request)
    elif action == 'getone':
        return getone(request)
    elif 'REQUIRED_FIELDS' not in request.session:
        return JsonResponse({'ret': 302, 'msg': '你还没有登录(QAQ)', 'redirect': '/api/sign'}, status=302)
    elif action == 'listbypage_allstate':
        return listbypage_allstate(request)
    elif action == 'listminebypage':
        return listminebypage(request)
    elif action == 'addone':
        return addone(request)
    elif action == 'modifyone':
        return modifyone(request)
    elif action == 'holdone':
        return holdone(request)
    elif action == 'banone':
        return banone(request)
    elif action == 'publishone':
        return publishone(request)
    elif action == 'deleteone':
        return deleteone(request)
    else:
        return JsonResponse({'ret': 1, 'msg': '没有这类型的http'})


def listbrpage(request):
    # 用来列出系统中 发布状态 的论文。
    try:
        withoutcontent = request.params.get('withoutcontent', None)
        if withoutcontent:
            qs = Paper.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'thumbupcount', 'status')
        else:
            qs = Paper.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate',
            'author', 'author__realname', 'title', 'content', 'thumbupcount', 'status')

        total = qs.count()
        qs = qs.filter(status__contains=1)
        pagesize = request.params['pagesize']
        pagenum = request.params['pagenum']
        keywords = request.params.get('keywords',None)
        if keywords:
            contains = [Q(title__contains=one) for one in keywords.split(' ')if one]
            query = Q()
            for contain in contains:
                query &= contain
            qs = qs.filter(query)
        pgnt = Paginator(qs, pagesize)
        items = list(pgnt.page(pagenum))
        return JsonResponse({'ret': 0, 'items': items, 'total': total, 'keywords': keywords})
    except EmptyPage:
        return JsonResponse({'ret': 0, 'items': [], 'total': 0, 'keywords': ""})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '发生了未知错误'})


def listbypage_allstate(request):
    # 用来列出系统中 所有的 论文。 包括非发布状态的论文
    #
    # 发出该 API 只能是管理员用户。后端要根据session校验。
    try:
        withoutcontent = request.params.get('withoutcontent', None)
        if withoutcontent:
            qs = Paper.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id','pubdate',
            'author', 'author__realname', 'title', 'thumbupcount', 'status')
        else:
            qs = Paper.objects.annotate(author=F('user__id'), author__realname=F('user__realname')).values('id','pubdate',
            'author', 'author__realname', 'title', 'content', 'thumbupcount', 'status')
        pagesize = request.params['pagesize']
        pagenum = request.params['pagenum']
        keywords = request.params.get('keywords', None)
        if keywords:
            contains = [Q(title__contains=one) for one in keywords.split(' ') if one]
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


def listminebypage(request):
    # 用来列出系统中 我创建的 论文。 包括非发布状态的论文
    #
    # 发出该 API 只能是学生、老师账号。后端要根据session校验。
    if request.session['REQUIRED_FIELDS'][0] != 2000 and request.session['REQUIRED_FIELDS'][0] != 3000:
        return JsonResponse({'ret': 302, 'msg': '只有在职学生/老师才能有论文哦(>_<)', 'redirect': '/api/sign'}, status=302)
    try:
        # 通过session获取登录本人id，然后进行筛选处理
        user = User.objects.get(id=request.session['REQUIRED_FIELDS'][1])
        qs = user.paper_set.all().annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate'
        , 'author', 'author__realname', 'title', 'content', 'thumbupcount', 'status')
        pagesize = request.params['pagesize']
        pagenum = request.params['pagenum']
        keywords = request.params.get('keywords', None)
        if keywords:
            contains = [Q(title__contains=one) for one in keywords.split(' ') if one]
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


def getone(request):
    # 用来查看一条论文的内容。该API的格式 和 查看一条论文API 格式一致
    id = request.params['id']
    try:
        one = Paper.objects.filter(id=id).annotate(author=F('user__id'), author__realname=F('user__realname')).values('id', 'pubdate', 'author', 'author__realname', 'title', 'content','thumbupcount', 'status')
        return JsonResponse({'ret': 0, 'rec': list(one)[0]})
    except Paper.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该论文不存在'})


def addone(request):
    # 用来添加一条论文。
    data = request.params['data']
    user = User.objects.get(id=request.session['REQUIRED_FIELDS'][1])
    new = Paper.objects.create(
        title=data['title'],
        content=data['content'],
        user=user,
        status=1
    )
    return JsonResponse({'ret': 0, 'id': new.id})


def modifyone(request):
    # 修改论文,发出该 API 只能是该论文的作者。后端要根据session校验。
    id = request.params['id']
    try:
        one = Paper.objects.get(id=id)
    except Paper.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该论文不存在'})
    if request.session['REQUIRED_FIELDS'][1] != one.user.id:
        return JsonResponse({'ret': 1, 'msg': '请不要试图修改别人的论文哦(>_<)'})
    newdata = request.params['newdata']
    if 'title' in newdata:
        one.title = newdata['title']
    if 'content' in newdata:
        one.content = newdata['content']
    one.save()
    return JsonResponse({'ret': 0})


def holdone(request):
    # 用来撤回一条论文。封禁后的论文，对学生、老师、未登录账号不可见
    #
    # 发出该 API 只能是作者本人。后端要根据session校验。
    id = request.params['id']
    try:
        one = Paper.objects.get(id=id)
    except Paper.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该论文不存在'})
    if request.session['REQUIRED_FIELDS'][1] != one.user.id:
        return JsonResponse({'ret': 1, 'msg': '撤回别人的论文是不好的(>_<)'})
    # 撤回论文的同时，删除所有点赞记录
    with transaction.atomic():
        one.status = 2
        one.thumbupcount = 0
        one.save()
        Like.objects.filter(pid=one.id).delete()
    return JsonResponse({'ret': 0, 'status': one.status})


def banone(request):
    # 用来封禁一条论文。封禁后的论文，对学生、老师、未登录账号不可见
    #
    # 发出该 API 只能是管理员用户。后端要根据session校验
    if request.session['REQUIRED_FIELDS'][0] != (1 or 1000):
        return JsonResponse({'ret': 1, 'msg': '只有管理员才能封禁论文 (-_-)'})
    try:
        id = request.params['id']
        one = Paper.objects.get(id=id)
    except Paper.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该论文不存在'})
    # 封禁论文的同时，删除所有点赞记录
    with transaction.atomic():
        one.status = 3
        one.thumbupcount = 0
        one.save()
        Like.objects.filter(pid=one.id).delete()
    return JsonResponse({'ret': 0, 'status': one.status})


def publishone(request):
    # 用来解禁一条论文。解禁后的论文，对学生、老师、未登录账号恢复可见
    # 获取准备解禁论文信息以及当前登陆者id
    id = request.params['id']
    user_id = request.session['REQUIRED_FIELDS'][1]
    one = Paper.objects.get(id=id)
    # 封禁态/撤回态的论文的处理权限不同，两者都可以被管理员发布，但撤回态论文还可以被本人重新发布
    if one.status == 3:
        if request.session['REQUIRED_FIELDS'][0] != 1 and request.session['REQUIRED_FIELDS'][0] != 1000:
            return JsonResponse({'ret': 1, 'msg': '只有管理员才能解禁被封禁的论文 (-_-)'})
    elif one.status == 2:
        if request.session['REQUIRED_FIELDS'][0] != 1 and request.session['REQUIRED_FIELDS'][0] != 1000 and user_id != one.user.id:
            return JsonResponse({'ret': 1, 'msg': '只有管理员/本人才能发布被撤回的论文 (-_-)'})
    one.status = 1
    one.save()
    return JsonResponse({'ret': 0, 'status': one.status})


def deleteone(request):
    # 用来删除一条论文。
    #
    # 发出该 API 只能是管理员用户 或者 论文作者。后端要根据session校验。
    id = request.params['id']
    try:
        one = Paper.objects.get(id=id)
    except Paper.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '该论文不存在'})
    if request.session['REQUIRED_FIELDS'][0] != 1 and request.session['REQUIRED_FIELDS'][0] != 1000 and request.session['REQUIRED_FIELDS'][1] != one.user.id:
        return JsonResponse({'ret': 1, 'msg': '只有管理员/用户作者才能删除论文 (-_-)'})
    # 删除论文的同时，删除所有点赞记录
    with transaction.atomic():
        Like.objects.filter(pid=one.id).delete()
        one.delete()
    return JsonResponse({'ret': 0})