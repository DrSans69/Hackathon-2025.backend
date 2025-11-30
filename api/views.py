from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .ai.model import AIAssistant

from shared.utils import handle_error

from .ai import answer
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


assistant = AIAssistant()


# @api_view(["POST"])
# def create_course(request):
#     """
#     Create a new course.
#     """
#     try:
#         serializer = CourseCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             course = serializer.save()
#             response_serializer = CourseSerializer(course)
#             return Response(response_serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     except Exception as e:
#         return handle_error()


# @api_view(["GET"])
# def list_courses(request):
#     """
#     List all courses.
#     """
#     try:
#         courses = Course.objects.all()
#         serializer = CourseListSerializer(courses, many=True)
#         return Response(serializer.data)
#     except Exception as e:
#         return handle_error()


# @api_view(["GET"])
# def get_course(request, course_id):
    # """
    # Get a specific course.
    # """
    # try:
    #     course = Course.objects.get(id=course_id)
    #     serializer = CourseSerializer(course)
    #     return Response(serializer.data)
    # except Course.DoesNotExist:
    #     return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
    # except Exception as e:
    #     return handle_error()


# @api_view(["POST"])
# def create_topic(request):
#     """
#     Create a new topic.
#     """
#     try:
#         serializer = TopicCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             topic = serializer.save()
#             response_serializer = TopicSerializer(topic)
#             return Response(response_serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     except Exception as e:
#         return handle_error()


# @api_view(["GET"])
# def list_topics(request):
#     """
#     List all topics, optionally filtered by course.
#     """
#     try:
#         topics = Topic.objects.all()

#         # Filter by course if provided
#         course_id = request.query_params.get("course")
#         if course_id:
#             topics = topics.filter(course_id=course_id)

#         serializer = TopicListSerializer(topics, many=True)
#         return Response(serializer.data)
#     except Exception as e:
#         return handle_error()


# @api_view(["GET"])
# def get_topic(request, topic_id):
#     """
#     Get a specific topic.
#     """
#     try:
#         topic = Topic.objects.get(id=topic_id)
#         serializer = TopicSerializer(topic)
#         return Response(serializer.data)
#     except Topic.DoesNotExist:
#         return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return handle_error()


# @api_view(["PUT", "PATCH"])
# def update_topic(request, topic_id):
#     """
#     Update a topic (including progress and learned_info).
#     """
#     try:
#         topic = Topic.objects.get(id=topic_id)
#         serializer = TopicSerializer(topic, data=request.data, partial=True)
#         if serializer.is_valid():
#             topic = serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     except Topic.DoesNotExist:
#         return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return handle_error()


# @api_view(["POST"])
# def create_chat(request):
#     """
#     Create a new chat.
#     """
#     try:
#         serializer = ChatCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             chat = serializer.save()
#             response_serializer = ChatSerializer(chat)
#             return Response(response_serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     except Exception as e:
#         return handle_error()


# @api_view(["GET"])
# def list_chats(request):
#     """
#     List all chats, optionally filtered by course or topic.
#     """
#     try:
#         chats = Chat.objects.all()

#         # Filter by course if provided
#         course_id = request.query_params.get("course")
#         if course_id:
#             chats = chats.filter(course_id=course_id)

#         # Filter by topic if provided
#         topic_id = request.query_params.get("topic")
#         if topic_id:
#             chats = chats.filter(topic_id=topic_id)

#         serializer = ChatListSerializer(chats, many=True)
#         return Response(serializer.data)
#     except Exception as e:
#         return handle_error()


# @api_view(["GET"])
# def get_chat(request, chat_id):
#     """
#     Get a specific chat with all messages.
#     """
#     try:
#         chat = Chat.objects.get(id=chat_id)
#         serializer = ChatSerializer(chat)
#         return Response(serializer.data)
#     except Chat.DoesNotExist:
#         return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return handle_error()


# @api_view(["POST"])
# def add_message(request):
#     """
#     Add a message to a chat without AI response.
#     """
#     try:
#         serializer = MessageCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             message = serializer.save()
#             response_serializer = MessageSerializer(message)
#             return Response(response_serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     except Exception as e:
#         return handle_error()


# @api_view(["POST"])
# def send_message_with_ai(request):
#     """
#     Add a user message and get an AI response.
#     """
#     try:
#         # Validate and save the user message
#         serializer = MessageCreateSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         user_message = serializer.save()

#         # Get the chat and its context
#         chat = user_message.chat  # type: ignore
#         course = chat.course
#         topic = chat.topic

#         # Get previous messages for context
#         previous_messages = Message.objects.filter(chat=chat).order_by(
#             "order", "created_at"
#         )

#         # Build context for AI (placeholder)
#         context = {
#             "course_name": course.name,
#             "course_info": course.main_info,
#             "course_additional_info": course.additional_info,
#             "topic_name": topic.name if topic else None,
#             "topic_info": topic.info if topic else None,
#             "chat_additional_info": chat.additional_info,
#             "previous_messages": [
#                 {"role": msg.role, "content": msg.content} for msg in previous_messages
#             ],
#         }

#         ai_response = answer(str(context))

#         # Create AI response message
#         ai_message = Message.objects.create(
#             chat=chat,
#             role="assistant",
#             content_type="text",
#             content=ai_response,
#             order=user_message.order + 1,  # type: ignore
#         )

#         # Return both messages
#         return Response(
#             {
#                 "user_message": MessageSerializer(user_message).data,
#                 "ai_message": MessageSerializer(ai_message).data,
#             },
#             status=status.HTTP_201_CREATED,
#         )
#     except Exception as e:
#         return handle_error()
    
@api_view(['POST'])
def chat(request):
    """
    Handle chat requests
    Expected JSON: { "message": "user message", "history": [...] }
    """
    try:
        message = request.data.get('message')
        history = request.data.get('history', [])
        
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get AI response
        result = assistant.chat(message, history)
        
        return Response({
            'response': result['response'],
            'history': result['conversation_history'],
            'has_news_context': result['has_news_context']
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def reset_conversation(request):
    """Reset conversation history"""
    return Response({'message': 'Conversation reset', 'history': []})
