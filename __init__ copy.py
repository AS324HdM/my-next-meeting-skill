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
        self.client = caldav.DAVClient(self.caldav)
        self.principal = self.client.principal()
        self.calendars = self.principal.calendars()
        self.calendar = self.calendars[0]

    def get_next_appointment_info(self):
        now = datetime.now()
        end = now + timedelta(1)
        results = self.calendar.date_search(now, end)
        list = []
        for event in results:
            start = event.instance.vevent.dtstart.value
            day = start.date().strftime('%d, %b %Y')
            time = start.time().strftime('%H:%M %p')
            summary = event.instance.vevent.summary.value
            list.append([day, time, summary])
        list.sort()
        event = list[0]
        apmnt_Date = event[0]#"June 22, 2020"
        apmnt_Time = event[1]#"4 pm"
        apmnt_Title = str(event[2])
        return apmnt_Date, apmnt_Time, apmnt_Title

    def stop(self):
        pass


def create_skill():
    return MyNextMeeting()

