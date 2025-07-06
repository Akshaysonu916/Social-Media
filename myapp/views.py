from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate , get_user_model
from django.shortcuts import get_object_or_404
from .forms import CustomUserCreationForm, CustomLoginForm, StoryForm, PostForm , EventForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import *
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import logging
from django.db.models import Count, IntegerField, ExpressionWrapper, F
from django.utils.timezone import now
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Create your views here.

@login_required
def home_view(request):
    now = timezone.now()

    # Get recent stories (last 24 hrs)
    stories = Story.objects.filter(
        created_at__gte=now - timedelta(hours=24)
    ).select_related('user').order_by('user', '-created_at')

    # Get all posts ordered by newest first
    posts = Post.objects.all().order_by('-created_at')

    # Handle post creation
    post_form = PostForm()
    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        if post_form.is_valid():
            new_post = post_form.save(commit=False)
            new_post.user = request.user
            new_post.save()
            return redirect('home')

    # Group stories by user
    story_groups = []
    user_stories_dict = defaultdict(list)
    for story in stories:
        user_stories_dict[story.user].append(story)
    for user, user_stories in user_stories_dict.items():
        story_groups.append((user, user_stories))

    # Suggest users to follow (exclude self + already followed)
    following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    suggestions = CustomUser.objects.exclude(id__in=following_ids).exclude(id=request.user.id).order_by('?')[:5]

    context = {
        'story_groups': story_groups,
        'posts': posts,
        'post_form': post_form,
        'suggestions': suggestions,
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
def profile(request, username=None):
    # View either own profile or someone else's
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user

    # 🔍 Track profile view (avoid self-viewing and duplicate within 24h)
    if request.user != profile_user:
        time_threshold = now() - timedelta(hours=24)
        already_viewed = ProfileView.objects.filter(
            viewer=request.user,
            viewed_user=profile_user,
            timestamp__gte=time_threshold
        ).exists()

        if not already_viewed:
            ProfileView.objects.create(viewer=request.user, viewed_user=profile_user)

    # 🧠 Handle profile update (only if own profile)
    if request.method == 'POST' and request.user == profile_user:
        full_name = request.POST.get('name', '')
        if full_name:
            parts = full_name.strip().split(' ', 1)
            profile_user.first_name = parts[0]
            profile_user.last_name = parts[1] if len(parts) > 1 else ''

        profile_user.email = request.POST.get('email', profile_user.email)
        profile_user.location = request.POST.get('location', profile_user.location)
        profile_user.bio = request.POST.get('bio', profile_user.bio)

        if 'profile_picture' in request.FILES:
            profile_user.profile_picture = request.FILES['profile_picture']

        if 'cover_photo' in request.FILES:
            profile_user.cover_photo = request.FILES['cover_photo']

        is_public = request.POST.get('is_public')
        profile_user.is_public = True if is_public == 'on' else False

        profile_user.save()
        return redirect('profile')

    # 📊 Followers and following count
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()

    # 🖼️ Recent posts
    recent_posts = Post.objects.filter(user=profile_user).order_by('-created_at')[:6]

    # 👀 Recent profile views (last 7 days)
    recent_views_count = ProfileView.objects.filter(
        viewed_user=profile_user,
        timestamp__gte=now() - timedelta(days=7)
    ).count()

    context = {
        'profile_user': profile_user,
        'followers_count': followers_count,
        'following_count': following_count,
        'recent_posts': recent_posts,
        'recent_views_count': recent_views_count,
    }

    return render(request, 'profile.html', context)


@login_required
def analytics_dashboard(request):
    # Get all posts by the current user with annotated counts
    posts = Post.objects.filter(user=request.user).annotate(
        total_likes_count=Count('like_entries', distinct=True),
        total_comments_count=Count('comments', distinct=True),
        total_views_count=Count('views', distinct=True),
    ).order_by('-created_at')

    # Summary totals
    total_likes = sum(post.total_likes_count for post in posts)
    total_comments = sum(post.total_comments_count for post in posts)
    total_views = sum(post.total_views_count for post in posts)

    # Last 7 days for chart
    today = now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [day.strftime('%b %d') for day in days]

    # Likes (using liked_at timestamp from Like model)
    likes_data = [
        Like.objects.filter(post__user=request.user, liked_at__date=day).count()
        for day in days
    ]

    # Comments per day
    comments_data = [
        Comment.objects.filter(post__user=request.user, created_at__date=day).count()
        for day in days
    ]

    # Views per day
    views_data = [
        PostView.objects.filter(post__user=request.user, viewed_at__date=day).count()
        for day in days
    ]

    context = {
        'posts': posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_views': total_views,
        'labels': labels,
        'likes_data': likes_data,
        'comments_data': comments_data,
        'views_data': views_data,
    }

    return render(request, 'analytics.html', context)

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
    now = timezone.now()
    recent_stories = Story.objects.filter(created_at__gte=now - timedelta(hours=24)).order_by('-created_at')

    # Group stories by user and pick the latest one (or first)
    story_groups = {}
    for story in recent_stories:
        if story.user not in story_groups:  # Only keep the latest story per user
            story_groups[story.user] = story  # or story.user.profile_picture if available
    
    return render(request, 'home.html', {'story_groups': story_groups.items()})


@login_required
def user_stories(request, user_id):
    # Get the specific user
    user = get_object_or_404(User, id=user_id)
    
    # Get their active stories (within last 24 hours)
    user_stories = Story.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-created_at')
    
    # If no stories found, redirect back or show message
    if not user_stories.exists():
        from django.contrib import messages
        messages.info(request, f"{user.username} has no active stories.")
        return redirect('home')
    
    context = {
        'story_user': user,  # The user whose stories we're viewing
        'stories': user_stories,  # Their stories
    }
    
    # Use the user_stories template (Instagram-style viewer)
    return render(request, 'user_stories.html', context)



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
    try:
        story = Story.objects.get(id=story_id)
        user = request.user

        liked = StoryLike.objects.filter(story=story, user=user).exists()
        if liked:
            StoryLike.objects.filter(story=story, user=user).delete()
            liked = False
        else:
            StoryLike.objects.create(story=story, user=user)
            liked = True

        return JsonResponse({
            'liked': liked, 
            'likes_count': story.likes.count()
        })
        
    except Story.DoesNotExist:
        return JsonResponse({'error': 'Story not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    # Toggle like/unlike
    like, created = Like.objects.get_or_create(user=user, post=post)

    if not created:
        # Already liked — unlike
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'total_likes': post.like_entries.count(),
        'status': 'success'
    })


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


def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.user:  # Ensure only the post owner can delete
        post.delete()
    return redirect('home')  # Redirect back to home after deletion


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Save view (avoid duplicate if same user refreshes)
    if request.user.is_authenticated:
        if not PostView.objects.filter(post=post, user=request.user).exists():
            PostView.objects.create(post=post, user=request.user)
    else:
        PostView.objects.create(post=post, user=None)

    return render(request, 'post_detail.html', {'post': post})


# message views

User = get_user_model()

@login_required
def messages_view(request):
    current_user = request.user

    # All users except the logged-in user
    all_users = User.objects.exclude(id=current_user.id)

    # All conversations involving current user, prefetch related for efficiency
    conversations = (
        Conversation.objects
        .filter(participants=current_user)
        .prefetch_related('participants', 'messages')
        .order_by('-updated_at')
    )

    # Map other_user.id -> conversation object for quick lookup in template
    conversation_partners = {}
    for convo in conversations:
        other_user = convo.get_other_participant(current_user)
        if other_user:
            conversation_partners[other_user.id] = convo

    # Pick first conversation to display in chat area (if any)
    active_conversation = conversations.first()
    
    # Also add the other participant for the active conversation for convenience
    active_other_user = None
    if active_conversation:
        active_other_user = active_conversation.get_other_participant(current_user)

    context = {
        'all_users': all_users,
        'conversations': conversations,
        'active_conversation': active_conversation,
        'active_other_user': active_other_user,
        'conversation_partners': conversation_partners,
    }
    return render(request, 'messages.html', context)

@login_required
def chat_detail(request, conversation_id):
    current_user = request.user

    # 1. Get the active conversation
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=current_user)

    # 2. Get all user’s conversations (for sidebar)
    conversations = Conversation.objects.filter(participants=current_user).order_by('-updated_at')

    # 3. Map other participants for sidebar quick access
    conversation_partners = {}
    for convo in conversations:
        other_user = convo.get_other_participant(current_user)
        if other_user:
            conversation_partners[other_user.id] = convo

    # 4. Get all users (for sidebar list)
    all_users = User.objects.exclude(id=current_user.id)

    # 5. Get the other user in this active conversation
    active_other_user = conversation.get_other_participant(current_user)

    # ✅ 6. Get messages that are NOT deleted for this user and not deleted for everyone
    messages = conversation.messages.exclude(deleted_for=current_user).filter(deleted_for_everyone=False).order_by('timestamp')

    # 7. Prepare context
    context = {
        'all_users': all_users,
        'conversations': conversations,
        'active_conversation': conversation,
        'conversation_partners': conversation_partners,
        'active_other_user': active_other_user,
        'messages': messages,  # ✅ Properly filtered messages
    }

    return render(request, 'messages.html', context)


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


User = get_user_model()

def profile_preview(request, user_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    target_user = get_object_or_404(User, id=user_id)

    # Example mutual followers logic (optional)
    mutuals = User.objects.filter(
        followers__in=[request.user],
        following__in=[target_user]
    ).exclude(id=request.user.id)[:3]

    data = {
        'username': target_user.username,
        'full_name': f"{target_user.first_name} {target_user.last_name}",
        'bio': target_user.bio,
        'location': target_user.location,
        'profile_picture': target_user.profile_picture.url if target_user.profile_picture else '/static/images/default-profile.png',
        'mutuals': [u.username for u in mutuals],
    }
    return JsonResponse(data)



@require_POST
@login_required
def delete_message(request, message_id, delete_type):
    message = get_object_or_404(Message, id=message_id)

    if delete_type == 'me':
        message.deleted_for.add(request.user)
        return JsonResponse({'success': True})

    elif delete_type == 'everyone':
        if message.sender != request.user:
            return JsonResponse({'error': 'Not authorized'}, status=403)
        if not message.can_delete_for_everyone():
            return JsonResponse({'error': 'Time limit exceeded'}, status=403)
        
        message.deleted_for_everyone = True
        message.save()

        # ✅ Broadcast the deletion to all WebSocket clients in the conversation
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.conversation.id}",
            {
                "type": "delete_message",
                "message_id": message.id
            }
        )

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid delete type'}, status=400)

def broadcast_message_deletion(message_id, conversation_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation_id}",
        {
            "type": "delete_message",
            "message_id": message_id,
        }
    )


# userlist view

User = get_user_model()

@login_required
def users_list(request):
    users = User.objects.exclude(id=request.user.id)  # Exclude self
    paginator = Paginator(users, 9)  # 9 users per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'users_list.html', {'users': page_obj})


@login_required
def follow_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        target_user = CustomUser.objects.get(id=user_id)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)

        if not created and follow.is_accepted:
            return JsonResponse({'status': 'already_following'})
        elif not created and not follow.is_accepted:
            return JsonResponse({'status': 'request_pending'})

        return JsonResponse({'status': 'follow_request_sent'})

@login_required
def unfollow_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        Follow.objects.filter(follower=request.user, following_id=user_id).delete()
        return JsonResponse({'status': 'unfollowed'})
    
@login_required
def profile_detail(request, username):
    user_profile = get_object_or_404(CustomUser, username=username)

    # Followers and Following
    followers = Follow.objects.filter(following=user_profile)
    following = Follow.objects.filter(follower=user_profile)

    # Relationship Status
    is_following = False
    is_followed_by = False
    if user_profile != request.user:
        is_following = followers.filter(follower=request.user).exists()
        is_followed_by = following.filter(following=request.user).exists()

    # Fetch posts and stories
    posts = Post.objects.filter(user=user_profile).order_by('-created_at')
    stories = Story.objects.filter(user=user_profile).order_by('-created_at')

    context = {
        'user_profile': user_profile,
        'follower_count': followers.count(),
        'following_count': following.count(),
        'is_following': is_following,
        'is_followed_by': is_followed_by,
        'posts': posts,
        'stories': stories,
    }

    return render(request, 'profile_detail.html', context)



User = get_user_model()

def follower_list(request, username):
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')
    return render(request, 'followers_list.html', {
        'user_profile': user,
        'users': [f.follower for f in followers],
        'list_type': 'Followers',
    })

def following_list(request, username):
    user = get_object_or_404(User, username=username)
    followings = Follow.objects.filter(follower=user).select_related('following')
    return render(request, 'followers_list.html', {
        'user_profile': user,
        'users': [f.following for f in followings],
        'list_type': 'Following',
    })

@login_required
def homefollow_user(request, user_id):
    user_to_follow = get_object_or_404(CustomUser, id=user_id)
    if user_to_follow != request.user:
        Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    return redirect('home')

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'post_detail.html', {'post': post})



# gaming views
def gaming_view(request):
    # Initialize session history if not present
    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    if request.method == "POST":
        message = request.POST.get("message", "").strip().lower()
        response = ""

        # Rule-based bot responses
        if "game" in message or "suggest" in message:
            response = "Try out Tic Tac Toe or Snake! 🎮"
        elif "hello" in message or "hi" in message:
            response = "Hey gamer! 👋 What can I help you with?"
        elif "bye" in message:
            response = "Goodbye! Come back for more games later!"
        else:
            response = "Sorry, I didn’t understand that. Try asking for a game suggestion!"

        # Append message-response pair to session chat history
        chat = request.session["chat_history"]
        chat.append({
            "user": message,
            "bot": response
        })
        request.session["chat_history"] = chat
        request.session.modified = True

    # Pass full history to the template
    return render(request, "gaming.html", {
        "chat_history": request.session.get("chat_history", [])
    })



# events views
def events_view(request):
    events = Event.objects.all().order_by('-date')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            event.save()
            return redirect('events_view')
    else:
        form = EventForm()
    
    return render(request, 'events.html', {
        'events': events,
        'form': form
    })

def event_details(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    data = {
        'title': event.title,
        'description': event.description,
        'type': event.event_type,
        'date': event.date.strftime('%B %d, %Y'),
        'location': event.location,
        'image_url': event.image_url,
        'organizer': event.creator.username
    }
    return JsonResponse(data)



# explore view
def explore_view(request):
    now = timezone.now()
    time_threshold = now - timedelta(hours=48)  # Last 48 hours

    trending_posts = (
        Post.objects.filter(created_at__gte=time_threshold)
        .annotate(
            like_count=Count('likes', distinct=True),
            comment_count=Count('comments', distinct=True),
            popularity_score=ExpressionWrapper(
                Count('likes', distinct=True) + Count('comments', distinct=True),
                output_field=IntegerField()
            )
        )
        .order_by('-popularity_score', '-created_at')[:20]  # Top 20 by popularity
    )

    context = {
        'trending_posts': trending_posts,
    }
    return render(request, 'explore.html', context)