# from pyexpat import model
# from xml.dom.minidom import Comment
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
# import django


# NOTE 資料庫存的時間統一都是 UTC + 0

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
            register_method=kwargs['register_method'],
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
    # breadtitle = models.CharField(max_length=100, null=True, blank=True)
    # breadtitle_en = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True) # 在網頁上夥伴頁面呈現在一頁
    group = models.CharField(max_length=100, null=True, blank=True) # 後台group
    select_title = models.CharField(max_length=100, null=True, blank=True) # 在網頁上夥伴頁面呈現在一頁(同個MOU簽署單位) 但後台是分開的 在前台顯示需區分
    select_title_en = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    title_en = models.CharField(max_length=100, null=True, blank=True)
    logo = models.TextField(null=True, blank=True)
    info = models.JSONField(null=True, blank=True) 
    # ['id', 'link', 'image', 'subtitle', 'description', 'dbname', 'color'] 
    # 'subtitle' 在夥伴頁面上呈現的資料庫名稱
    # 'subtitle_en' 在夥伴頁面上呈現的英文資料庫名稱
    # 'dbname' 在進階搜尋下拉選單對應的資料庫名稱，在資料內同樣也存這個名字 (=rightsHolder)
    # 'color' 後台圓餅圖使用的顏色
    index_order = models.IntegerField(null=True, blank=True) # 在首頁的順序
    # 正式會員顯示順序: brcas 1, forest 2, tbri 3, tfri 4, oca 5, nps 6, ntm 7, wra 8
    # 合作夥伴顯示順序: 

    is_collaboration = models.BooleanField(default=False) # 是否為合作夥伴

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
    register_method = models.CharField(max_length=20, blank=True) # portal, google

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
    # is_collaboration_account = models.BooleanField(default=False)
    # is_collaboration_admin = models.BooleanField(default=False)

    status = models.CharField(choices=status_choice,max_length=20, blank=True) # pending, pass, fail 

    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'tbia_user'


class SearchStat(models.Model):
    location_choice = [
        ('full', '全站搜尋'),
        ('occ', '物種出現紀錄進階搜尋'),
        ('col', '自然史典藏進階搜尋'),
        ('api_occ', '物種出現紀錄API'),
    ]
    search_location = models.CharField(choices=location_choice,max_length=20, blank=True) 
    query = models.TextField(null=True, blank=True)
    stat = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)


# API 請求次數
class SearchCount(models.Model):
    location_choice = [
        # ('full', '全站搜尋'),
        # ('occ', '物種出現紀錄進階搜尋'),
        # ('col', '自然史典藏進階搜尋'),
        ('api_occ', '物種出現紀錄API'),
    ]
    search_location = models.CharField(choices=location_choice,max_length=20, blank=True) 
    count = models.IntegerField(default=0)
    # created = models.DateTimeField(auto_now_add=True)


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
    # 使用者個人下載編號id
    personal_id = models.IntegerField(null=True, blank=True)
    stat = models.JSONField(null=True, blank=True)


class SensitiveDataRequest(models.Model):
    # 用query_id和SearchQuery串接

    type_choice = [
        ('0', '個人研究計畫'),
        ('1', '委辦工作計畫'),
    ]

    applicant =  models.CharField(max_length=100, blank=True)
    phone =  models.CharField(max_length=100, blank=True)
    address =  models.CharField(max_length=100, blank=True)
    affiliation =  models.CharField(max_length=100, blank=True)
    job_title =  models.CharField(max_length=100, blank=True)
    project_name =  models.CharField(max_length=1000, blank=True)
    project_affiliation =  models.CharField(max_length=1000, blank=True)
    type = models.CharField(choices=type_choice, max_length=20, blank=True)
    users = models.JSONField(null=True, blank=True) # 資料使用者
    abstract = models.TextField(null=True, blank=True)
    is_agreed_report = models.BooleanField(default=False) # 是否同意提供研究成果
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
    is_partial_transferred = models.BooleanField(default=False)


class About(models.Model):
    content = models.TextField(null=True, blank=True)
    content_en = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)


# 工作日
class Workday(models.Model):
    # '西元日期','是否放假'
    date = models.DateField(blank=True, null=True)
    is_dayoff = models.BooleanField(default=False)


# 每月關鍵字統計
class KeywordStat(models.Model):
    keyword = models.TextField(null=True, blank=True)
    count = models.IntegerField(null=True, blank=True)
    year_month = models.CharField(max_length=1000, null=True, blank=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)


# 資料 物種類群 / 科別 統計
class TaxonStat(models.Model):
    type_choice = [
        ('taxon_group', '物種類群'),
        ('family', '科別'),
    ]
    type = models.CharField(choices=type_choice,max_length=20, blank=True, db_index=True)
    group = models.CharField(max_length=100, null=True, blank=True, db_index=True) # 後台group
    rights_holder = models.CharField(max_length=100, null=True, blank=True, db_index=True) # 來源資料庫
    year_month = models.CharField(max_length=1000, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=10000, null=True, blank=True)  # 類群名 / 科名
    count = models.IntegerField(null=True, blank=True)
    modified = models.DateTimeField(auto_now_add=True)


# 資料數量統計 
class DataStat(models.Model):
    type_choice = [
        ('data', '累積資料數量'),
        ('search', '累積被查詢資料數量'),
        ('download', '累積被下載資料數量'),
    ]
    type = models.CharField(choices=type_choice,max_length=20, blank=True, db_index=True)
    group = models.CharField(max_length=100, null=True, blank=True, db_index=True) # 後台group
    rights_holder = models.CharField(max_length=100, null=True, blank=True, db_index=True) # 來源資料庫
    year_month = models.CharField(max_length=1000, null=True, blank=True, db_index=True)
    count = models.CharField(max_length=10000, null=True, blank=True)  # 數字太大 改用string
    created = models.DateTimeField(auto_now_add=True)


# 名錄下載統計
class ChecklistStat(models.Model):
    year_month = models.CharField(max_length=1000, null=True, blank=True, db_index=True)
    count = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
