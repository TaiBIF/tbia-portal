from django.db import models
from django.db.models.fields import TextField
from account.models import User, Unit


class News(models.Model):
    type_choice = [
        ('news', '新聞公告'),
        ('event', '活動訊息'),
        ('project', '計畫徵求'),
    ]
    type = models.CharField(max_length=10, choices=type_choice, blank=True, null=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    unit_id = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1000, blank=True, null=True)
    content = models.TextField( blank=True, null=True)
    image = models.TextField( blank=True, null=True)
    attachments = models.TextField( blank=True, null=True)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now_add=True)
    class Meta:
        db_table = 'news'


class Resource(models.Model):
    type_choice = [
        ('strategy', 'TBIA策略文件'),
        ('guide', '開放資料指引'),
        ('tool', '參考文件&工具'),
        ('tutorial', '教學文件'),
    ]
    type = models.CharField(max_length=10, choices=type_choice, blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    url = models.CharField(max_length=1000, blank=True, null=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    unit_id = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now_add=True)
    class Meta:
        db_table = 'resource'


class Feedback(models.Model):
    unit_id = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    content = TextField(null=True, blank=True)
    is_replied = models.BooleanField(default=False)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateField(auto_now_add=True)
    replied = models.DateField()
    class Meta:
        db_table = 'feedback'


class Notification(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    unit_id = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created = models.DateField(auto_now_add=True)
    notified = models.DateField(auto_now_add=True)
    content = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'notification'


class Download(models.Model):
    file = models.CharField(max_length=1000, blank=True, null=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    unit_id = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    submitted = models.DateField(auto_now_add=True)
    expired = models.DateField()
    class Meta:
        db_table = 'download'
