from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler


class MyNextMeeting(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()
        self.login_to_nextcloud()

    def on_settings_changed(self):
        self.caldav = self.settings.get('caldav')
        self.userName = self.settings.get('username')
        self.password = self.settings.get('password')

    @intent_file_handler('meeting.next.my.intent')
    def handle_meeting_next_my(self, message):
        apmnt_Date, apmnt_Time, apmnt_Title =  self.get_next_appointment_info()
        self.speak('Your next appointment is on {} at {} and is entitled {}'
            .format(apmnt_Date, apmnt_Time, apmnt_Title))
    
    def login_to_nextcloud(self):
        #login to nextcloud
        self.log.info("caldav:",self.caldav)
        self.log.info("username:",self.userName)
        self.log.info("password:",self.password)

    def get_next_appointment_info(self):
        apmnt_Date = "June 22, 2020"
        apmnt_Time = "4 pm"
        apmnt_Title = "Speech Interaction class"
        return apmnt_Date, apmnt_Time, apmnt_Title

    def stop(self):
        pass


def create_skill():
    return MyNextMeeting()

