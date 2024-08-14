from django.db import models
from django.db.models.fields import TextField
from manager.models import User, Partner
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField


class Keyword(models.Model):
    lang_choice = [
        ('en-us', '英文'),
        ('zh-hant', '中文'),
    ]
    keyword = models.TextField( blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    lang = models.CharField(max_length=10, choices=lang_choice, blank=True, null=True)
    # created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now_add=True)
    class Meta:
        db_table = 'keyword'


class News(models.Model):
    type_choice = [
        ('news', '新聞公告'),
        ('event', '活動訊息'),
        ('project', '徵求公告'),
        ('datathon', '數據松成果'),
    ]
    status_choice = [
        ('pending', '等待審核'),
        ('pass', '通過'),
        ('fail', '不通過'),
        ('withdraw', '撤回'),
    ]
    lang_choice = [
        ('en-us', '英文'),
        ('zh-hant', '中文'),
    ]
    type = models.CharField(max_length=10, choices=type_choice, blank=True, null=True)
    lang = models.CharField(max_length=10, choices=lang_choice, default='zh-hant') # en-us, zh-hant
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    author_use_tbia = models.BooleanField(default=False, null=True, blank=True) # 夥伴單位發布 但作者顯示TBIA秘書處
    title = models.CharField(max_length=1000, blank=True, null=True)
    # content = RichTextUploadingField( blank=True, null=True)
    content = RichTextField(blank=True, null=True)
    image = models.TextField( blank=True, null=True)
    status = models.CharField(choices=status_choice, max_length=20, blank=True) # pending, pass, fail, withdraw
    # attachments = models.TextField( blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)
    publish_date = models.DateField(null=True, blank=True) # 使用者自定義 不管時區
    order = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = 'news'


class Link(models.Model): # 推薦連結
    content = RichTextUploadingField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'link'


class Resource(models.Model):
    type_choice = [
        ('strategy', 'TBIA策略文件'),
        ('guide', '開放資料指引'),
        ('tool', '參考文件&工具'),
        ('tutorial', '教學文件'),
    ]
    lang_choice = [
        ('en-us', '英文'),
        ('zh-hant', '中文'),
    ]
    type = models.CharField(max_length=10, choices=type_choice, blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    lang = models.CharField(max_length=10, choices=lang_choice, blank=True, null=True) # en-us, zh-hant
    extension = models.CharField(max_length=10, blank=True, null=True)
    url = models.CharField(max_length=1000, blank=True, null=True)
    doc_url = models.CharField(max_length=1000, blank=True, null=True) # TBIA 文件網站網址
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now_add=True) # 已經是UTF+8
    publish_date = models.DateField(null=True, blank=True) # 使用者自定義 不管時區
    class Meta:
        db_table = 'resource'


class Feedback(models.Model):

    type_choice = [
        (1,'網頁操作'),
        (2,'網頁內容'),
        (3,'聯盟相關'),]
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.IntegerField(choices=type_choice,blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    content = TextField(null=True, blank=True)
    is_replied = models.BooleanField(default=False)
    # user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    # replied = models.DateField()
    class Meta:
        db_table = 'feedback'


class Notification(models.Model):
    type_choice = [
        (0,'下載名錄編號 #0000 已處理完成，請至後台查看'),
        (1,'下載資料編號 #0000 已處理完成，請至後台查看'),
        (2,'有新的意見回饋 #0000，請至後台查看'),
        (3,'有新的單次使用敏感資料申請 #0000，請至後台審核'),
        (4,'單次使用敏感資料申請編號 #0000 審核已完成，請至後台查看'),
        (5,'有新的單位帳號 #0000 申請，請至後台審核'),
        (6,'申請單位帳號審核已完成，結果為：0000'),
        (7,'有新的消息 #0000 發布申請，請至後台審核'),
        (8,'消息 #0000 發布審核已完成，請至後台查看')]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=100, null=True, blank=True)
    type = models.IntegerField(null=True, blank=True, choices=type_choice)
    class Meta:
        db_table = 'notification'


class Qa(models.Model):

    type_choice = [
        (1,'網頁操作'),
        (2,'網頁內容'),
        (3,'聯盟相關'),]
    type = models.IntegerField(choices=type_choice,blank=True, null=True)
    question = TextField(null=True, blank=True)
    question_en = TextField(null=True, blank=True)
    answer = TextField(null=True, blank=True)
    answer_en = TextField(null=True, blank=True)
    order = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = 'qa'
