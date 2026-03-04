from rest_framework import viewsets, status, permissions, filters # 增加 filters
from rest_framework.decorators import action
from .tasks import send_notification_task
from rest_framework.response import Response
from django.db.models import Q  # <--- 添加这一行
from .models import User, Course, CourseMaterial, StatusUpdate, Feedback,Notification,ChatMessage

from .serializers import (

    UserSerializer, CourseSerializer, CourseMaterialSerializer,NotificationSerializer,

    StatusUpdateSerializer, FeedbackSerializer,ChatMessageSerializer

)

from django.shortcuts import render, redirect

from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.forms import AuthenticationForm

from .forms import CustomUserCreationForm

# 导入你稍后要写的 Celery 任务

# from .tasks import send_notification_task
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


# 1. 用户视图集 (Requirement R4)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # 增加搜索过滤器
    filter_backends = [filters.SearchFilter]
    # 定义可以被搜索的字段：用户名和真实姓名
    search_fields = ['username', 'real_name']



# 2. 课程视图集 (包含选课和权限逻辑)

class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # 如果是老师，只返回他自己创建的课程
        if user.user_type == 'teacher':
            return Course.objects.filter(teacher=user)
        # 如果是学生，返回所有可选课程
        return Course.objects.all()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    # 学生选课逻辑 (Requirement R1-e)
    @action(detail=True, methods=['post'])
    def enrol(self, request, pk=None):
        course = self.get_object()
        user = request.user
        
        # 核心权限检查：判断用户类型 [cite: 10, 61]
        if user.user_type != 'student':
            return Response(
                {'detail': 'Permission Denied: Only students can enrol in courses.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 防止重复选课
        if course.students.filter(id=user.id).exists():
            return Response({'detail': 'You are already enrolled.'}, status=400)

        course.students.add(user)
        
        # 触发 Celery 异步通知老师 (Requirement R1-k) [cite: 68]
        
        send_notification_task.delay(course.teacher.id, f"Student : {request.user.real_name} joined your course : {course.title}")
        return Response({'status': 'Enrolled'})
        
        return Response({'status': 'Enrolled successfully'}, status=status.HTTP_200_OK)
    @action(detail=True, methods=['post'])
    def remove_student(self, request, pk=None):
        course = self.get_object()
        student_id = request.data.get('student_id')
        
        # 权限检查：只有该课的老师可以移除学生 [cite: 11, 19]
        if course.teacher != request.user:
            return Response({'detail': 'No permission'}, status=403)
            
        try:
            student = User.objects.get(id=student_id, user_type='student')
            course.students.remove(student)
            send_notification_task.delay(student.id, f"You have been removed from course : {course.title}")
            return Response({'status': f' {student.real_name} is removed'})
        except User.DoesNotExist:
            return Response({'detail': 'Student not exist'}, status=404)


# 3. 教材上传视图集 (Requirement R1-j)

class CourseMaterialViewSet(viewsets.ModelViewSet):
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        material = serializer.save()
        course = material.course
        student_ids = list(course.students.values_list('id', flat=True))
        
        # --- 异步通知所有选课学生 ---
        if student_ids:
            send_notification_task.delay(student_ids, f"Course :  {course.title} has uploaded a new learning material : {material.title}")



# 4. 状态更新视图集 (Requirement R1-i)

# views.py
class StatusUpdateViewSet(viewsets.ModelViewSet):
    serializer_class = StatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 满足需求：HomePage 只显示属于自己的状态历史
        return StatusUpdate.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



# 5. 反馈视图集 (Requirement R1-f)

class FeedbackViewSet(viewsets.ModelViewSet):

    queryset = Feedback.objects.all()

    serializer_class = FeedbackSerializer



    def perform_create(self, serializer):

        instance = serializer.save(student=self.request.user)
        send_notification_task.delay(instance.course.teacher.id, f"You received a new feedback on course :  {instance.course.title}")


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 核心：只返回当前登录用户的通知，并按时间倒序排列
        
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    @action(detail=False, methods=['post'], url_path='triggertask')
    def trigger_task(self, request):
        recipient_id = request.data.get('recipient')
        message = request.data.get('message')
        
        if recipient_id and message:
            # 直接触发 Celery 任务进行实时推送
            send_notification_task.delay([recipient_id], message)
            return Response({'status': 'Task triggered successfully'}, status=200)
        
        return Response({'error': 'Missing recipient or message'}, status=400)
        
# 1. 登录 API (供 React 使用)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    
    if user is not None:
        login(request, user)
        return Response({
            'status': 'success',
            'user': UserSerializer(user, context={'request': request}).data
        })
    return Response({'status': 'error', 'message': '用户名或密码错误'}, status=400)

# 2. 注册 API (供 React 使用)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    # 使用你之前的 CustomUserCreationForm 逻辑，但返回 JSON
    form = CustomUserCreationForm(request.data, request.FILES)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return Response({
            'status': 'success', 
            'user': UserSerializer(user, context={'request': request}).data
        })
    return Response({'status': 'error', 'errors': form.errors}, status=400)

# 3. 获取当前用户信息的 API (React 初始化时调用)
@api_view(['GET'])
def get_current_user(request):
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    return Response({'detail': '未登录'}, status=401)

# 4. 获取 CSRF Token 的接口 (React 需要它来发送 POST 请求)


def index_view(request):
    # 无论是否登录，都返回 index.html
    # React 的 App.js 会在 useEffect 里自动检查登录状态并决定显示哪个页面
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    # 返回到首页，让 React 重新加载
    return redirect('index')


# main_app/views.py

class ChatHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        recipient_id = self.request.query_params.get('recipient_id')
        if not recipient_id:
            return ChatMessage.objects.none()
        
        # 获取当前用户和对方之间的双向聊天记录
        return ChatMessage.objects.filter(
            Q(sender=user, recipient_id=recipient_id) | 
            Q(sender_id=recipient_id, recipient=user)
        ).order_by('timestamp')