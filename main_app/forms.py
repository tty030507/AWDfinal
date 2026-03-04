from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(forms.ModelForm):
    # 手动定义密码字段，因为 ModelForm 默认不会处理 User 的密码哈希
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'real_name', 'password', 'user_type', 'photo')

    def save(self, commit=True):
        user = super().save(commit=False)
        # 必须使用 set_password 来加密密码，否则无法登录
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user