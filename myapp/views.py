from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate , get_user_model
from django.shortcuts import get_object_or_404
from .forms import CustomUserCreationForm, CustomLoginForm, StoryForm, PostForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import *
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Create your views here.

@login_required
def home_view(request):
    now = timezone.now()
    stories = Story.objects.filter(created_at__gte=now - timedelta(hours=24)).order_by('-created_at')
    posts = Post.objects.all().order_by('-created_at')
    post_form = PostForm()

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        if post_form.is_valid():
            new_post = post_form.save(commit=False)
            new_post.user = request.user
            new_post.save()
            return redirect('home')

    context = {
        'stories': stories,
        'posts': posts,
        'post_form': post_form,
    }
    return render(request, 'home.html', context)

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



# def home_view(request):
#     return render(request, 'home.html')


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



# story views
@login_required
def create_story(request):
    """
    Allow logged-in users to upload a new story (image or video).
    """
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            return redirect('home')
    else:
        form = StoryForm()
    return render(request, 'story_form.html', {'form': form})


def story_detail(request, pk):
    story = Story.objects.get(pk=pk)
    user_liked_story = False
    if request.user.is_authenticated:
        user_liked_story = story.likes.filter(user=request.user).exists()

    context = {
        'story': story,
        'user_liked_story': user_liked_story,
    }
    return render(request, 'story_detail.html', context)

def story_list(request):
    from datetime import timedelta
    now = timezone.now()
    stories = Story.objects.filter(created_at__gte=now - timedelta(hours=24))
    return render(request, 'home.html', {'stories': stories})

def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)

    # Only allow deletion if the logged-in user owns the story
    if story.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this story.")

    if request.method == "POST":
        story.delete()
        # Redirect to homepage or story list or user profile page after deletion
        return redirect('home')  # Change 'home' to wherever you want

    # For GET requests, you might want to confirm deletion or just redirect
    return redirect('home')



@login_required
def like_story(request, story_id):
    story = Story.objects.get(id=story_id)
    user = request.user

    liked = StoryLike.objects.filter(story=story, user=user).exists()
    if liked:
        # Unlike
        StoryLike.objects.filter(story=story, user=user).delete()
        liked = False
    else:
        # Like
        StoryLike.objects.create(story=story, user=user)
        liked = True

    likes_count = story.likes.count()
    return JsonResponse({'liked': liked, 'likes_count': likes_count})


@login_required
def comment_story(request, story_id):
    if request.method == 'POST':
        story = Story.objects.get(id=story_id)
        user = request.user
        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            comment = StoryComment.objects.create(story=story, user=user, text=comment_text)
            return JsonResponse({
                'success': True,
                'comment': {
                    'user': user.username,
                    'text': comment.text,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                }
            })
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def share_story(request, story_id):
    story = Story.objects.get(id=story_id)
    user = request.user
    # For sharing logic, you might want to record the share and/or open a share dialog.
    StoryShare.objects.create(story=story, user=user)
    return JsonResponse({'success': True, 'message': 'Story shared!'})


# post views
@login_required
@csrf_exempt  # Ideally handle CSRF properly in AJAX
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True

        return JsonResponse({'liked': liked, 'total_likes': post.likes.count()})

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        comment_text = request.POST.get('comment_text')

        if comment_text:
            Comment.objects.create(post=post, user=request.user, text=comment_text)
        else:
            # Optional: return error if comment text is empty
            return JsonResponse({'error': 'Empty comment'}, status=400)

        # If you want to return JSON (AJAX), you can do:
        # return JsonResponse({'success': True})

        # Otherwise, redirect back to referring page
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# message views

User = get_user_model()

@login_required
def messages_view(request):
    current_user = request.user

    # All users except the logged-in one
    all_users = User.objects.exclude(id=current_user.id)

    # All conversations of the current user
    conversations = Conversation.objects.filter(participants=current_user).prefetch_related('participants', 'messages').order_by('-updated_at')

    # Build a dict of user_id -> conversation
    conversation_dict = {}
    for convo in conversations:
        other_user = convo.get_other_participant(current_user)
        if other_user:
            convo.other_participant = other_user
            conversation_dict[other_user.id] = convo

    # Get the first conversation to show on the right side
    active_conversation = conversations.first()
    if active_conversation:
        active_conversation.other_participant = active_conversation.get_other_participant(current_user)

    context = {
        'all_users': all_users,
        'conversation_dict': conversation_dict,
        'active_conversation': active_conversation,
    }
    return render(request, 'messages.html', context)

@login_required
def chat_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')

    return render(request, 'messages.html', {
        'conversations': conversations,
        'active_conversation': conversation
    })

@login_required
def send_message(request, conversation_id):
    if request.method == 'POST':
        content = request.POST.get('message')
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        conversation.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'content': message.content,
                'timestamp': message.timestamp.strftime("%I:%M %p")
            })

        return redirect('chat_detail', conversation_id=conversation.id)

@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)

    return redirect('chat_detail', conversation_id=conversation.id)
