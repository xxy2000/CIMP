from django.http import JsonResponse
import json
from api.models import User, Notification, News, Paper, Likes, Students, Workflow, Workstep
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.hashers import make_password
from django.db import transaction


def dispatcher(request):
    # 判断是否登录/管理员
    if 'REQUIRED_FIELDS' not in request.session:
        return JsonResponse({'ret': 302, 'msg': '用户未登录', 'redirect': '/api/sign'}, status=302)
    if request.session['REQUIRED_FIELDS'][0] != 1:
        return JsonResponse({'ret': 302, 'msg': '用户非管理员', 'redirect': '/api/sign'}, status=302)
    # 将请求参数统一放入request参数的params中，方便后续处理
    if request.method == 'GET':
        request.params = request.GET
    elif request.method in ['POST', 'PUT', 'DELETE']:
        request.params = json.loads(request.body)
    # 根据不同的action分派给不同函数处理
    action = request.params['action']
    if action == 'listbypage':
        return listbypage(request)
    elif action == 'addone':
        return addone(request)
    elif action == 'modifyone':
        return modifyone(request)
    elif action == 'deleteone':
        return deleteone(request)
    else:
        return JsonResponse({'ret': 1, 'msg': '不支持该类型的http请求'})


def listbypage(request):
    # 用来列出系统中的账号信息。
    try:
        # 按照最近插入顺序插入
        qs = User.objects.values().order_by('-id')
        # 根据keyword筛选
        keywords = request.params.get('keywords', None)
        if keywords:
            conditions = [Q(name__contains=one) for one in keywords.split(' ')if one]
            query = Q()
            for condition in conditions:
                query &= condition
            qs.filter(query)
        pagenum = request.params['pagenum']
        pagesize = request.params['pagesize']
        pgnt = Paginator(qs, pagesize)
        items = list(pgnt.page(pagenum))
        return JsonResponse({'ret': 0, 'items': items, 'total': pgnt.count, 'keywords': keywords})
    except EmptyPage:
        return JsonResponse({'ret': 0, 'items': [], 'total': 0, 'keywords': ""})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 2, 'msg': '未知错误'})


def addone(request):
    # 添加账号
    info = request.params['data']
    user = User.objects.create(realname=info['realname'],
                               username=info['username'],
                               password=make_password(info['password']),
                               studentno=info['studentno'],
                               desc=info['desc'],
                               usertype=info['usertype'])
    return JsonResponse({'ret': 0, 'id': user.id})


def modifyone(request):
    # 用来修改系统中的账号信息
    # 获取修改账号的id和修改内容
    user_id = request.params['id']
    newdata = request.params['newdata']
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'ret': 1, 'msg': '不存在此ID'})
    if 'realname' in newdata:
        user.realname = newdata['realname']
    if 'username' in newdata:
        user.username = newdata['username']
    if 'studentno' in newdata:
        user.studentno = newdata['studentno']
    if 'password' in newdata:
        user.password = make_password(newdata['password'])
    if 'desc' in newdata:
        user.desc = newdata['desc']
    user.save()
    return JsonResponse({'ret': 0})


def deleteone(request):
    # 用来删除系统中的账号信息
    user_id = request.params['id']
    # 通过级联删除多个表与user有关的内容
    try:
        user = User.objects.get(id=user_id)
        with transaction.atomic():
            Notification.objects.filter(user=user).delete()
            News.objects.filter(user=user).delete()
            papers = Paper.objects.filter(user=user)
            if papers:
                query = Q()
                for paper in papers:
                    query |= Q(paper=paper)
                Likes.objects.filter(query).delete()
            papers.delete()
            if user.usertype in [2000, 3000]:
                if user.usertype == 2000:
                    students = Students.objects.filter(sid=user.id)
                else:
                    students = Students.objects.filter(Tea=user)
                query = Q()
                if students:
                    for student in students:
                        s_user = User.objects.get(id=student.sid)
                        query |= Q(user=s_user)
                    workflows = Workflow.objects.filter(query)
                    query = Q()
                    if workflows:
                        for workflow in workflows:
                            query |= Q(workflow=workflow)
                        Workstep.objects.filter(query).delete()
                        workflows.delete()
                    students.delete()
            user.delete()
        return JsonResponse({'ret': 0})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})
