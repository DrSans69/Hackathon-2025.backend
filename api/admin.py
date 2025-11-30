from django.contrib import admin
from .models import Conversation, ChatMessage


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'user']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'role', 'short_content', 'has_news_context', 'created_at']
    list_filter = ['role', 'has_news_context', 'created_at']
    search_fields = ['content', 'conversation__title']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'