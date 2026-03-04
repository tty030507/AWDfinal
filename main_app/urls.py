# main_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, CourseViewSet, CourseMaterialViewSet, 
    StatusUpdateViewSet, FeedbackViewSet,NotificationViewSet,ChatHistoryViewSet,
    login_api, register_api, get_current_user
    # index_view 挪到 core 去了，这里不需要
)

router = DefaultRouter()
router.register(r'users', UserViewSet)

# 1. 修复 Course 路由
router.register(r'courses', CourseViewSet, basename='course') 

# 2. 修复 Materials 路由（建议也加上以防万一）
router.register(r'materials', CourseMaterialViewSet, basename='material')

# 3. 关键修复：修复 Updates 路由，因为它在 views 里也没写 queryset 属性
router.register(r'updates', StatusUpdateViewSet, basename='status-update') 

# 4. 修复 Feedback 路由
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'notifications', NotificationViewSet, basename='notification') # 必须有这一行
router.register(r'chathistory', ChatHistoryViewSet, basename='chat-history')
urlpatterns = [
    # 所有的 API 路径
    path('', include(router.urls)), 
    path('login/', login_api, name='login_api'),
    path('register/', register_api, name='register_api'),
    path('me/', get_current_user, name='current_user'),
]