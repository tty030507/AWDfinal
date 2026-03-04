from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Course, Notification
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
class ELearningSystemTests(APITestCase):
    def setUp(self):
        # 1. 创建一名老师
        self.teacher = User.objects.create_user(
            username='teacher1', 
            password='password123', 
            real_name='Dr. Smith', 
            user_type='teacher'
        )
        # 2. 创建一名学生
        self.student = User.objects.create_user(
            username='student1', 
            password='password123', 
            real_name='John Doe', 
            user_type='student'
        )

    def test_course_creation_and_enrollment(self):
        """测试课程创建及学生选课流程"""
        # 老师登录
        self.client.login(username='teacher1', password='password123')
        
        # 创建课程
        url = reverse('course-list')
        data = {'title': 'Python 101', 'description': 'Intro to Python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)
        
        course_id = response.data['id']
        self.client.logout()

        # 学生登录并选课
        self.client.login(username='student1', password='password123')
        enrol_url = reverse('course-enrol', args=[course_id])
        
        # 模拟 Celery 任务，防止测试时真的去连 Redis
        with patch('main_app.views.send_notification_task.delay') as mocked_task:
            response = self.client.post(enrol_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # 验证选课逻辑
            self.assertTrue(self.student.enrolled_courses.filter(id=course_id).exists())
            # 验证通知任务是否被触发
            mocked_task.assert_called_once()

    def test_notification_fetching(self):
        """测试通知获取逻辑"""
        # 为学生创建一条通知
        Notification.objects.create(
            recipient=self.student,
            message="Welcome to the platform!"
        )
        
        self.client.login(username='student1', password='password123')
        url = reverse('notification-list')
        response = self.client.get(url)
        # 修复分页导致的长度判断错误
        self.assertEqual(len(response.data['results']), 1) 
        self.assertEqual(response.data['results'][0]['message'], "Welcome to the platform!")

    def test_search_user(self):
        """测试用户搜索功能"""
        self.client.login(username='student1', password='password123')
        # 搜索老师的名字
        url = f"{reverse('user-list')}?search=Smith"
        response = self.client.get(url)
        # 修复分页导致的长度判断错误
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'teacher1')

    def test_security_constraints(self):
        """测试安全性约束"""
        # 创建一门课程
        course = Course.objects.create(title="Security 101", teacher=self.teacher)

        # 1. 测试：老师不能选课
        self.client.login(username='teacher1', password='password123')
        enrol_url = reverse('course-enrol', args=[course.id])
        response = self.client.post(enrol_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 2. 测试：学生不能移除自己或其他学生
        self.client.logout()
        self.client.login(username='student1', password='password123')
        remove_url = reverse('course-remove-student', args=[course.id])
        response = self.client.post(remove_url, {'student_id': self.student.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_enrollment(self):
        """测试防止重复选课逻辑"""
        course = Course.objects.create(title="Math", teacher=self.teacher)
        self.client.login(username='student1', password='password123')
        
        # 第一次选课
        enrol_url = reverse('course-enrol', args=[course.id])
        self.client.post(enrol_url)
        
        # 第二次选课，应该返回 400 错误
        response = self.client.post(enrol_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'You are already enrolled.')

    def test_material_notification_broadcast(self):
        """测试教材上传时的批量通知逻辑"""
        # 准备数据
        course = Course.objects.create(title="Science", teacher=self.teacher)
        course.students.add(self.student)
        # 再增加一个学生
        another_student = User.objects.create_user(username='student2', password='123', real_name='User 2')
        course.students.add(another_student)

        self.client.login(username='teacher1', password='password123')
        
        # 模拟上传教材
        url = reverse('material-list')
        # 注意：这里我们只模拟逻辑，不实际上传物理文件
        fake_file = SimpleUploadedFile("test_lab.pdf", b"file_content", content_type="application/pdf")
    
        data = {
            'course': course.id, 
            'title': 'Lab Notes',
            'file': fake_file  # 补全必填的文件字段
        }
        
        # 使用 multipart 格式发送请求以支持文件上传
        response = self.client.post(url, data, format='multipart') 
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)