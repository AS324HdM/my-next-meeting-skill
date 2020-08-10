# -*- coding: utf-8 -*-
# pylint: disable=unidiomatic-typecheck
"""Mycroft Skill that handles requests on a private NextCloud calendar.

This Skill is activated via Mycroft by one of the key sentences in meeting.my.next.intent.
Settings can be changed via Mycroft profile. The settings are defined in settingsmeta.yaml.
They include neccessary login information for NextCloud.

  Typical usage example:

  Q: "Hey Mycroft, when is my next appointment?"
  A: "Your next appointment is on June 22th at 12:30 and is entitled Speech Interaction Class"
"""
import re
from datetime import datetime, timedelta, time, date, timezone
from pytz import timezone as tz
from dateutil.relativedelta import relativedelta
import caldav
from caldav.elements import dav, cdav
# from tzlocal import get_localzone
from adapt.intent import IntentBuilder # import for Mycroft only works internaly pylint: disable=import-error
from mycroft.util.parse import extract_duration, extract_datetime # import for Mycroft only works internaly pylint: disable=import-error
from mycroft import MycroftSkill, intent_file_handler # import for Mycroft only works internaly pylint: disable=import-error
from mycroft.util.format import nice_date, nice_date_time # import for Mycroft only works internaly pylint: disable=import-error

class MyNextMeeting(MycroftSkill): # attributes neccessary pylint: disable=too-many-instance-attributes
    """Main Class for the Skill.

    Attributes:
        caldav (str): URL for NextCloud Login, from settings.
        calendar (obj): object to get all calendar information from.
    """

    def __init__(self):
        """__init__ Method in Mycroft Skill Lifecycle.

        The __init__ method is called when the Skill is first constructed.
        It is used to declare variables or perform setup actions.
        However it cannot utilize other MycroftSkill methods and
        properties as the class does not yet exist.
        This includes self.settings which must instead be called
        from the Skill's initialize method.
        """
        MycroftSkill.__init__(self)
        self.timezone = "Europe/Berlin"
        self.caldav = ""
        self.calendar = {}

    def initialize(self):
        """Method in Mycroft Skill Lifecycle.

        The initialize method is called after the Skill is
        fully constructed and registered with the system.
        It is used to perform any final setup for the Skill
        including accessing Skill settings.
        """
        self.register_entity_file('day.entity')
        self.register_entity_file('month.entity')
        self.settings_change_callback = self.on_settings_changed # pylint: disable=attribute-defined-outside-init
        self.on_settings_changed()

    def on_settings_changed(self):
        """Get settings from Mycroft profile for NextCloud Login.
        """
        user_name = self.settings.get('username')
        password = self.settings.get('password')
        self.timezone = self.settings.get('timezone')
        self.caldav = "https://{}:{}@next.social-robot.info/nc/remote.php/dav" \
            .format(user_name, password)

    def login_to_nextcloud(self):
        """Log in to NextCloud and get the calendar.

        Uses the caldav-URL to get the users calendar Information from Nextcloud.
        """
        client = caldav.DAVClient(self.caldav)
        principal = client.principal()
        calendars = principal.calendars()
        self.calendar = calendars[0]

    @intent_file_handler('meeting.next.my.intent')
    def handle_meeting_next_my(self):
        """Method is called when user speaks an intent in ``meeting.next.my.intent``.

        Calls the methods login_to_nextcloud() and get_appointment_info() to get
        the info of the users next appointment and gives the answer.

        speak() is a build-in MycroftSkill method, to let mycroft speak to the user.
        """
        self.login_to_nextcloud()
        apmnt_date_time, apmnt_title = self.get_appointment_info()
        if len(apmnt_date_time) > 0:
            self.speak_dialog('meeting.next.my', \
                data={"date_time": apmnt_date_time, "title": apmnt_title})
        else:
            self.speak('You Don\'t have any appointments planned')

    @intent_file_handler('meetings.at.day.intent')
    def handle_meetings_at_day(self, message):
        """Method is called when user speaks an intent in ``meetings.at.day.intent``.

        Calls the methods login_to_nextcloud() and get_appointment_info() to get
        the info of the users next appointment and gives the answer, for a specific day.

        speak() is a build-in MycroftSkill method, to let mycroft speak to the user.
        """
        self.login_to_nextcloud()
        try:
            start = get_date(message.data)
            list_of_events = self.get_appointment_info(from_start=start, days=1, get_next=False)
            if len(list_of_events) > 0:
                self.log.info(list_of_events)
                events_string = ' and '.join(event[1]+event[0]\
                    for event in list_of_events)
                self.speak('On '+nice_date(start)+\
                    ' you have the following appointments: '+\
                        events_string)
            else:
                self.speak('You Don\'t have any appointments planned')
        except TypeError:
            self.speak('Sorry, I need you to tell me a month and day')

    @intent_file_handler('meeting.create.intent')
    def handle_meeting_create(self, message):
        """Method is called when user speaks an intent in ``meeting.next.my.intent``.

        Calls the methods login_to_nextcloud() and get_next_appointment_info() to get
        the info of the users next appointment and gives the answer.

        speak() is a build-in MycroftSkill method, to let mycroft speak to the user.
        """
        self.login_to_nextcloud()
        try:
            name = message.data.get('name')
            date_u = get_date(message.data)

            self.create_event(name, date_u)
            self.speak_dialog('meeting created')
        except TypeError:
            self.speak('Sorry, cannot create event, I need you to tell me a month and day')

    def create_event(self, name, date_u):
        """Create an event for the NextCloud calendar.
        Args:
            name (string): The name of the event.
            date_u (datetime): The date of the event.
        Returns:
            True (bool): True. 
        """
        date_full = date_u.strftime("%Y%m%d")
        now = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        uid = datetime.now().timestamp()
        new_event = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp.//CalDAV Client//EN
BEGIN:VEVENT
UID: {}
DTSTAMP:{}
DTSTART;VALUE=DATE:{}
SUMMARY:{}
END:VEVENT
END:VCALENDAR"""
        new_event = new_event.format(uid, now, date_full, name)
        self.calendar.save_event(new_event)
        self.log.info('Create event was successful')
        return True

    @intent_file_handler('meeting.delete.intent')
    def handle_meeting_delete(self, message):
        """Method is called when user speaks an intent in ``meeting.next.my.intent``.

        Calls the methods login_to_nextcloud() and get_next_appointment_info() to get
        the info of the users next appointment and gives the answer.

        speak() is a build-in MycroftSkill method, to let mycroft speak to the user.
        """
        self.login_to_nextcloud()
        try:
            date_u = get_date(message.data)
            events = self.calendar.date_search(date_u, date_u + timedelta(1))
            summary = ""
            if len(events) > 0:
                summary = events[0].instance.vevent.summary.value
                events[0].delete()
                self.speak('event: '+summary+' deleted')
            else:
                self.speak('Sorry, no event to delete')
        except TypeError:
            self.speak('Sorry, no event to delete, I need you to tell me a month and day')

    @intent_file_handler('meeting.rename.intent')
    def handle_meeting_rename(self, message):
        """Method is called when user speaks an intent in ``meeting.next.my.intent``.

        Calls the methods login_to_nextcloud() and get_next_appointment_info() to get
        the info of the users next appointment and gives the answer.

        speak() is a build-in MycroftSkill method, to let mycroft speak to the user.
        """
        self.login_to_nextcloud()
        date_u = extract_datetime(message.data.get('date'))[0]
        events = self.calendar.date_search(date_u, date_u + timedelta(1))
        name = message.data.get('name')
        summary = ""
        if len(events) > 0:
            summary = events[0].instance.vevent.summary.value
            events[0].vobject_instance.vevent.summary.value = name
            events[0].save()
            self.speak('event: '+summary+' renamed to '+name)
        else:
            self.speak('Sorry, no event to rename')

    def get_appointment_info(self, from_start=None, days=30, get_next=True):
        """Get the next appointment from the NextCloud calendar.

        Args:
            from_start (timestamp): Start date to look next appointment up from.
            If None, from now on.
            days (int): The Range of time to look up from ``from_start`` on.
            F.e. if ``from_start`` is 1.10, it will look up only the Time from 1.10 to 31.10.
            get_next(bool): If True, just the next appointment. If False, all appointments.

        Returns:
            (array): Array of the three Strings apmnt_date, apmnt_time, apmnt_title
        """
        start = datetime.utcnow()
        if from_start is not None:
            start = from_start + timedelta(0)
            self.log.info(start)
        end = start + timedelta(days)
        self.log.info(end)
        results = self.calendar.date_search(start, end)
        self.log.info("results:", results)
        events = []
        for event in results:
            start_e = event.instance.vevent.dtstart.value
            if type(start_e) is datetime:
                start_e = self.utc_to_local(start_e)
            summary = event.instance.vevent.summary.value
            events.append([start_e, summary])
        if len(events) > 0:
            events = sorted(events, key=lambda event: \
                self.utc_to_local(datetime.combine(event[0], datetime.min.time()))\
                    if type(event[0]) is date else event[0])
            if get_next:
                event = events[0]
                return get_nice_event(events[0])
            return [get_nice_event(event, True) for event in events]
        self.log.info("There is no event")
        if get_next: 
            return []
        return "", ""

    def utc_to_local(self, date_arg):
        """Transforms time to local time.

        Args:
            date_arg (datetime): UTC datetime Object

        Returns:
            (datetime): Local datetime Object
        """
        time_zone = tz(self.timezone)
        return date_arg.astimezone(time_zone).replace(tzinfo=None)

def get_date(message_data):
    """get a datetime from input.

    Args:
        message_data (object): all data input from user

    Returns:
        (datetime): datetime Object
    """
    day = int(re.findall(r'\d+', message_data.get('day'))[0])
    month = month_to_num(message_data.get('month'))
    now = datetime.now()
    year = int(now.year)
    return datetime(year, month, day)

def get_nice_event(event, is_on_date=False):
    """Transforms Events nicely spoken for Mycroft.

    nice_date() and nice_time() are functions from Mycroft.util.format that
    uses Lingua Franca to transform numbers and dates etc. to words.
    see mycroft.ai documentation at:
    https://mycroft-ai.gitbook.io/docs/mycroft-technologies/lingua-franca

    Args:
        event: Event extracted from Nextcloud.

    Returns:
        apmnt_date_time (str): The Date and Time of the next appointment  nicely spoken String.
        apmnt_title (str): The Title of the Appointment.
    """
    if type(event[0]) is date:
        apmnt_date_time = nice_date(event[0]) + ", all day "
        if is_on_date:
            apmnt_date_time = ", all day"
    else:
        apmnt_date_time = nice_date_time(event[0])
        if is_on_date:
            apmnt_date_time = ", at " + apmnt_date_time
    apmnt_title = str(event[1])
    return apmnt_date_time, apmnt_title

def month_to_num(month):
    """Transforms the spoken month to numbers.

    Args:
        month (str): spoken month

    Returns:
        (int): Number of month
    """
    switcher = {
        "january":1,
        "february":2,
        "march":3,
        "april":4,
        "may":5,
        "june":6,
        "july":7,
        "august":8,
        "september":9,
        "october":10,
        "november":11,
        "december":12
    }
    return switcher.get(month, "Invalid month")

def create_skill():
    """Create the skill instance

    This is required by Mycroft and is responsible for actually creating an instance of the Skill
    that Mycroft can load.
    """
    return MyNextMeeting()
