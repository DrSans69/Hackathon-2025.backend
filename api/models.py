from django.db import models


class Course(models.Model):
    """
    A course is a collection of AI chats combined with the same theme.
    """

    MODEL_CHOICES = [
        ("claude", "Claude"),
        ("gpt", "GPT"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(help_text="General information about the course")
    main_info = models.TextField(
        blank=True, help_text="Main information about the course"
    )
    additional_info = models.TextField(
        blank=True, help_text="Additional information for AI context"
    )
    model = models.CharField(
        max_length=50,
        choices=MODEL_CHOICES,
        default="gpt",
        help_text="AI model to use",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Topic(models.Model):
    """
    A topic belongs to a course and represents a specific learning area.
    Tracks learning progress and content.
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=255)
    description = models.TextField(help_text="Description of the topic")
    info = models.TextField(help_text="Information about what this topic covers")
    learned_info = models.TextField(
        blank=True, default="", help_text="Information that has been learned so far"
    )
    expected_info = models.TextField(
        blank=True,
        default="",
        help_text="Expected knowledge to compare against for progress calculation",
    )
    progress = models.IntegerField(default=0, help_text="Progress percentage (0-100)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "created_at"]

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class Chat(models.Model):
    """
    A chat session tied to either a specific topic or the course as a whole.
    If topic is None, the chat represents the whole course (default topic).
    """

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chats")
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="chats",
        null=True,
        blank=True,
        help_text="Optional topic. If null, chat represents the whole course.",
    )
    name = models.CharField(max_length=255)
    additional_info = models.TextField(
        blank=True, default="", help_text="Additional information for AI context"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "Chats"

    def __str__(self):
        if self.topic:
            return f"{self.course.name} - {self.topic.name} - {self.name}"
        return f"{self.course.name} - {self.name}"


class Message(models.Model):
    """
    A message in a chat session.
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    CONTENT_TYPE_CHOICES = [
        ("text", "Text"),
        ("file", "File"),
        ("image", "Image"),
        ("voice", "Voice Message"),
        ("video", "Video"),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="user",
        help_text="Message sender role",
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default="text",
        help_text="Type of content",
    )
    content = models.TextField(help_text="Message content or file path/URL")
    order = models.IntegerField(
        default=0, help_text="Message order in the conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chat", "order", "created_at"]

    def __str__(self):
        return f"{self.chat.name} - {self.role} ({self.content_type}) - {self.content[:50]}"
