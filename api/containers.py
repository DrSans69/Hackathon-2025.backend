from ai.mentor import MentorService

mentor = None


def get_accounts_service():
    global mentor
    if mentor is None:
        mentor = MentorService("1")
    return mentor
