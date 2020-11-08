from django.http import JsonResponse


def dispatcher(request):
    # 处理图片下载
    # 图片上传肯定是POST请求
    if request.method != 'POST':
        return JsonResponse({"ret": 1, 'mag': '上传图片只支持POST请求'})
    # 根据FILES函数得到图片对象，其中小于2.5M的为InMeoryUploadedFile,大于2.5M的为TemporaryUploadedFile
    pic = request.FILES.get('upload1')
    # 检查图片名字最后三位是否符合规定
    if pic.name[-3:] != 'png' and pic.name[-3:] != 'jpg':
        return JsonResponse({"ret": 1, 'msg': '请上传png或jpg格式图片'})
    # 根据图片名字设置存储path,由于前端原因，图片只能保存在前端z_dist文件夹下，不然显示不出来QAQ
    save_path = '../CIMP/frontend/z_dist/upload/%s'%(pic.name)
    try:
        # 打开文件，通过chunks函数进行存储
        with open(save_path, 'wb')as f:
            for content in pic.chunks():
                f.write(content)
        return JsonResponse({'ret': 0, 'url': '/upload/%s'%(pic.name)})
    except Exception as e:
        print(e)
        return JsonResponse({'ret': 1, 'msg': '未知错误'})