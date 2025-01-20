from django.db import models
from manager.models import User, Partner


# 限制型API key
class APIkey(models.Model): 

    status_choice = [
        # ('pending', '等待審核'),
        ('pass', '通過'),
        # ('fail', '不通過'),
        ('expired', '過期'),
    ]

    key = models.CharField(max_length=100, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=status_choice,max_length=20, blank=True) 
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    applicant =  models.CharField(max_length=100, blank=True) # 申請者姓名
