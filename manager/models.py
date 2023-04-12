from pyexpat import model
from xml.dom.minidom import Comment
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import django


class UserManager(BaseUserManager):
    def create_user(self, email, **kwargs):
        """
        Creates and saves a User with the given email (email)
        """
        user = self.model(
            email=self.normalize_email(email),
            name=kwargs['name'],
            is_email_verified=kwargs['is_email_verified'],
            is_active=kwargs['is_active'],
        )
        user.set_password(kwargs['password'])
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        """
        Creates and saves a superuser with the given email (email) and password
        """
        user = self.model(
            email=self.normalize_email(email),
            # first_name=kwargs['first_name'],
            # last_name=kwargs['last_name'],
        )
        user.set_password(password)
        user.is_superuser = True
        user.is_email_verified = True
        user.is_staff = True
        user.is_active = True
        user.role = 'de'
        user.save(using=self._db)
        return user


class Partner(models.Model):
    breadtitle = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True) # 在網頁上呈現在一起
    group = models.CharField(max_length=100, null=True, blank=True) # 後台group
    title = models.CharField(max_length=100, null=True, blank=True)
    logo = models.TextField(null=True, blank=True)
    info = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modifed = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'partner'


class User(AbstractUser):
    name = models.CharField(max_length=1000, blank=True)
    email = models.EmailField(max_length=254, blank=False, unique=True)
    is_active = models.BooleanField(default=True)
    # is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=True)
    first_login = models.BooleanField(default=True)

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True)
    
    
    status_choice = [
        ('pending', '等待審核'),
        ('pass', '通過'),
        ('fail', '不通過'),
        ('withdraw', '撤回'),
    ]

    is_partner_account = models.BooleanField(default=False)
    is_partner_admin = models.BooleanField(default=False)
    is_system_admin = models.BooleanField(default=False)
    status = models.CharField(choices=status_choice,max_length=20, blank=True) # pending, pass, fail 

    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'tbia_user'


class SearchQuery(models.Model):
    status_choice = [
        ('pending', '處理中'),
        ('pass', '完成'),
        ('fail', '失敗'),
        ('expired', '過期'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.TextField(null=True, blank=True)
    # download_times = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(null=True, blank=True)
    status = models.CharField(choices=status_choice,max_length=20, blank=True) # pending, pass, fail 
    type = models.CharField(max_length=20, blank=True) # taxon, record, sensitive
    query_id = models.CharField(max_length=50, blank=True)


class SensitiveDataRequest(models.Model):
    # 用query_id和SearchQuery串接

    type_choice = [
        (0, '個人研究計畫'),
        (1, '委辦工作計畫'),
    ]

    applicant =  models.CharField(max_length=100, blank=True)
    phone =  models.CharField(max_length=100, blank=True)
    address =  models.CharField(max_length=100, blank=True)
    affiliation =  models.CharField(max_length=100, blank=True)
    project_name =  models.CharField(max_length=1000, blank=True)
    project_affiliation =  models.CharField(max_length=1000, blank=True)
    type = models.CharField(choices=type_choice, max_length=20, blank=True)
    users = models.JSONField(null=True, blank=True) # 資料使用者
    abstract = models.TextField(null=True, blank=True)
    # status = models.CharField(choices=status_choice, max_length=20, blank=True) # pending, pass, fail 這邊是集合各單位的回覆
    created = models.DateTimeField(auto_now_add=True) # 申請時間
    query_id = models.CharField(max_length=50, blank=True)



# 單位意見回覆
class SensitiveDataResponse(models.Model):
    # 用query_id和SearchQuery串接
    # 每個單位為一筆
    status_choice = [
        ('pending', '等待審核'),
        ('pass', '通過'),
        ('fail', '不通過'),
    ]

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True) # 若空值則為秘書處
    reviewer_name = models.CharField(max_length=1000, blank=True)
    comment = models.TextField(null=True, blank=True)
    status = models.CharField(choices=status_choice,max_length=20, blank=True) # pending, pass, fail 
    query_id = models.CharField(max_length=50, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(null=True, blank=True)
    is_transferred = models.BooleanField(default=False)


class About(models.Model):
    content = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)


class MatchLog(models.Model):
    occurrenceID = models.CharField(max_length=1000, blank=True)
    tbiaID = models.CharField(max_length=50, blank=True)
    sourceScientificName = models.CharField(max_length=1000, blank=True, null=True)
    is_matched = models.BooleanField()
    taxonID = models.CharField(max_length=20, blank=True, null=True)
    parentTaxonID = models.CharField(max_length=20, blank=True, null=True)
    match_stage = models.CharField(max_length=5, blank=True, null=True)
    stage_1 = models.CharField(max_length=20, blank=True, null=True)
    stage_2 = models.CharField(max_length=20, blank=True, null=True)
    stage_3 = models.CharField(max_length=20, blank=True, null=True)
    stage_4 = models.CharField(max_length=20, blank=True, null=True)
    stage_5 = models.CharField(max_length=20, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(null=True, blank=True)
