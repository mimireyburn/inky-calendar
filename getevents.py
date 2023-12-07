from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import datetime
import json

class GoogleCalendarFetcher:
    def __init__(self, credentials_file="KEY.json"):
        self.credentials_file = credentials_file
        self.calendar_service = self._initialize_calendar_service()
        self.events = []
        self.organizer_colors = {}
        self.colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33F6', '#57FF33', '#F633FF', '#33FFF6', '#FFC733', '#33D4FF', '#FF3380']  # Predefined colors
        self.color_index = 0  # To keep track of which color to assign next

    def _initialize_calendar_service(self):
        with open(self.credentials_file) as file:
            credentials_data = json.load(file)
        self.calendar_id = credentials_data["calendar_id"]
        credentials = Credentials.from_service_account_file(self.credentials_file)
        return build("calendar", "v3", credentials=credentials)

    def fetch_events(self, start_time, end_time):
        events_result = self.calendar_service.events().list(
            calendarId=self.calendar_id, timeMin=start_time, timeMax=end_time, 
            singleEvents=True, orderBy="startTime"
        ).execute()
        return events_result.get("items", [])
    
    def _get_color_for_organizer(self, organizer_email):
        if organizer_email not in self.organizer_colors:
            self.organizer_colors[organizer_email] = self.colors[self.color_index]
            self.color_index = (self.color_index + 1) % len(self.colors)  # Move to the next color and loop back if necessary
        return self.organizer_colors[organizer_email]

    def organize_events(self, events):
        for event in events:
            start_date = self._extract_date(event.get("start"))
            end_date = self._extract_date(event.get("end"))
            organizer_email = event.get("creator", {}).get("email", "")
            color = self._get_color_for_organizer(organizer_email)

            event_info = {
                "title": event["summary"],
                "start": start_date,
                "end": end_date,
                "color": color
            }
            if "dateTime" in event.get("start", {}):
                event_info["allDay"] = False

            self.events.append(event_info)

    def _extract_date(self, date_info):
        date_str = date_info.get("dateTime", date_info.get("date", ""))
        return date_str  # Extracts the 'YYYY-MM-DD' part
        
    def get_events_dict(self):
        return self.events

# Usage example
if __name__ == "__main__":
    calendar_fetcher = GoogleCalendarFetcher()

    # Define start and end times
    start_time = datetime.datetime.utcnow().isoformat() + "Z"
    end_time = (datetime.datetime.utcnow() + datetime.timedelta(days=28)).isoformat() + "Z"

    events = calendar_fetcher.fetch_events(start_time, end_time)
    calendar_fetcher.organize_events(events)

    # Print and save events list as JSON
    for event in calendar_fetcher.get_events_dict():
        print(json.dumps(event, indent=2))

    with open("events.json", "w") as file:
        json.dump(calendar_fetcher.get_events_dict(), file, indent=2)