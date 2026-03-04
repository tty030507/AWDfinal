from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
# 1. 自定义用户模型
class User(AbstractUser):
    # 定义身份类型选项
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    
    # 使用 user_type 字段区分身份
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        default='student'
    )
    
    real_name = models.CharField(max_length=100)
    # 个人 profile 的照片
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)

    # 注：username, password, email 已经由 AbstractUser 自动包含了，不需要重复写出来
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"

# 2. 课程模型
class Course(models.Model):
    # 关联老师：这里可以加一个限制，确保只有 teacher 类型的用户能被关联
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_courses',
        limit_choices_to={'user_type': 'teacher'} 
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    # 关联学生
    students = models.ManyToManyField(
        User, 
        related_name='enrolled_courses', 
        blank=True,
        limit_choices_to={'user_type': 'student'}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# 3. 课程材料模型 (支持 PDF、图像等)
class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    # 新增下面这一行，用来存储文件的标题/名称
    title = models.CharField(max_length=255, default="Untitled Material") 
    file = models.FileField(upload_to='course_materials/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# 4. 状态更新模型 (用于用户 Home 页面)
class StatusUpdate(models.Model):
    # 只有学生会发布状态更新 (Requirement R1-i)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='updates',
        limit_choices_to={'user_type': 'student'}
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# 5. 课程反馈模型
class Feedback(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='feedbacks')
    # 只有学生能留下反馈 (Requirement R1-j)
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'student'}
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False) # 重点：用来标记用户是否看过了
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# main_app/models.py

class ChatMessage(models.Model):
    # 记录谁发的，发给谁
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp'] # 按时间顺序排列

    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.message[:20]}"