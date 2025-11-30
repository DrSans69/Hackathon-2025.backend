from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    """
    A conversation belongs to a user and stores chat history.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    """
    A message in a conversation.
    """
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    has_news_context = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.conversation.title} - {self.role}: {self.content[:50]}"