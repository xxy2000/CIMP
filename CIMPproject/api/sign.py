from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
import json


def sign_in_out(request):
    # 获取request返回内容
    if request.method == 'POST':
        request.params = json.loads(request.body)
    else:
        return JsonResponse({'ret': 1, 'msg': '只支持POST请求'})
    if request.params['action'] == 'signin':
        return signin(request, request.params)
    elif request.params['action'] == 'signout':
        return signout(request)
    else:
        return JsonResponse({'ret': 1, 'msg': '不支持该类型http请求'})


def signin(request, params):
    # 登入处理
    userName = params['username']
    passWord = params['password']
    user = authenticate(username=userName, password=passWord)
    # 如果用户存在，并且没被禁用
    if user is not None:
        if user.is_active:
            login(request, user)
            # 存入session
            request.session['REQUIRED_FIELDS'] = [user.usertype, user.id]
            return JsonResponse({'ret': 0, "usertype": user.usertype, "userid": user.id, "realname": user.username})
        else:
            return JsonResponse({'ret': 1, 'msg': '用户已经被禁用'})
    else:
        return JsonResponse({'ret': 1, 'msg': '用户名或者密码错误'})


def signout(request):
    logout(request)
    return JsonResponse({'ret': 0})