from django.urls import path
from api import sign, account, notice, news, paper, config, upload, etc, wf_graduatedesign
urlpatterns = [
    # 根据二级路由，返回对应的函数
    path('sign', sign.sign_in_out),
    path('account', account.dispatcher),
    path('notice', notice.dispatcher),
    path('news', news.dispatcher),
    path('paper', paper.dispatcher),
    path('config', config.dispatcher),
    path('upload', upload.dispatcher),
    path('etc', etc.dispatcher),
    path('wf_graduatedesign', wf_graduatedesign.dispatcher),
]