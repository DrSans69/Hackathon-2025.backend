from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth endpoints
    path("auth/register/", views.register_user, name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", views.logout_user, name="logout"),
    path("auth/me/", views.get_current_user, name="current_user"),
    
    # Conversation endpoints
    path("conversations/", views.list_conversations, name="list_conversations"),
    path("conversations/create/", views.create_conversation, name="create_conversation"),
    path("conversations/<int:conversation_id>/", views.get_conversation, name="get_conversation"),
    path("conversations/<int:conversation_id>/update/", views.update_conversation, name="update_conversation"),
    path("conversations/<int:conversation_id>/delete/", views.delete_conversation, name="delete_conversation"),
    
    # Chat endpoints
    path("chat/", views.chat, name="chat"),
    path("chat/reset/", views.reset_conversation, name="reset_conversation"),
]