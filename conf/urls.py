"""tbia URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from django.conf import settings
from django.conf.urls.static import static
# from ckeditor_uploader import views as ckeditor_views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('', include('data.urls')),
    path('', include('manager.urls')),
    path('', include('api.urls')),
    # path('ckeditor/upload/', login_required(ckeditor_views.upload), name='ckeditor_upload'),
    # path('ckeditor/', include('ckeditor_uploader.urls')),
    path('accounts/', include('allauth.urls')),  # django-allauth網址
    path("robots.txt",TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "pages.views.page_not_found_view"
handler500 = "pages.views.error_view"
