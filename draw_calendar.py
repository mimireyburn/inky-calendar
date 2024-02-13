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
        self.events_dict = {}

        self.font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 18)
        self.small_font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 13)
        self.img = Image.new('RGB', (self.width, self.height), color='white')
        self.d = ImageDraw.Draw(self.img)


    def load_credentials(self):
        with open("KEY.json") as f:
            data = json.load(f)
        self.cal_id = data["calendar_id"]
        self.demo_id = data["demo_id"]
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
            if event["organizer"]["email"] == self.demo_id:
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
            # Make background blue
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
                if len(self.events_dict[date][i][0]) > 19:
                    self.events_dict[date][i][0] = self.events_dict[date][i][0][:18] + "..."
                # if self.events_dict[date][i][1] != self.cal_id:
                    # text_colour = self.colors['external_event']
                if " w " in self.events_dict[date][i][0]: 
                    text_colour = self.colors['external_event']
                else:
                    text_colour = self.colors['internal_event']
                self.d.text((math.floor(self.box_width*day_of_week) + 5, self.top_padding + self.box_padding + (week*self.box_height) + (i*self.event_height)), self.events_dict[date][i][0], font=self.small_font, fill=text_colour)

    
    def save_image(self):
        self.img.save('calendar_image.png')


if __name__ == "__main__":
    cal_img = CalendarImage()
    # month view
    WEEKS = 4
    today = datetime.datetime.today()
    prev_monday = today - datetime.timedelta(days=today.weekday())
    start_time = prev_monday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_time = (prev_monday + datetime.timedelta(days=(WEEKS * 7) - 1)).replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z"
    
    # week view
    # start_time = (datetime.datetime.utcnow() - datetime.timedelta(days=datetime.datetime.utcnow().weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    # end_time = (datetime.datetime.utcnow() + datetime.timedelta(days=6-datetime.datetime.utcnow().weekday())).replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z" 
    
    events = cal_img.get_events(start_time, end_time)
    cal_img.populate_events_dict(events)

    # cal_img.draw_week()
    # cal_img.draw_week_events()

    cal_img.draw_month()
    cal_img.draw_month_events()

    cal_img.save_image()
