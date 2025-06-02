from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import CustomUserCreationForm, CustomLoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def home(request):
    return render(request, 'home.html')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # or your desired redirect
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



def home_view(request):
    return render(request, 'home.html')


@login_required
def profile(request):
    user = request.user

    if request.method == 'POST':
        # Split full name into first and last names if provided
        full_name = request.POST.get('name', '')
        if full_name:
            parts = full_name.strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''

        user.email = request.POST.get('email', user.email)
        user.location = request.POST.get('location', user.location)
        user.bio = request.POST.get('bio', user.bio)

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()
        return redirect('profile')

    return render(request, 'profile.html', {'user': user})


def users_list(request):
    return render(request, 'users_list.html')

def notifications(request):
    return render(request, 'notifications.html')

def messages_view(request):
    return render(request, 'messages.html')



def search_view(request):
    query = request.GET.get('q', '')
    # Implement your search logic here
    context = {'query': query}
    return render(request, 'search_results.html', context)


def friends_view(request):
    return render(request, 'friends.html')

def saved_view(request):
    return render(request, 'saved.html')

def groups_view(request):
    return render(request, 'groups.html')

def watch_view(request):
    return render(request, 'watch.html')

def memories_view(request):
    return render(request, 'memories.html')

def explore_view(request):
    return render(request, 'explore.html')

def events_view(request):
    # Render a template for Events page
    return render(request, 'events.html')

def gaming_view(request):
    return render(request, 'gaming.html')