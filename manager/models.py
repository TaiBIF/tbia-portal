from pyexpat import model
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import django

# Create your models here.



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

# partner_choice = [
#     ('none', '無'),
#     ('taibif', 'TaiBIF'),
#     ('tesri', '特生中心'),
#     ('tfri', '林試所'),
#     ('oca', '海保署'),
#     ('cpami', '營建署'),
#     ('forest', '林務局'),
#     ('tbia', 'TBIA'),
# ]

class Partner(models.Model):
    breadtitle = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True) # 在網頁上呈現在一起
    group = models.CharField(max_length=100, null=True, blank=True) # 後台group
    title = models.CharField(max_length=100, null=True, blank=True)
    # subtitle = models.CharField(max_length=100, null=True, blank=True)
    # description = models.TextField(null=True, blank=True)
    # link = models.TextField(null=True, blank=True)
    # image = models.TextField(null=True, blank=True)
    # logo = models.TextField(null=True, blank=True)
    info = models.JSONField(null=True, blank=True)
    created = models.DateField(auto_now_add=True)
    modifed = models.DateField(auto_now_add=True)
    class Meta:
        db_table = 'partner'


class User(AbstractUser):
    name = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=254, blank=False, unique=True)
    is_active = models.BooleanField(default=True)
    # is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=True)
    first_login = models.BooleanField(default=True)

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True)

    # role_choice = [
    #     ('gu', '一般使用者'),
    #     ('uu', '單位帳號'),
    #     ('ua', '單位管理員'),
    #     ('sa', '系統管理員'),
    #     ('de', '開發者/superuser'),
    # ]
    # role = models.CharField(
    #     max_length=2,
    #     choices=role_choice,
    #     default='gu',
    # )
    is_partner_account = models.BooleanField(default=False)
    is_partner_admin = models.BooleanField(default=False)
    is_system_admin = models.BooleanField(default=False)

    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'tbia_user'


class PartnerRequest(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, blank=True) # pending, pass, fail 
    created = models.DateField(auto_now_add=True) # 申請時間
    # 如果該帳號只剩下fail，開放再申請


class SearchQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.TextField(null=True, blank=True)
    download_times = models.IntegerField(default=0)
    created = models.DateField(auto_now_add=True)


class About(models.Model):
    content = models.TextField(null=True, blank=True)
    created = models.DateField(auto_now_add=True)



# class DownloadStat(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     query = models.TextField(null=True, blank=True)
#     created = models.DateField(auto_now_add=True)



