# -*- coding: utf-8 -*-
"""Mycroft Skill that handles requests on a private NextCloud calendar.

This Skill is activated via Mycroft by one of the key sentences in meeting.my.next.intent.
Settings can be changed via Mycroft profile. The settings are defined in settingsmeta.yaml.
They include neccessary login information for NextCloud.

  Typical usage example:

  Q: "Hey Mycroft, when is my next appointment?"
  A: "Your next appointment is on June 22th at 12:30 and is entitled Speech Interaction Class"
"""

from datetime import datetime, timedelta, time, date
import caldav
from caldav.elements import dav, cdav
from dateutil import tz
from adapt.intent import IntentBuilder # import for Mycroft only works internaly pylint: disable=import-error
from mycroft import MycroftSkill, intent_file_handler # import for Mycroft only works internaly pylint: disable=import-error

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
        self.caldav = ""
        self.calendar = {}

    def initialize(self):
        """Method in Mycroft Skill Lifecycle.

        The initialize method is called after the Skill is
        fully constructed and registered with the system.
        It is used to perform any final setup for the Skill
        including accessing Skill settings.
        """
        self.settings_change_callback = self.on_settings_changed # pylint: disable=attribute-defined-outside-init
        self.on_settings_changed()

    def on_settings_changed(self):
        """Get settings from Mycroft profile for NextCloud Login.
        """
        user_name = self.settings.get('username')
        password = self.settings.get('password')
        self.caldav = "https://{}:{}@next.social-robot.info/nc/remote.php/dav" \
            .format(user_name, password)

    @intent_file_handler('meeting.next.my.intent')
    def handle_meeting_next_my(self):
        """Method is called when user speaks an intent in ``meeting.next.my.intent``.

        Calls the methods login_to_nextcloud() and get_next_appointment_info() to get
        the info of the users next appointment and gives the answer.

        speak() is a build-in MycroftSkill method, to let mycroft speak to the user.
        """
        self.login_to_nextcloud()
        apmnt_date, apmnt_time, apmnt_title = self.get_next_appointment_info()
        if len(apmnt_date) > 0:
            self.speak('Your next appointment is on {} at {} and is entitled {}' \
                .format(apmnt_date, apmnt_time, apmnt_title))
        else:
            self.speak('You Don\'t have any appointments planned')

    def login_to_nextcloud(self):
        """Log in to NextCloud and get the calendar.

        Uses the caldav-URL to get the users calendar Information from Nextcloud.
        """
        client = caldav.DAVClient(self.caldav)
        principal = client.principal()
        calendars = principal.calendars()
        self.calendar = calendars[0]

    def get_next_appointment_info(self, from_start=None, days=30):
        """Get the next appointment from the NextCloud calendar.

        Args:
            from_start (timestamp): Start date to look next appointment up from.
            If None, from now on.
            days (int): The Range of time to look up from ``from_start`` on.
            F.e. if ``from_start`` is 1.10, it will look up only the Time from 1.10 to 31.10.

        Returns:
            apmnt_date (str): The Date of the next appointment as String.
            apmnt_time (str): The Time of the occasion.
            apmnt_title (str): The Title of the Appointment.
        """
        if from_start is not None:
            start = from_start
        end = start + timedelta(days)
        results = self.calendar.date_search(start, end)
        if results is None:
            self.log.info("There is no event")
            return "", "", ""
        events = []
        for event in results:
            start_e = event.instance.vevent.dtstart.value
            if not hasattr(start_e, 'time'):
                start_e = datetime.combine(start_e, datetime.min.time())
            day = start_e.date().strftime('%d, %b %Y')
            day_time = start_e.time().strftime('%H:%M %p')
            summary = event.instance.vevent.summary.value
            events.append([day, day_time, summary])
        events = sorted(events, key=lambda event: event[1] and event[0])
        event = events[0]
        apmnt_date = event[0]#"F.e. June 22, 2020"
        apmnt_time = event[1]#"F.e. 4 pm"
        apmnt_title = str(event[2])
        return apmnt_date, apmnt_time, apmnt_title


def create_skill():
    """Create the skill instance

    This is required by Mycroft and is responsible for actually creating an instance of the Skill
    that Mycroft can load.
    """
    return MyNextMeeting()
