from django.http import JsonResponse
import json
from api.models import User,Students,Likes,Paper
from django.db.models import Q,F
from django.contrib.auth.hashers import make_password


def dispatcher(request):
    if request.method == 'GET':
        request.params = request.GET
    elif request.method in ['POST', 'PUT', 'DELETE']:
        request.params = json.loads(request.body)
    action=request.params['action']
    if 'REQUIRED_FIELDS' not in request.session:
        return JsonResponse({'ret': 302, 'msg': '用户未登录', 'redirect': '/api/sign'}, status=302)
    if request.session['REQUIRED_FIELDS'][0] != 2000 and request.session['REQUIRED_FIELDS'][0] != 3000:
        return JsonResponse({'ret': 302, 'msg': '只有学生/老师才能查看/修改个人信息', 'redirect': '/api/sign'}, status=302)
    elif action == 'getmyprofile':
        return getmyprofile(request)
    elif action == 'setmyprofile':
        return setmyprofile(request)
    elif action == 'listteachers':
        return listteachers(request)
    elif action == 'thumbuporcancel':
        return thumbuporcancel(request)
    else:
        return JsonResponse({'ret': 1, 'msg': '没有这类型的http'})


def getmyprofile(request):
    try:
        id = request.session['REQUIRED_FIELDS'][1]
        if request.session['REQUIRED_FIELDS'][0] == 3000:
            data = User.objects.filter(id=id).annotate(userid=F('id')).values('userid', 'username', 'usertype', 'realname')
            return JsonResponse({'ret': 0, 'profile': list(data)[0]})
        else:
            one = User.objects.get(id=id)
            student = Students.objects.filter(sid=id)
            if student:
                teacher = {'id': student[0].Tea.id, 'realname': student[0].Tea.realname}
            else:
                teacher = {'id': None, 'realname': None}
            return JsonResponse({'ret': 0, 'profile': {'userid': one.id, 'usernmae': one.username, 'usertype': one.usertype,
                                                       'realname': one.realname, 'teacher': teacher}})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})


def setmyprofile(request):
    try:
        id = request.session['REQUIRED_FIELDS'][1]
        newdata = request.params['newdata']
        one = User.objects.get(id=id)
        if 'realname' in newdata:
            one.realname = newdata['realname']
        if 'password' in newdata:
            one.password = make_password(newdata['password'])
        one.save()
        if 'teacherid' in newdata:
            teacher = User.objects.get(id=newdata['teacherid'])
            if teacher and teacher.usertype == 3000:
                print(111111111111111111)
                stu = Students.objects.filter(sid=id)
                if stu:
                    stu[0].Tea = teacher
                    stu[0].save()
                else:
                    Students.objects.create(sid=id, Tea=teacher)
            else:
                return JsonResponse({'ret': 1, 'msg': '你输入的ID不存在/不是老师的ID'})
        return JsonResponse({'ret': 0})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})


def listteachers(request):
    try:
        qs = User.objects.filter(usertype=3000).values('id', 'realname')
        keywords = request.params.get('keywords', None)
        if keywords:
            contains = [Q(realname__contains=one) for one in keywords.split(' ') if one]
            query = Q()
            for contain in contains:
                query &= contain
            qs = qs.filter(query)
        return JsonResponse({'ret': 0, 'items': list(qs)})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})


def thumbuporcancel(request):
    try:
        user_id = request.session['REQUIRED_FIELDS'][1]
        user = User.objects.get(id=user_id)
        paper_id = request.params['paperid']
        paper = Paper.objects.get(id=paper_id)
        like_record, b = Likes.objects.get_or_create(user=user, paper=paper)
        if b:
            paper.thumbupcount += 1
        else:
            paper.thumbupcount -= 1
            like_record.delete()
        paper.save()
        return JsonResponse({'ret': 0, "thumbupcount": paper.thumbupcount})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})


