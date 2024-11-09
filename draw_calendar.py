from PIL import Image, ImageDraw, ImageFont
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import datetime 
import re
import calendar
import os
from dotenv import load_dotenv
import math
import json 

class CalendarImage:
    def __init__(self):
        self.load_credentials()
        self.initialize_variables()        

    def initialize_variables(self):
        self.width = 800
        self.height = 480
        self.weeks = 4
        self.top_padding = 35
        self.box_padding = 30
        self.calendar_height = self.height - self.top_padding - 1
        self.box_height = math.floor(self.calendar_height / self.weeks)
        self.box_width = math.floor(self.width / 7)
        self.event_height = 16

        self.colors = {
            # Colour options are: "black", "white", "green", "blue", "red", "yellow", "orange"
            'outline': "black",
            'days': "black", # days of the week text
            'number': "black",
            'today_text': "white",
            'today_circle': "red",
            'background': "white",
            'internal_event': "blue",
            'external_event': "orange",
        }

        self.prev_monday = (datetime.datetime.utcnow() - datetime.timedelta(days=datetime.datetime.utcnow().weekday())) - datetime.timedelta(days=7)
        self.days_of_week = ["M", "T", "W", "T", "F", "S", "S"]
        self.long_days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.events_dict = {}

        self.font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 18)
        self.small_font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 13)
        self.tiny_font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 9)
        self.img = Image.new('RGB', (self.width, self.height), color='white')
        self.d = ImageDraw.Draw(self.img)


    def load_credentials(self):
        with open("KEY.json") as f:
            data = json.load(f)
        self.cal_id = data["calendar_id"]
        self.credentials = Credentials.from_service_account_file("KEY.json")
        self.service = build("calendar", "v3", credentials=self.credentials)


    def get_events(self, start_time, end_time):
        events_result = self.service.events().list(
            calendarId=self.cal_id, timeMin=start_time, timeMax=end_time, singleEvents=True, orderBy="startTime"
        ).execute()
        return events_result.get("items", [])


    def populate_events_dict(self, events):
        for event in events:
            start_date, end_date, time, end = self.extract_event_details(event)
            self.add_event_to_dict(start_date, [event["summary"], event["organizer"]["email"], time, end])


    def extract_event_details(self, event):
        try:
            start = event["start"]["dateTime"]
            end = event["end"]["dateTime"]
            start_date, time = start[:10], start
            end_date, end_time = end[:10], end
        except KeyError:
            start_date = event["start"]["date"]
            end_date = event["end"]["date"]
            time = "06:00"
            end_time = "06:30"
        return start_date, end_date, time, end_time


    def add_event_to_dict(self, date, event_details):
        if date in self.events_dict:
            self.events_dict[date].append(event_details)
        else:
            self.events_dict[date] = [event_details]


    def draw_month(self):
            self.d.rectangle([(0, 0), (self.width, self.height)], fill=self.colors['background'])

            year = datetime.datetime.utcnow().year
            month = datetime.datetime.utcnow().month

            # Draw capitalised month and year at top of calendar
            self.d.text((2,0), calendar.month_name[month][:3].upper() + " " + str(year), font=self.font, fill=self.colors['number'])

            # Draw calendar days_of_week at top of calendar
            for i in range(7):
                self.d.text((math.floor((self.width/7)*i) + math.floor(self.width/14), self.top_padding-15), self.days_of_week[i], font=self.small_font, fill=self.colors['days'])

            # Draw calendar days with labels from start_time to end_time
            for i in range(self.weeks):
                for j in range(7):
                    self.d.rectangle([(math.floor(self.box_width*j)+1, self.top_padding + (i*self.box_height)), (math.floor(self.box_width*(j+1))+1, self.top_padding + ((i+1)*self.box_height))], outline=self.colors['outline'], width=1)
                    
                    text_color = self.colors['number']

                    today = datetime.datetime.utcnow().date()
                    box_date = self.prev_monday.date() + datetime.timedelta(days=(i*7) + j)
                    radius = 11
                    if box_date == today:
                        self.d.ellipse([
                            (math.floor(self.box_width*(j+1) - 20) - radius, self.top_padding + (i*self.box_height) + 14 - radius), 
                            (math.floor(self.box_width*(j+1) - 20) + radius + 8, self.top_padding + (i*self.box_height) + 20 + radius)], fill=self.colors['today_circle'])
                        text_color = self.colors['today_text']

                    # If day is in next month            
                    if self.prev_monday.day + (i*7) + j > calendar.monthrange(self.prev_monday.year, self.prev_monday.month)[1]:
                        self.d.text((math.floor(self.box_width*(j+1) - 25), self.top_padding + (i*self.box_height) + 5), str(self.prev_monday.day + (i*7) + j - calendar.monthrange(self.prev_monday.year, self.prev_monday.month)[1]), font=self.font, fill=text_color)
                    else:
                        self.d.text((math.floor(self.box_width*(j+1) - 25), self.top_padding + (i*self.box_height) + 5), str(self.prev_monday.day + (i*7) + j), font=self.font, fill=text_color)


    def draw_month_events(self):
        # Draw events on calendar
        for date in self.events_dict:
            # Get day of week of event
            day_of_week = datetime.datetime.strptime(date, "%Y-%m-%d").weekday()
            # Get week of event
            week = math.floor((datetime.datetime.strptime(date, "%Y-%m-%d") - self.prev_monday.replace(hour=0, minute=0, second=0, microsecond=0)).days / 7) 
            # Get number of events on day
            num_events = len(self.events_dict[date])
            # Draw each event
            for i in range(num_events):
                # truncate event name if too long
                if len(self.events_dict[date][i][0]) > 17:
                    self.events_dict[date][i][0] = self.events_dict[date][i][0][:16] + ".."
                
                if self.cal_id in self.events_dict[date][i][1]: 
                    text_colour = self.colors['internal_event']
                else:
                    text_colour = self.colors['external_event']
                self.d.text((math.floor(self.box_width*day_of_week) + 5, self.top_padding + self.box_padding + (week*self.box_height) + (i*self.event_height)), self.events_dict[date][i][0], font=self.small_font, fill=text_colour)

    
    def draw_week(self): 
        self.d.rectangle([(0, 0), (self.width, self.height)], fill=self.colors['background'])

        year = datetime.datetime.utcnow().year
        month = datetime.datetime.utcnow().month
        today = datetime.datetime.utcnow().date()
        
        # Draw capitalised month and year at top of calendar
        self.d.text((2,0), calendar.month_name[month][:3].upper() + " " + str(year), font=self.font, fill=self.colors['number'])

        # Draw calendar days_of_week at top of calendar
        for i in range(7):
            left_padding = 20
            width =(self.width - left_padding) / 7 
            
            self.d.text((math.floor(width*i) + math.floor(width/14) + left_padding + 30, self.top_padding-15), self.long_days_of_week[i], font=self.small_font, fill=self.colors['days'])
        
            date_number = self.prev_monday.day + 6 + i 
            if date_number >= calendar.monthrange(year, month)[1]:
                date_number = date_number - calendar.monthrange(year, month)[1]

            if date_number == today.day:
                radius = 9
                text_color = self.colors['today_text']
                self.d.ellipse([
                    (math.floor(width*i) + math.floor(width/14) + left_padding + 60 - radius, self.top_padding - 9  - radius), 
                    (math.floor(width*i) + math.floor(width/14) + left_padding + 60 + radius + 8, self.top_padding - 5 + radius)], fill=self.colors['today_circle'])
                
                self.d.text((math.floor(width*i) + math.floor(width/14) + left_padding + 60, self.top_padding-15), str(date_number), font=self.small_font, fill=text_color)     
            else:   
                self.d.text((math.floor(width*i) + math.floor(width/14) + left_padding + 60, self.top_padding-15), str(date_number), font=self.small_font, fill=self.colors['number'])
                
        # Draw vertical lines to separate days of the week
        for i in range(1, 7):  # There are 6 lines to draw for 7 days
            x_position = width * i + left_padding
            self.d.line([(x_position, 0), (x_position, self.height)], fill=self.colors['outline'], width=2)


        # Draw horizontal lines to indicate hours in grey
        hour_height = self.height / 18  # Assuming a 24-hour format
        for hour in range(18):
            y_position = hour * hour_height + self.top_padding + 25
            self.d.line([(0, y_position), (self.width, y_position)], fill='lightgrey', width=1)
        # Draw labels for hours on the left-hand side
        for hour in range(7, 23):  # From 07:00 to 22:00
            y_position = (hour - 7) * hour_height + self.top_padding + 25  # Adjust position based on hour
            self.d.text((5, y_position), f"{hour:02}:00", font=self.small_font, fill=self.colors['number'])
    
    def draw_week_events(self):
        # Define hour_height at the beginning of the method
        hour_height = self.height / 18  # Assuming a 24-hour format

        for date, events in self.events_dict.items():
            for event in events:
                try: 
                    event_start = datetime.datetime.fromisoformat(event[2][:-1])
                    event_end = datetime.datetime.fromisoformat(event[3][:-1])

                    # Calculate positions
                    start_time = (self.prev_monday + datetime.timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
                    day_index = (event_start.date() - datetime.datetime.fromisoformat(start_time[:-1]).date()).days
                    if day_index < 0 or day_index >= 7:
                        continue  # Skip events that are not in the current week

                    start_hour = event_start.hour + event_start.minute / 60
                    end_hour = event_end.hour + event_end.minute / 60

                    start_y = (start_hour - 7) * hour_height + self.top_padding + 25
                    end_y = (end_hour - 7) * hour_height + self.top_padding + 25

                    left_padding = 20
                    width = (self.width - left_padding) / 7
                    x_position = day_index * width + left_padding + 5

                    # Draw event rectangle
                    self.d.rectangle([(x_position, start_y), (x_position + width - 10, end_y)], fill=self.colors['internal_event'], outline=self.colors['outline'])

                    # Draw event text
                    event_text = event[0]
                    self.d.text((x_position + 5, start_y + 2), event_text, font=self.tiny_font, fill=self.colors['today_text'])
                except Exception as e:
                    print(e)
                    print(event)
    def save_image(self):
        self.img.save('calendar_image.png')
