from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.generic import CreateView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Message, Profile
from .forms import ProfileForm


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('chat')

    def form_valid(self, form):
        user = form.save()
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=user.username, password=raw_password)
        login(self.request, user)
        Profile.objects.get_or_create(user=user)
        return super().form_valid(form)

class CustomLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('chat')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

@login_required
def chat_view(request):
    users = User.objects.exclude(id=request.user.id).prefetch_related('profile')
    for user in users:
        room = '_'.join(sorted([request.user.username, user.username]))
        latest = Message.objects.filter(room=room).order_by('-timestamp').first()
        user.profile.latest_message = latest.content if latest else 'Say hi to start chatting!'
        user.profile.latest_timestamp = latest.timestamp if latest else None
        print(f"User: {user.username}, image URL: {user.profile.image.url if user.profile.image else 'None'}")
    profile = request.user.profile
    current_name = profile.name or request.user.username
    current_initials = current_name[:2].upper()
    # Ensure profile.image.url is not accessed directly if None
    return render(request, 'chat.html', {
        'users': users,
        'profile': profile,
        'current_name': current_name,
        'current_initials': current_initials,
        'user': request.user,
    })
def home(request):
    return render(request, 'home.html')
