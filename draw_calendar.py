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
        self.WIDTH = 800
        self.HEIGHT = 480
        self.WEEKS = 5
        self.TOP_PADDING = 35
        self.BOX_PADDING = 30
        self.CALENDAR_HEIGHT = self.HEIGHT - self.TOP_PADDING - 1
        self.BOX_HEIGHT = math.floor(self.CALENDAR_HEIGHT / self.WEEKS)
        self.BOX_WIDTH = math.floor((self.WIDTH)/ 7)-0.25
        self.EVENT_HEIGHT = 16

        self.outline_colour = "white"
        self.outline_width = 1
        self.days_colour = "white"  
        self.number_colour = "white"
        self.day_txt_colour = "blue"
        self.day_cl_colour = "yellow"
        self.bg_colour = "blue"
        self.my_event_colour = "white"
        self.ext_event_colour = "orange"

        self.wk_day_colour = "black"
        self.wk_event_text = "white"
        self.wk_ext_event_colour = "orange"
        self.wk_outline_colour = "black"
        self.wk_event_colour = "blue"
        self.wk_event_radius = 5
        self.wk_today_colour = "red"


        self.prev_monday = (datetime.datetime.utcnow() - datetime.timedelta(days=datetime.datetime.utcnow().weekday())) - datetime.timedelta(days=7)
        self.days_of_week = ["M", "T", "W", "T", "F", "S", "S"]
        self.events_dict = {}

        self.font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 18)
        self.small_font = ImageFont.truetype("AtkinsonHyperlegible-Regular.ttf", 12)
        self.img = Image.new('RGB', (self.WIDTH, self.HEIGHT), color='white')
        self.d = ImageDraw.Draw(self.img)


    def load_credentials(self):
        with open("KEY.json") as f:
            data = json.load(f)
        self.CAL_ID = data["calendar_id"]
        self.credentials = Credentials.from_service_account_file("KEY.json")
        self.service = build("calendar", "v3", credentials=self.credentials)

    def get_events(self, start_time, end_time):
        events_result = self.service.events().list(
            calendarId=self.CAL_ID, timeMin=start_time, timeMax=end_time, singleEvents=True, orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        return events


    def populate_events_dict(self, events):
        for event in events:
            try:
                start_date = event["start"]["dateTime"][:10]
                end_date = event["end"]["dateTime"][:10]
                time = event["start"]["dateTime"]
                end = event["end"]["dateTime"]
            except:
                start_date = event["start"]["date"]
                end_date = event["end"]["date"]
                time = "06:00"
                end = "06:30"

            if end_date != start_date:
                self.events_dict


            if start_date in self.events_dict:
                self.events_dict[start_date].append([event["summary"], event["creator"]["email"], time, end])
            else:
                self.events_dict[start_date] = [[event["summary"], event["creator"]["email"], time, end]]
        return self.events_dict


    def draw_week(self):

        year = datetime.datetime.utcnow().year
        month = datetime.datetime.utcnow().month
        # Draw capitalised month and year at top of calendar
        self.d.text((2,0), calendar.month_name[month] + " " + str(year), font=self.font, fill=self.wk_day_colour)

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        today = datetime.datetime.today()
        prev_monday = today - datetime.timedelta(days=today.weekday())
        num_days = 6  # Sunday is 6 days after Monday
        num_dates = num_days + 1  # Add 1 to include Monday
        dates = [prev_monday + datetime.timedelta(days=i) for i in range(num_dates)]
        dates = [date.strftime("%d") for date in dates]
        dates = [re.sub("^0", "", date) for date in dates]

        WEEK_WIDTH = (self.WIDTH - self.TOP_PADDING - 10) 
        WEEK_HEIGHT = (self.HEIGHT - self.TOP_PADDING)
        
        # Draw calendar days_of_week at top of calendar from (TOP PADDING, TOP PADDING)
        for i in range(7):
            # Draw vertical lines for each day
            self.d.line([(math.floor((WEEK_WIDTH/7)*(i+1)) + math.floor(WEEK_WIDTH/14), self.TOP_PADDING), (math.floor((WEEK_WIDTH/7)*(i+1)) + math.floor(WEEK_WIDTH/14), self.HEIGHT)], fill=self.wk_outline_colour, width=self.outline_width)
            # Draw weekday followed by date number in centre of each column 
            # If date is today, draw red circle around it 
            text_colour = self.wk_day_colour
            if int(dates[i]) == today.day:
                text_colour = "white"
                self.d.ellipse([
                    (math.floor((WEEK_WIDTH/7)*i) + math.floor(WEEK_WIDTH/14) + self.TOP_PADDING + 22, self.TOP_PADDING - 16), 
                    (math.floor((WEEK_WIDTH/7)*i) + math.floor(WEEK_WIDTH/14) + self.TOP_PADDING + 40, self.TOP_PADDING + 2)], fill=self.wk_today_colour)
            # Draw weekday and date number separately 
            self.d.text((math.floor((WEEK_WIDTH/7)*i) + math.floor(WEEK_WIDTH/14) + self.TOP_PADDING, self.TOP_PADDING - 15), weekdays[i], font=self.small_font, fill=self.wk_day_colour)
            self.d.text((math.floor((WEEK_WIDTH/7)*i) + math.floor(WEEK_WIDTH/14) + self.TOP_PADDING + 25, self.TOP_PADDING - 15), dates[i], font=self.small_font, fill=text_colour)

        # Write time labels for each hour from 06:00 to 00:00
        for i in range(18):
            # Draw horizontal lines for each hour
            self.d.line([(math.floor(WEEK_WIDTH/14), self.TOP_PADDING + (i*WEEK_HEIGHT/18)), (self.WIDTH, self.TOP_PADDING + (i*WEEK_HEIGHT/18))], fill=self.wk_outline_colour, width=self.outline_width)
            # Draw time label for each hour
            self.d.text((10, self.TOP_PADDING - 7+ (i*WEEK_HEIGHT/18)), str(i+6) + ":00", font=self.small_font, fill=self.wk_outline_colour)
            
            

    def draw_week_events(self):
        WEEK_WIDTH = (self.WIDTH - self.TOP_PADDING -10)
        APPT_HEIGHT = (self.HEIGHT - self.TOP_PADDING)/18
        # Draw events on calendar
        for date in self.events_dict:
            # Get day of week of event
            day_of_week = datetime.datetime.strptime(date, "%Y-%m-%d").weekday()
            # Get number of events on day
            num_events = len(self.events_dict[date])
            # Draw each event
            for i in range(num_events):
                # truncate event name if too long
                if len(self.events_dict[date][i][0]) > 18:
                    self.events_dict[date][i][0] = self.events_dict[date][i][0][:17] + "..."
                if self.events_dict[date][i][1] != self.CAL_ID:
                    text_colour = self.wk_ext_event_colour
                else:
                    text_colour = self.wk_event_text
                
                # Draw event box based on how many hours event is 
                start_time = datetime.datetime.strptime(self.events_dict[date][i][2], "%H:%M")
                end_time = datetime.datetime.strptime(self.events_dict[date][i][3], "%H:%M")
                start_time = start_time.hour + (start_time.minute/60)
                end_time = end_time.hour + (end_time.minute/60)
 
                cal_start = 6.0
                start_time = start_time - cal_start
                end_time = end_time - cal_start

                self.d.rounded_rectangle([(math.floor((WEEK_WIDTH/7)*day_of_week) + math.floor(WEEK_WIDTH/14), self.TOP_PADDING + (start_time*APPT_HEIGHT)), (math.floor((WEEK_WIDTH/7)*day_of_week) + math.floor(WEEK_WIDTH/14)+ (self.BOX_WIDTH) -4, self.TOP_PADDING + (end_time*APPT_HEIGHT) )], radius=self.wk_event_radius, fill=self.wk_event_colour)
                self.d.text((math.floor((WEEK_WIDTH/7)*day_of_week) + math.floor(WEEK_WIDTH/14) + 5, self.TOP_PADDING + (start_time*APPT_HEIGHT)), self.events_dict[date][i][0], font=self.small_font, fill=text_colour)


    def draw_month(self):
            # Make background blue 
            self.d.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=self.bg_colour)

            year = datetime.datetime.utcnow().year
            month = datetime.datetime.utcnow().month
            # Draw capitalised month and year at top of calendar
            self.d.text((2,0), calendar.month_name[month][:3].upper() + " " + str(year), font=self.font, fill=self.number_colour)

            # Draw calendar days_of_week at top of calendar
            for i in range(7):
                self.d.text((math.floor((self.WIDTH/7)*i) + math.floor(self.WIDTH/14), self.TOP_PADDING-15), self.days_of_week[i], font=self.small_font, fill=self.days_colour)

            # Draw calendar days with labels from start_time to end_time
            for i in range(self.WEEKS):
                for j in range(7):
                    self.d.rectangle([(math.floor(self.BOX_WIDTH*j)+1, self.TOP_PADDING + (i*self.BOX_HEIGHT)), (math.floor(self.BOX_WIDTH*(j+1))+1, self.TOP_PADDING + ((i+1)*self.BOX_HEIGHT))], outline=self.outline_colour, width=self.outline_width)
                    
                    text_color = self.number_colour

                    today = datetime.datetime.utcnow().date()
                    box_date = self.prev_monday.date() + datetime.timedelta(days=(i*7) + j)
                    radius = 11
                    if box_date == today:
                        self.d.ellipse([
                            (math.floor(self.BOX_WIDTH*(j+1) - 20) - radius, self.TOP_PADDING + (i*self.BOX_HEIGHT) + 14 - radius), 
                            (math.floor(self.BOX_WIDTH*(j+1) - 20) + radius + 8, self.TOP_PADDING + (i*self.BOX_HEIGHT) + 20 + radius)], fill=self.day_cl_colour)
                        text_color = self.day_txt_colour
                                    
                    if self.prev_monday.day + (i*7) + j > calendar.monthrange(self.prev_monday.year, self.prev_monday.month)[1]:
                        self.d.text((math.floor(self.BOX_WIDTH*(j+1) - 25), self.TOP_PADDING + (i*self.BOX_HEIGHT) + 5), str(self.prev_monday.day + (i*7) + j + 1 - calendar.monthrange(year, month)[1]), font=self.font, fill=text_color)
                    else:
                        self.d.text((math.floor(self.BOX_WIDTH*(j+1) - 25), self.TOP_PADDING + (i*self.BOX_HEIGHT) + 5), str(self.prev_monday.day + (i*7) + j), font=self.font, fill=text_color)

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
                if len(self.events_dict[date][i][0]) > 18:
                    self.events_dict[date][i][0] = self.events_dict[date][i][0][:17] + "..."
                if self.events_dict[date][i][1] != self.CAL_ID:
                    text_colour = self.ext_event_colour
                else:
                    text_colour = self.my_event_colour
                self.d.text((math.floor(self.BOX_WIDTH*day_of_week) + 5, self.TOP_PADDING + self.BOX_PADDING + (week*self.BOX_HEIGHT) + (i*self.EVENT_HEIGHT)), self.events_dict[date][i][0], font=self.small_font, fill=text_colour)


    
    def save_image(self):
        self.img.save('calendar_image.png')


if __name__ == "__main__":
    cal_img = CalendarImage()
    # month view
    WEEKS = 5
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
