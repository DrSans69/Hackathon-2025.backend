from typing import List
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


from shared.utils import handle_error

from .ai import do
from .containers import get_mentor
from .models import Chat, Course, Message, Topic
from .serializers import (
    ChatCreateSerializer,
    ChatListSerializer,
    ChatSerializer,
    CourseCreateSerializer,
    CourseListSerializer,
    CourseSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    TopicCreateSerializer,
    TopicListSerializer,
    TopicSerializer,
)


@api_view(["GET"])
def hello(request):
    try:

        return Response({"message": do()})

    except Exception as e:
        return handle_error()


@api_view(["POST"])
def create_course(request):
    """
    Create a new course.
    """
    try:
        serializer = CourseCreateSerializer(data=request.data)
        if serializer.is_valid():
            course = serializer.save()
            response_serializer = CourseSerializer(course)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return handle_error()


@api_view(["GET"])
def list_courses(request):
    """
    List all courses.
    """
    try:
        courses = Course.objects.all()
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)
    except Exception as e:
        return handle_error()


@api_view(["GET"])
def get_course(request, course_id):
    """
    Get a specific course.
    """
    try:
        course = Course.objects.get(id=course_id)
        serializer = CourseSerializer(course)
        return Response(serializer.data)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return handle_error()


@api_view(["POST"])
def create_topic(request):
    """
    Create a new topic.
    """
    try:
        serializer = TopicCreateSerializer(data=request.data)
        if serializer.is_valid():
            topic = serializer.save()
            response_serializer = TopicSerializer(topic)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return handle_error()


@api_view(["GET"])
def list_topics(request):
    """
    List all topics, optionally filtered by course.
    """
    try:
        topics = Topic.objects.all()

        # Filter by course if provided
        course_id = request.query_params.get("course")
        if course_id:
            topics = topics.filter(course_id=course_id)

        serializer = TopicListSerializer(topics, many=True)
        return Response(serializer.data)
    except Exception as e:
        return handle_error()


@api_view(["GET"])
def get_topic(request, topic_id):
    """
    Get a specific topic.
    """
    try:
        topic = Topic.objects.get(id=topic_id)
        serializer = TopicSerializer(topic)
        return Response(serializer.data)
    except Topic.DoesNotExist:
        return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return handle_error()


@api_view(["PUT", "PATCH"])
def update_topic(request, topic_id):
    """
    Update a topic (including progress and learned_info).
    """
    try:
        topic = Topic.objects.get(id=topic_id)
        serializer = TopicSerializer(topic, data=request.data, partial=True)
        if serializer.is_valid():
            topic = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Topic.DoesNotExist:
        return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return handle_error()


@api_view(["POST"])
def create_chat(request):
    """
    Create a new chat.
    """
    try:
        serializer = ChatCreateSerializer(data=request.data)
        if serializer.is_valid():
            chat = serializer.save()
            response_serializer = ChatSerializer(chat)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return handle_error()


@api_view(["GET"])
def list_chats(request):
    """
    List all chats, optionally filtered by course or topic.
    """
    try:
        chats = Chat.objects.all()

        # Filter by course if provided
        course_id = request.query_params.get("course")
        if course_id:
            chats = chats.filter(course_id=course_id)

        # Filter by topic if provided
        topic_id = request.query_params.get("topic")
        if topic_id:
            chats = chats.filter(topic_id=topic_id)

        serializer = ChatListSerializer(chats, many=True)
        return Response(serializer.data)
    except Exception as e:
        return handle_error()


@api_view(["GET"])
def get_chat(request, chat_id):
    """
    Get a specific chat with all messages.
    """
    try:
        chat = Chat.objects.get(id=chat_id)
        serializer = ChatSerializer(chat)
        return Response(serializer.data)
    except Chat.DoesNotExist:
        return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return handle_error()


@api_view(["POST"])
def add_message(request):
    """
    Add a message to a chat without AI response.
    """
    try:
        serializer = MessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save()
            response_serializer = MessageSerializer(message)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return handle_error()


@api_view(["POST"])
def send_message_with_ai(request):
    """
    Add a user message and get an AI response.
    """
    try:
        # Validate and save the user message
        serializer = MessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.save()

        # Get the chat and its context
        chat = user_message.chat  # type: ignore
        course = chat.course
        topic = chat.topic

        # Get previous messages for context
        previous_messages = Message.objects.filter(chat=chat).order_by(
            "order", "created_at"
        )

        # Build context for AI (placeholder)
        context = {
            "course_name": course.name,
            "course_info": course.main_info,
            "course_additional_info": course.additional_info,
            "topic_name": topic.name if topic else None,
            "topic_info": topic.info if topic else None,
            "chat_additional_info": chat.additional_info,
            "previous_messages": [
                {"role": msg.role, "content": msg.content} for msg in previous_messages
            ],
        }

        # TODO: Call actual AI API based on course.model
        # For now, use placeholder response
        if course.model == "gpt":
            ai_response = f"[GPT Placeholder] Response to: {user_message.content}"  # type: ignore
        elif course.model == "claude":
            ai_response = f"[Claude Placeholder] Response to: {user_message.content}"  # type: ignore
        else:
            ai_response = f"[Unknown Model] Response to: {user_message.content}"  # type: ignore

        # Create AI response message
        ai_message = Message.objects.create(
            chat=chat,
            role="assistant",
            content_type="text",
            content=ai_response,
            order=user_message.order + 1,  # type: ignore
        )

        # Return both messages
        return Response(
            {
                "user_message": MessageSerializer(user_message).data,
                "ai_message": MessageSerializer(ai_message).data,
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return handle_error()


@api_view(["POST"])
def upload_material(request):
    """
    Process uploaded materials (files and URLs).
    Expects:
    - Files via multipart/form-data
    - URLs as JSON in request.data['urls']
    """
    try:
        materials = []

        # Get uploaded files from request.FILES
        for key, uploaded_file in request.FILES.items():
            materials.append(
                {
                    "filename": uploaded_file.name,
                    "content": uploaded_file.read(),  # bytes
                    "content_type": uploaded_file.content_type
                    or "application/octet-stream",
                }
            )

        # Get URLs from request.data (JSON)
        urls = request.data.get("urls", [])
        for url_item in urls:
            materials.append(
                {
                    "filename": url_item.get("filename", "Unnamed"),
                    "url": url_item["url"],
                    "content_type": url_item.get("content_type", "url/webpage"),
                }
            )

        # Now process materials
        # materials is List[dict] as expected
        mentor = get_mentor()

        a = mentor.process_uploaded_materials(materials)

        return Response({"processed": len(materials)}, status=status.HTTP_200_OK)
    except Exception as e:
        return handle_error()
