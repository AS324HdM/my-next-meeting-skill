from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_file_handler
from datetime import datetime, timedelta, time, date
import caldav
from caldav.elements import dav, cdav
from dateutil import tz


class MyNextMeeting(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()

    def on_settings_changed(self):
        self.userName = self.settings.get('username')
        self.password = self.settings.get('password')
        self.caldav = "https://{}:{}@next.social-robot.info/nc/remote.php/dav".format(self.userName, self.password)

    @intent_file_handler('meeting.next.my.intent')
    def handle_meeting_next_my(self, message):
        self.login_to_nextcloud()
        apmnt_Date, apmnt_Time, apmnt_Title =  self.get_next_appointment_info()
        self.log.info("cal:",self.caldav, self.userName, self.password)
        self.speak('Your next appointment is on {} at {} and is entitled {}'
            .format(apmnt_Date, apmnt_Time, apmnt_Title))
    
    def login_to_nextcloud(self):
        #login to nextcloud
        self.client = caldav.DAVClient(self.caldav)
        self.principal = self.client.principal()
        self.calendars = self.principal.calendars()
        self.calendar = self.calendars[0]

    def get_next_appointment_info(self):
        apmnt_Date = "June 22, 2020"
        apmnt_Time = "4 pm"
        apmnt_Title = "Speech Interaction class"
        return apmnt_Date, apmnt_Time, apmnt_Title

    def stop(self):
        pass


def create_skill():
    return MyNextMeeting()

