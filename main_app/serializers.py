# main_app/serializers.py
from rest_framework import serializers
from .models import User, Course, CourseMaterial, StatusUpdate, Feedback,Notification,ChatMessage

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'real_name', 'user_type']

class FeedbackSerializer(serializers.ModelSerializer):
    # 嵌套显示学生姓名和提交时间 
    student_name = serializers.ReadOnlyField(source='student.real_name')
    class Meta:
        model = Feedback
        fields = ['id', 'course', 'student', 'student_name', 'content', 'created_at']
        read_only_fields = ['student']
class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        # 这里的字段现在和模型一一对应了
        fields = ['id', 'course', 'title', 'file', 'uploaded_at']

class CourseSerializer(serializers.ModelSerializer):
    # 嵌套教材和反馈列表 [cite: 66, 67]
    materials = CourseMaterialSerializer(many=True, read_only=True)
    feedbacks = FeedbackSerializer(many=True, read_only=True)
    students_details = UserSerializer(source='students', many=True, read_only=True)
    teacher_name = serializers.ReadOnlyField(source='teacher.real_name')

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'teacher', 'teacher_name', 'students', 'students_details', 'materials', 'feedbacks']
        read_only_fields = ['teacher', 'students']
# 4. 状态更新 Serializer (用于 Home Page 动态 [cite: 2357, 2359])
class StatusUpdateSerializer(serializers.ModelSerializer):
    # 自动获取当前登录用户
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = StatusUpdate
        fields = ['id', 'user', 'content', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient','message', 'is_read', 'created_at']

# main_app/serializers.py

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.real_name')
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'sender_name', 'recipient', 'message', 'timestamp']