from .ai.mentor import MentorService

mentor = None


def get_mentor():
    global mentor
    if mentor is None:
        mentor = MentorService("1")
    return mentor
