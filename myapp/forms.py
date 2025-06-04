from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import *

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)  # make sure email is required

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')


    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username", max_length=150 ,required=True)



# story forms
class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['image', 'video', 'caption']

    def clean(self):
        cleaned = super().clean()
        image = cleaned.get('image')
        video = cleaned.get('video')
        if not image and not video:
            raise forms.ValidationError("You must upload either an image or a video.")
        return cleaned
    

# post forms
class PostForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3,
        'placeholder': "What's on your mind?"
    }), max_length=500, required=True)

    class Meta:
        model = Post
        fields = ['content', 'image']