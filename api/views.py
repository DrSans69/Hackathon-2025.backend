from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from .ai.model import AIAssistant
from .models import Conversation, ChatMessage
from .serializers import (
    ConversationSerializer, 
    ConversationListSerializer, 
    ChatMessageSerializer,
    UserSerializer,
)

assistant = AIAssistant()


# ============== AUTH VIEWS ==============

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user.
    
    POST /api/auth/register/
    Body: { "username": "john", "email": "john@example.com", "password": "secret123" }
    
    Returns: { "user": {...}, "access": "token", "refresh": "token" }
    """
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    
    # Validation
    if not username:
        return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not password:
        return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(password) < 6:
        return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(username) < 3:
        return Response({'error': 'Username must be at least 3 characters'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
    
    if email and User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create user in database
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password  # Django automatically hashes the password
        )
        
        # Generate JWT tokens for immediate login
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get the currently authenticated user.
    
    GET /api/auth/me/
    Headers: Authorization: Bearer <access_token>
    
    Returns: { "id": 1, "username": "john", "email": "john@example.com" }
    """
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user by blacklisting the refresh token.
    
    POST /api/auth/logout/
    Body: { "refresh": "refresh_token" }
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logged out successfully'})
    except Exception:
        return Response({'message': 'Logged out'})


# ============== CONVERSATION VIEWS ==============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_conversations(request):
    """
    List all conversations for the authenticated user.
    
    GET /api/conversations/
    """
    conversations = Conversation.objects.filter(user=request.user)
    serializer = ConversationListSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    """
    Create a new conversation.
    
    POST /api/conversations/
    Body: { "title": "Optional title" }
    """
    title = request.data.get('title', 'New Chat')
    conversation = Conversation.objects.create(user=request.user, title=title)
    serializer = ConversationSerializer(conversation)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation(request, conversation_id):
    """
    Get a specific conversation with all messages.
    
    GET /api/conversations/<id>/
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """
    Delete a conversation.
    
    DELETE /api/conversations/<id>/
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        conversation.delete()
        return Response({'message': 'Conversation deleted'})
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_conversation(request, conversation_id):
    """
    Update conversation title.
    
    PATCH /api/conversations/<id>/
    Body: { "title": "New Title" }
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        title = request.data.get('title')
        if title:
            conversation.title = title
            conversation.save()
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)


# ============== CHAT VIEWS ==============

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow anonymous chat, or change to IsAuthenticated
def chat(request):
    """
    Handle chat requests. Saves messages to database if user is authenticated.
    
    POST /api/chat/
    Body: { 
        "message": "user message", 
        "conversation_id": 1,  // optional, creates new if not provided
        "history": [...]  // optional, for anonymous users
    }
    """
    try:
        message = request.data.get('message')
        conversation_id = request.data.get('conversation_id')
        history = request.data.get('history', [])
        
        if not message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        conversation = None
        
        # If user is authenticated, save to database
        if request.user.is_authenticated:
            # Get or create conversation
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id, user=request.user)
                except Conversation.DoesNotExist:
                    return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
            else:
                # Create new conversation with first message as title
                title = message[:50] + "..." if len(message) > 50 else message
                conversation = Conversation.objects.create(user=request.user, title=title)
            
            # Save user message
            ChatMessage.objects.create(
                conversation=conversation,
                role='user',
                content=message
            )
            
            # Build history from database
            history = [
                {'role': msg.role, 'content': msg.content}
                for msg in conversation.messages.all()
            ]
        
        # Get AI response
        result = assistant.chat(message, history)
        
        # Save assistant response if authenticated
        if conversation:
            ChatMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=result['response'],
                has_news_context=result.get('has_news_context', False)
            )
            conversation.save()  # Update updated_at timestamp
        
        response_data = {
            'response': result['response'],
            'has_news_context': result.get('has_news_context', False)
        }
        
        if conversation:
            response_data['conversation_id'] = conversation.id
            response_data['conversation'] = ConversationSerializer(conversation).data
        else:
            response_data['history'] = result['conversation_history']
        
        return Response(response_data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_conversation(request):
    """Reset conversation history (for anonymous users)"""
    return Response({'message': 'Conversation reset', 'history': []})
