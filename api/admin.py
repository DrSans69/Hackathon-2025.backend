from django.contrib import admin

from .models import Chat, Course, Message, Topic


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "model", "created_at", "updated_at"]
    list_filter = ["model", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "course", "progress", "created_at", "updated_at"]
    list_filter = ["course", "created_at"]
    search_fields = ["name", "description", "course__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ["name", "course", "topic", "created_at", "updated_at"]
    list_filter = ["course", "topic", "created_at"]
    search_fields = ["name", "course__name", "topic__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["chat", "role", "content_type", "order", "created_at"]
    list_filter = ["role", "content_type", "created_at"]
    search_fields = ["content", "chat__name"]
    readonly_fields = ["created_at"]
