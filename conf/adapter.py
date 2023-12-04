from django.contrib.auth import get_user_model
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login

usermodel = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin): 
        user = sociallogin.user
        if user.id:  #Already linked
            return          
        try:
            UserObj = usermodel.objects.get(email=user.email)  # if user exists, connect the account to the existing account and login
            sociallogin.state['process'] = 'connect'                
            perform_login(request, UserObj, 'none')
        except usermodel.DoesNotExist:
            pass
