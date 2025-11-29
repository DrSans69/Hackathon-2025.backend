from django.urls import include, path

from . import views

urlpatterns = [
    path("hello/", views.hello),
    # Course endpoints
    path("courses/", views.list_courses, name="list_courses"),
    path("courses/create/", views.create_course, name="create_course"),
    path("courses/<int:course_id>/", views.get_course, name="get_course"),
    # Topic endpoints
    path("topics/", views.list_topics, name="list_topics"),
    path("topics/create/", views.create_topic, name="create_topic"),
    path("topics/<int:topic_id>/", views.get_topic, name="get_topic"),
    path("topics/<int:topic_id>/update/", views.update_topic, name="update_topic"),
    # Chat endpoints
    path("chats/", views.list_chats, name="list_chats"),
    path("chats/create/", views.create_chat, name="create_chat"),
    path("chats/<int:chat_id>/", views.get_chat, name="get_chat"),
    # Message endpoints
    path("messages/add/", views.add_message, name="add_message"),
    path("messages/send/", views.send_message_with_ai, name="send_message_with_ai"),
]
