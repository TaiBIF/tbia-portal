from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import django

# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, username, **kwargs):
        """
        Creates and saves a User with the given email (username)
        """
        user = self.model(
            username=self.normalize_email(username),
            first_name=kwargs['first_name'],
            last_name=kwargs['last_name'],
        )

        # user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **kwargs):
        """
        Creates and saves a superuser with the given email (username) and password
        """
        user = self.model(
            username=self.normalize_email(username),
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



class User(AbstractUser):
    first_name = models.CharField(max_length=20, blank=True)
    last_name = models.CharField(max_length=20, blank=True)
    username = models.EmailField(max_length=254, blank=False, unique=True)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email = None

    unit_choice = [
        ('none', '無'),
        ('taibif', 'TaiBIF'),
        ('tesri', '特生中心'),
        ('tfri', '林試所'),
        ('oca', '海保署'),
        ('cpami', '營建署'),
        ('forest', '林務局'),
        ('tbia', 'TBIA'),
    ]
    unit = models.CharField(
        max_length=20,
        choices=unit_choice,
        default='none'
    )

    role_choice = [
        ('gu', '一般使用者'),
        ('uu', '單位帳號'),
        ('ua', '單位管理員'),
        ('sa', '系統管理員'),
        ('de', '開發者/superuser'),
    ]
    role = models.CharField(
        max_length=2,
        choices=role_choice,
        default='gu',
    )

    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'tbia_user'


class Partner(models.Model):
    breadtitle = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    subtitle = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    link = models.TextField(null=True, blank=True)
    image = models.TextField(null=True, blank=True)
    logo = models.TextField(null=True, blank=True)
    created = models.DateField(auto_now_add=True)
    modifed = models.DateField(auto_now_add=True)
    class Meta:
        db_table = 'partner'