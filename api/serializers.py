from rest_framework import serializers

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer for Chat model.
    """

    messages = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "course",
            "topic",
            "name",
            "additional_info",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_messages(self, obj):
        """
        Get messages for this chat.
        """
        messages = obj.messages.all()
        return MessageListSerializer(messages, many=True).data


class ChatCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating chats.
    """

    class Meta:
        model = Chat
        fields = [
            "course",
            "topic",
            "name",
            "additional_info",
        ]


class ChatListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing chats without messages.
    """

    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            "id",
            "course",
            "topic",
            "name",
            "message_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        """
        Get the count of messages in this chat.
        """
        return obj.messages.count()


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    """

    class Meta:
        model = Message
        fields = [
            "id",
            "chat",
            "role",
            "content_type",
            "content",
            "order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating messages.
    """

    class Meta:
        model = Message
        fields = [
            "chat",
            "role",
            "content_type",
            "content",
            "order",
        ]


class MessageListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing messages with minimal fields.
    """

    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "content_type",
            "content",
            "order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
