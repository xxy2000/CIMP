from django.shortcuts import render
from django.http import HttpResponse

def listorders(request):
    return HttpResponse("下面是系统中所有的订单信息。。。")


def listorders1(request):
    return HttpResponse("下面是系统中所有的订单信息111。。。")



def listorders2(request):
    return HttpResponse("下面是系统中所有的订单信息222。。。")


def listorders3(request):
    return HttpResponse("下面是系统中所有的订单信息3333。。。")