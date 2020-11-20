from django.http import JsonResponse
import json
from api.models import User, Workflow, Workstep, Students
from django.db.models import Q, F
from django.core.paginator import Paginator, EmptyPage


def dispatcher(request):
    if request.method == 'GET':
        request.params = request.GET
    if request.method in ['POST', 'PUT', 'DELETE']:
        request.params = json.loads(request.body)
    action = request.params['action']
    if 'REQUIRED_FIELDS' not in request.session:
        return JsonResponse({'ret': 302, 'msg': '用户未登录', 'redirect': '/api/sign'}, status=302)
    elif request.session['REQUIRED_FIELDS'][0] != 2000 and request.session['REQUIRED_FIELDS'][0] != 3000:
        return JsonResponse({'ret': 302, 'msg': '只有老师/学生有权利操作', 'redirect': '/api/sign'}, status=302)
    elif action == 'listbypage':
        return listbypage(request)
    elif action == 'getone':
        return getone(request)
    elif action == 'stepaction':
        return stepaction(request)
    elif action == 'getstepactiondata':
        return getstepactiondata(request)
    else:
        return JsonResponse({'ret': 1, 'msg': '没有这类型的http'})


def listbypage(request):
    try:
        # 得到登录用户id
        uid = request.session['REQUIRED_FIELDS'][1]
        # 学生查看毕业工作流
        if request.session['REQUIRED_FIELDS'][0] == 2000:
            # 根据自身ID对工作流进行过滤
            qs = Workflow.objects.filter(user__id=uid).annotate(creator=F('user__id'), creator__realname=
            F('user__realname')).values('id', 'creator', 'creator__realname', 'title', 'currentstate', 'createdate')
        # 老师查看毕业工作流
        else:
            user = User.objects.get(id=uid)
            # 根据Student关联表列出自己所有的学生
            students = user.students_set.all()
            if not students:
                return JsonResponse({'ret': 0, 'items': [], 'total': 0, 'keywords': ""})
            query = Q()
            for student in students:
                query |= Q(user__id=student.sid)
            # 根据自己的所有学生ID对工作流进行过滤
            qs = Workflow.objects.filter(query).annotate(creator=F('user__id'), creator__realname=
            F('user__realname')).values('id', 'creator', 'creator__realname', 'title', 'currentstate', 'createdate')
            print(students)
        # 经典的分页处理
        pagesize = request.params['pagesize']
        pagenum = request.params['pagenum']
        keywords = request.params.get('keywords', None)
        # 根据keywords筛选
        if keywords:
            query = Q()
            contains = [Q(title__contains=one) for one in keywords.split(' ')if one]
            for contain in contains:
                query &= contain
            qs.filter(query)
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
    try:
        # 获取工作流ID
        wf_id = int(request.params['wf_id'])
        # 如果工作流ID是-1代表需要创建工作流
        if wf_id == -1:
            return JsonResponse({
  "ret": 0,
  "rec": {
    "id": -1,
    "creatorname": "",
    "title": "",
    "currentstate": "",
    "createdate": ""
  },
  "whaticando": [
    {
      "name": "创建主题",
      "submitdata": [
        {
          "name": "毕业设计标题",
          "type": "text",
          "check_string_len": [
            1,
            20
          ]
        },
        {
          "name": "主题描述",
          "type": "richtext",
          "check_string_len": [
            0,
            2000
          ]
        }
      ],
      "whocan": 1,
      "next": "主题已创建",
      "key": "create_topic"
    }
  ]
})
        # 通过ID获取工作流和工作流下属所有的工作步骤,其中worksteps一定得按id顺序排列，不然工作流排序会出现错误
        # 通过select_related减少查询次数，提升性能
        workflow = Workflow.objects.select_related('user').get(id=wf_id)
        worksteps = workflow.workstep_set.all().order_by('id')
        # 将工作步骤所需信息添加进workstep对象里
        steps = []
        for workstep in worksteps:
            if workstep:
                steps.append({'id': workstep.id, 'operator__realname': workstep.operator.realname, 'actiondate': workstep.actiondate,
                             'actionname': workstep.actionname, 'nextstate': workstep.nextstate})
        # 根据最后一次操作判断接下来的工作流，并填写whaticando
        whaticando = []
        if request.params['withwhatcanido'] == 'true':
            last_action = steps[-1]['actionname']
            # 如果上次是学生操作，则下一次轮到老师操作
            if last_action == '创建主题' or last_action == '修改主题' or last_action == '提交毕业设计':
                # 上次学生操作过创建主题/修改主题后，轮到老师操作(检查session保存的usertype确定老师/学生)
                if request.session['REQUIRED_FIELDS'][0] == 3000:
                    whocan = Students.objects.get(sid=workflow.user.id).Tea.id
                    # 提交毕业设计后面的状态只能跟评分，但是创建/修改主题后面的状态可以有批准/驳回主题，所以需要分开写
                    if last_action == '提交毕业设计':
                        whaticando = [
                                 {
                                    "name": '评分',
                                    "submitdata": [
                                        {
                                            "name": "评分内容",
                                            "type": "richtext",
                                            "check_string_len": [
                                                0,
                                                2000
                                                                ]
                                        }
                                        ],
                                    "whocan": whocan,
                                    "next": '结束',
                                    "key": "over"
                                }]
                    else:
                        whaticando = [
    {
      "name": "驳回主题",
      "submitdata": [
        {
          "name": "驳回原因",
          "type": "richtext",
          "check_string_len": [
            0,
            2000
          ]
        }
      ],
      "whocan": whocan,
      "next": "主题被驳回",
      "key": "reject_topic"
    },
    {
      "name": "批准主题",
      "submitdata": [
        {
          "name": "备注",
          "type": "richtext",
          "check_string_len": [
            0,
            2000
          ]
        }
      ],
      "whocan": whocan,
      "next": "主题已通过",
      "key": "approve_topic"
    }
  ]
                else:
                    whaticando = []
            # 上次老师操作过驳回主题后，轮到学生操作
            if last_action == '驳回主题' or last_action == '批准主题':
                # 主题被驳回后，需要修改自己的主题
                if last_action == '驳回主题':
                    actionname = "修改主题"
                    nextstate = "主题已创建"
                    key = "change_topic"
                # 主题通过后，开始写毕业设计内容
                    submitdata = [
        {
          "name": "毕业设计标题",
          "type": "text",
          "check_string_len": [
            1,
            20
          ]
        },
        {
          "name": "修改内容",
          "type": "richtext",
          "check_string_len": [
            0,
            2000
          ]
        }
      ]
                else:
                    actionname = "提交毕业设计"
                    nextstate = "学生已提交毕业设计"
                    key = "write_data"
                    submitdata = [
                                        {
                                            "name": "提交内容",
                                            "type": "richtext",
                                            "check_string_len": [
                                                0,
                                                2000
                                                                ]
                                        }
                                        ]
                if request.session['REQUIRED_FIELDS'][0] == 2000:
                    whocan = workflow.user.id
                    whaticando = [
                                 {
                                    "name": actionname,
                                    "submitdata": submitdata,
                                    "whocan": whocan,
                                    "next": nextstate,
                                    "key": key
                                }]
                else:
                    whaticando = []
        return JsonResponse({'ret': 0, 'rec': {"id": workflow.id, "creatorname": workflow.user.realname, "title": workflow.title,
                                               "currentstate": workflow.currentstate, "createdate": workflow.createdate,
                                               "steps": steps}, "whaticando": whaticando})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '发生了未知错误'})


def stepaction(request):
    key = request.params['key']
    submitdata = request.params['submitdata']
    try:
        # create/change_topic 需要和其他key分开写，因为他们不仅要创建workstep还要创建/修改workflow
        if key in ['create_topic', 'change_topic']:
            if request.session['REQUIRED_FIELDS'][0] != 2000:
                return JsonResponse({'ret': 1, 'msg': '只有学生才有资格创建毕业设计'})
            opreator = User.objects.get(id=request.session['REQUIRED_FIELDS'][1])
            student = Students.objects.filter(sid=request.session['REQUIRED_FIELDS'][1])
            if not student:
                return JsonResponse({'ret': 1, 'msg': '请在个人信息处选择你的老师'})
            currentstate = '主题已创建'
            if key == 'create_topic':
                user = User.objects.get(id=int(request.session['REQUIRED_FIELDS'][1]))
                title = submitdata[0]['value']
                workflow = Workflow.objects.create(user=user, currentstate=currentstate, title=title)
                actionname = '创建主题'
            else:
                workflow = Workflow.objects.get(id=request.params['wf_id'])
                actionname = '修改主题'
                workflow.title = submitdata[0]['value']
                workflow.currentstate = currentstate
                workflow.save()
            nextstate = '主题已创建'
            name = submitdata[1]['name']
            type = submitdata[1]['type']
            value = submitdata[1]['value']
            Workstep.objects.create(workflow=workflow, operator=opreator, actionname=actionname, nextstate=nextstate,
                                    name=name, type=type, value=value)
            return JsonResponse({'ret': 0, 'wf_id': workflow.id})
        # 根据key值的不同，actionname和nextstate需要额外处理
        elif key in ['reject_topic', 'approve_topic', 'change_topic', 'write_data', 'over']:
            opreator = User.objects.get(id=request.session['REQUIRED_FIELDS'][1])
            wf_id = request.params['wf_id']
            submitdata = request.params['submitdata']
            workflow = Workflow.objects.get(id=wf_id)
            name = submitdata[0]['name']
            type = submitdata[0]['type']
            value = submitdata[0]['value']
            if key == 'reject_topic':
                actionname = '驳回主题'
                nextstate = '主题被驳回'
            elif key == 'approve_topic':
                actionname = '批准主题'
                nextstate = '主题已通过'
            elif key == 'change_topic':
                actionname = '修改主题'
                nextstate = '主题已修改'
            elif key == 'write_data':
                actionname = '提交毕业设计'
                nextstate = '学生已提交毕业设计'
            elif key == 'over':
                actionname = '评分'
                nextstate = '结束'
            else:
                return JsonResponse({'ret': 1, 'msg': '没有这种key'})
            # 根据下一个状态修改workflow中的currentstate值
            workflow.currentstate = nextstate
            workflow.save()
            # 创建一个workstep
            Workstep.objects.create(workflow=workflow, operator=opreator, actionname=actionname, nextstate=nextstate,
                                    name=name, type=type, value=value)
            return JsonResponse({'ret': 0, 'wf_id': workflow.id})
        else:
            return JsonResponse({'ret': 1, 'msg': '发生了未知错误'})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '发生了未知错误'})


def getstepactiondata(request):
    try:
        # 根据ID查找对应的work_data,并返回所需值
        step_id = request.params['step_id']
        data = Workstep.objects.filter(id=step_id).values('name', 'type', 'value')
        return JsonResponse({'ret': 0, 'data': list(data)})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '发生了未知错误'})