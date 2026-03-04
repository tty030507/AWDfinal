"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from main_app.views import index_view, logout_view # 确保导入这两个

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main_app.urls')), # 所有的接口都在这里
    
    # 所有的页面路径都指向同一个 index_view
    path('', index_view, name='index'), 
    path('home/', index_view, name='home'),
    path('login/', index_view, name='login'),
    path('register/', index_view, name='register'),
    
    # 注销逻辑
    path('logout/', logout_view, name='logout'),
    
    # 1. 自动生成 OpenAPI Schema (JSON 格式) 
   
    path('apischema/', get_schema_view(
        title="eLearning API",
        description="Final Coursework eLearning App API",
        version="1.0.0"
    ), name='openapi-schema'),

    # 2. Swagger 交互式文档界面 (Rubric 加分项) 
    path('docs/', TemplateView.as_view(
        template_name='swagger-docs.html',
        extra_context={'schema_url': 'openapi-schema'}
    ), name='swagger-ui'),
]

# 必须添加这个才能在开发环境下通过 URL 访问上传的教材和照片 [cite: 2507]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)