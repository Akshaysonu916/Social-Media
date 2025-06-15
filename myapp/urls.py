from django.urls import path
from . import views

urlpatterns = [

    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),



    # Home view
    path('', views.home_view, name='home'),
    path('profile/', views.profile, name='profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('search/', views.search_view, name='search'),
    path('friends/', views.friends_view, name='friends'),
    path('saved/', views.saved_view, name='saved'),
    path('groups/', views.groups_view, name='groups'),
    path('watch/', views.watch_view, name='watch'),
    path('memories/', views.memories_view, name='memories'),
    path('explore/', views.explore_view, name='explore'),



    # Story URLs
    path('story/create/', views.create_story, name='create_story'),
    path('stories/<int:pk>/', views.story_detail, name='story_detail'),
    path('story/delete/<int:story_id>/', views.delete_story, name='delete_story'),
    path('story/<int:story_id>/like/', views.like_story, name='like_story'),
    path('story/<int:story_id>/comment/', views.comment_story, name='comment_story'),
    path('story/<int:story_id>/share/', views.share_story, name='share_story'),
    path('user-stories/<int:user_id>/', views.user_stories, name='user_stories'),


    # Post URLs
    path('like_post/<int:post_id>/', views.like_post, name='like_post'),
    path('add_comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),

    # messaging URLs
    path('messages/', views.messages_view, name='messages'),
    path('start-conversation/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('messages/<int:conversation_id>/', views.chat_detail, name='chat_detail'),
    path('messages/<int:conversation_id>/send/', views.send_message, name='send_message'),


    # userlist URLs
    path('users/', views.users_list, name='users_list'),
    path('follow/', views.follow_user, name='follow_user'),
    path('unfollow/', views.unfollow_user, name='unfollow_user'),
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),
    path('followers/<str:username>/', views.follower_list, name='follower_list'),
    path('following/<str:username>/', views.following_list, name='following_list'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    

    # gaming URLs
    path('gaming/', views.gaming_view, name='gaming'),


    # events URLs
    path('events/', views.events_view, name='events_view'),
    path('events/<int:event_id>/',views.event_details, name='event_details'),

]