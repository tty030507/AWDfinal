from django.core.management.base import BaseCommand
from main_app.models import User, Course
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with initial students, teachers, and courses'

    def handle(self, *args, **kwargs):
        self.stdout.write('正在清理旧数据...')
        # 1. 清理旧数据 (不删除超级管理员)
        User.objects.filter(is_superuser=False).delete()
        Course.objects.all().delete()

        # 2. 创建老师 (使用 user_type='teacher')
        teacher = User.objects.create_user(
            username='teacher1', 
            password='password123',
            email='smith@university.edu',
            real_name='Dr. Smith',
            user_type='teacher'  # 修改点：对应新模型的字段
        )
        self.stdout.write(self.style.SUCCESS('成功创建老师: teacher1 (密码: password123)'))

        # 3. 创建学生 (使用 user_type='student')
        student = User.objects.create_user(
            username='student1', 
            password='password123',
            email='john@student.com',
            real_name='John Doe',
            user_type='student'  # 修改点：对应新模型的字段
        )
        self.stdout.write(self.style.SUCCESS('成功创建学生: student1 (密码: password123)'))

        # 4. 创建一个演示课程
        course = Course.objects.create(
            teacher=teacher,
            title='Advanced Web Development',
            description='Learn Django, Celery, and Channels.'
        )
        # 将学生添加到课程中
        course.students.add(student)
        
        self.stdout.write(self.style.SUCCESS(f'成功创建并关联课程: {course.title}'))
        self.stdout.write(self.style.SUCCESS('--- 数据播种完成 ---'))