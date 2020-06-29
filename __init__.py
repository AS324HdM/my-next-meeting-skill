from mycroft import MycroftSkill, intent_file_handler


class MyNextMeeting(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('meeting.next.my.intent')
    def handle_meeting_next_my(self, message):
        self.speak_dialog('meeting.next.my')


def create_skill():
    return MyNextMeeting()

