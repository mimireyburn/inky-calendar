from PIL import Image, ImageDraw, ImageFont
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import datetime 
import calendar
import math
import json
import os 

class CalendarImage:
    def __init__(self, start_date=None):
        self.start_date = start_date
        self.load_credentials()
        self.initialize_variables()        

    def initialize_variables(self):
        self.width = 1600
        self.height = 1200
        self.weeks = 4
        self.top_padding = 55
        self.box_padding = 55
        self.calendar_height = self.height - self.top_padding - 1
        self.box_height = math.floor(self.calendar_height / self.weeks)-10
        self.box_width = math.floor(self.width / 7)
        self.event_height = 24
        self.font_size = 28
        self.small_font_size = self.event_height

        self.colors = {
            # Colour options are: "black", "white", "green", "blue", "red", "yellow"
            'outline': "black",
            'days': "black", # days of the week text
            'number': "black",
            'today_text': "white",
            'today_circle': "red",
            'background': "white",
        }
        
        # Available colors for different organizers
        self.organizer_colors = ["blue", "green", "purple", "orange", "pink", "brown", "gray", "cyan"]
        self.organizer_color_map = {}  # Maps organizer email to color

        # Calculate prev_monday based on start_date or default to current time
        if self.start_date:
            # If start_date is provided, use it as the reference point
            if isinstance(self.start_date, str):
                # Parse string date if needed
                reference_date = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
            else:
                reference_date = self.start_date
        else:
            # Default to current local time
            reference_date = datetime.datetime.now()
        
        # Calculate the Monday of the week containing the reference date
        # Then go back one week to get the "previous Monday"
        monday_of_week = reference_date - datetime.timedelta(days=reference_date.weekday())
        self.prev_monday = monday_of_week - datetime.timedelta(days=7)
        self.days_of_week = ["M", "T", "W", "T", "F", "S", "S"]
        self.events_dict = {}

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(script_dir, "AtkinsonHyperlegible-Regular.ttf")
        
        # Check if font file exists, fallback to default if not
        if os.path.exists(font_path):
            self.font = ImageFont.truetype(font_path, self.font_size)
            self.small_font = ImageFont.truetype(font_path, self.small_font_size)
        else:
            print(f"Warning: Font file not found at {font_path}. Using default font.")
            self.font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
        self.img = Image.new('RGB', (self.width, self.height), color='white')
        self.d = ImageDraw.Draw(self.img)


    def load_credentials(self):
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        key_file_path = os.path.join(script_dir, "KEY.json")
        
        if not os.path.exists(key_file_path):
            raise FileNotFoundError(f"KEY.json file not found at {key_file_path}")
        
        with open(key_file_path) as f:
            data = json.load(f)
        self.cal_id = data["calendar_id"]
        self.credentials = Credentials.from_service_account_file(key_file_path)
        self.service = build("calendar", "v3", credentials=self.credentials)


    def get_events(self, start_time, end_time):
        try:
            events_result = self.service.events().list(
                calendarId=self.cal_id, timeMin=start_time, timeMax=end_time, singleEvents=True, orderBy="startTime"
            ).execute()
            print(events_result)
            return events_result.get("items", [])
        except Exception as e:
            print(f"Error fetching events from Google Calendar: {e}")
            print("Continuing without events...")
            return []


    def populate_events_dict(self, events):
        for event in events:
            start_date, end_date, time, end, duration_days = self.extract_event_details(event)
            
            # Add event to all days it spans
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            for day_offset in range(duration_days):
                current_date = start_dt + datetime.timedelta(days=day_offset)
                current_date_str = current_date.strftime("%Y-%m-%d")
                
                # Determine if this is the start, middle, or end of a multi-day event
                if duration_days == 1:
                    event_type = "single"
                elif day_offset == 0:
                    event_type = "start"
                elif day_offset == duration_days - 1:
                    event_type = "end"
                else:
                    event_type = "middle"
                
                self.add_event_to_dict(current_date_str, [
                    event.get("summary", "No title"), 
                    event.get("creator", {}).get("email", "unknown"), 
                    time, 
                    end, 
                    event_type,
                    duration_days
                ])


    def extract_event_details(self, event):
        is_all_day = False
        try:
            start = event["start"]["dateTime"]
            end = event["end"]["dateTime"]
            start_date, time = start[:10], start
            end_date, end_time = end[:10], end
        except KeyError:
            # This is an all-day event
            start_date = event["start"]["date"]
            end_date = event["end"]["date"]
            time = "06:00"
            end_time = "06:30"
            is_all_day = True
        
        # Calculate duration in days for multi-day events
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        if is_all_day:
            # For all-day events, Google Calendar sets end date to the day after
            # So we don't add 1 to the duration calculation
            duration_days = (end_dt - start_dt).days
        else:
            # For timed events, we add 1 to include both start and end days
            duration_days = (end_dt - start_dt).days + 1
        
        return start_date, end_date, time, end_time, duration_days


    def add_event_to_dict(self, date, event_details):
        if date in self.events_dict:
            self.events_dict[date].append(event_details)
        else:
            self.events_dict[date] = [event_details]

    def get_organizer_color(self, organizer_email):
        """Assign a unique color to each organizer email address"""
        if organizer_email not in self.organizer_color_map:
            # Assign the next available color
            color_index = len(self.organizer_color_map) % len(self.organizer_colors)
            self.organizer_color_map[organizer_email] = self.organizer_colors[color_index]
            print(f"Assigned color '{self.organizer_colors[color_index]}' to organizer: {organizer_email}")
        return self.organizer_color_map[organizer_email]

    def print_color_mapping(self):
        """Print the organizer to color mapping for debugging"""
        print("\nOrganizer Color Mapping:")
        for email, color in self.organizer_color_map.items():
            print(f"  {email} -> {color}")
        print()

    def draw_color_key(self):
        """Draw a color key at the bottom of the calendar"""
        if not self.organizer_color_map:
            return  # No organizers to show
            
        # Calculate the bottom area for the key (start just below the calendar line)
        key_start_y = self.top_padding + (self.weeks * self.box_height) + 1
        key_height = 40  # Height for the key area
        key_padding = 10  # Padding from edges
        
        # Draw background for the key area
        self.d.rectangle([(0, key_start_y), (self.width, key_start_y + key_height)], 
                        fill=self.colors['background'])
        
        # Draw "Key:" label
        key_label = "Key:"
        self.d.text((key_padding, key_start_y + 5), key_label, font=self.small_font, fill=self.colors['number'])
        
        # Calculate positions for color squares and labels
        start_x = key_padding + 50  # Start after "Key:" label
        square_size = 20
        text_spacing = 25
        
        current_x = start_x
        
        for email, color in self.organizer_color_map.items():
            # Truncate email at the "@" symbol
            display_text = email.split('@')[0] if '@' in email else email
            
            # Draw color square
            square_y = key_start_y + 10
            self.d.rectangle([(current_x, square_y), (current_x + square_size, square_y + square_size)], 
                           fill=color, outline=self.colors['outline'], width=1)
            
            # Draw email label (truncated before @)
            label_y = key_start_y + 5
            self.d.text((current_x + square_size + 5, label_y), display_text, font=self.small_font, fill=self.colors['number'])
            
            # Move to next position
            current_x += square_size + text_spacing + len(display_text) * 14  # Approximate text width
            
            # If we're running out of space, wrap to next line
            if current_x > self.width - 50:
                current_x = start_x
                key_start_y += 25
                square_y = key_start_y + 10
                label_y = key_start_y + 15


    def draw_month(self):
            # Make background blue
            self.d.rectangle([(0, 0), (self.width, self.height)], fill=self.colors['background'])

            # Calculate the months being displayed in the calendar
            start_date = self.prev_monday.date()
            end_date = start_date + datetime.timedelta(days=(self.weeks * 7) - 1)
            
            # Get the months that are actually displayed
            start_month = start_date.month
            start_year = start_date.year
            end_month = end_date.month
            end_year = end_date.year
            
            # Create month display text
            if start_month == end_month and start_year == end_year:
                # Calendar is within a single month
                month_text = calendar.month_name[start_month][:3].upper() + " " + str(start_year)
            else:
                # Calendar spans multiple months
                if start_year == end_year:
                    # Same year, different months
                    month_text = calendar.month_name[start_month][:3].upper() + " - " + calendar.month_name[end_month][:3].upper() + " " + str(start_year)
                else:
                    # Different years
                    month_text = calendar.month_name[start_month][:3].upper() + " " + str(start_year) + " - " + calendar.month_name[end_month][:3].upper() + " " + str(end_year)

            # Draw capitalised month and year at top of calendar
            self.d.text((2,0), month_text, font=self.font, fill=self.colors['number'])

            # Draw calendar days_of_week at top of calendar
            for i in range(7):
                self.d.text((math.floor((self.width/7)*i) + math.floor(self.width/14), self.top_padding-(self.event_height*1.1)), self.days_of_week[i], font=self.small_font, fill=self.colors['days'])

            # Draw calendar days with labels from start_time to end_time
            for i in range(self.weeks):
                for j in range(7):
                    self.d.rectangle([(math.floor(self.box_width*j)+1, self.top_padding + (i*self.box_height)), (math.floor(self.box_width*(j+1))+1, self.top_padding + ((i+1)*self.box_height))], outline=self.colors['outline'], width=1)
                    
                    text_color = self.colors['number']

                    today = datetime.datetime.now().date()
                    box_date = self.prev_monday.date() + datetime.timedelta(days=(i*7) + j)
                    radius = 18
                    
                    # Only show red circle if start_date is None (default to today) or if start_date equals today
                    should_show_red_circle = False
                    if self.start_date is None:
                        # Default behavior - show red circle for today
                        should_show_red_circle = (box_date == today)
                    else:
                        # If start_date is provided, only show red circle if start_date equals today
                        if isinstance(self.start_date, str):
                            start_date_obj = datetime.datetime.strptime(self.start_date, "%Y-%m-%d").date()
                        else:
                            start_date_obj = self.start_date.date()
                        should_show_red_circle = (box_date == today and start_date_obj == today)
                    
                    if should_show_red_circle:
                        self.d.ellipse([
                            (math.floor(self.box_width*(j+1) - 30) - radius, self.top_padding + (i*self.box_height) + 20 - radius), 
                            (math.floor(self.box_width*(j+1) - 30) + radius + 8, self.top_padding + (i*self.box_height) + 26 + radius)], fill=self.colors['today_circle'])
                        text_color = self.colors['today_text']

                    # If day is in next month            
                    if self.prev_monday.day + (i*7) + j > calendar.monthrange(self.prev_monday.year, self.prev_monday.month)[1]:
                        self.d.text((math.floor(self.box_width*(j+1) - 35), self.top_padding + (i*self.box_height) + 5), str(self.prev_monday.day + (i*7) + j - calendar.monthrange(self.prev_monday.year, self.prev_monday.month)[1]), font=self.font, fill=text_color)
                    else:
                        self.d.text((math.floor(self.box_width*(j+1) - 35), self.top_padding + (i*self.box_height) + 5), str(self.prev_monday.day + (i*7) + j), font=self.font, fill=text_color)

            # Draw horizontal line at the bottom of the calendar grid
            calendar_bottom = self.top_padding + (self.weeks * self.box_height)
            self.d.rectangle([(0, calendar_bottom), (self.width, calendar_bottom + 1)], fill=self.colors['outline'])


    def draw_month_events(self):
        # Draw events on calendar
        for date in self.events_dict:
            # Get day of week of event
            day_of_week = datetime.datetime.strptime(date, "%Y-%m-%d").weekday()
            # Get week of event
            week = math.floor((datetime.datetime.strptime(date, "%Y-%m-%d") - self.prev_monday.replace(hour=0, minute=0, second=0, microsecond=0)).days / 7) 
            # Get number of events on day
            num_events = len(self.events_dict[date])
            
            # Track vertical position for this day to prevent overlapping
            current_y_offset = 0
            event_gap = 9  # Gap between events in pixels
            
            # Draw each event
            for i in range(num_events):
                event_data = self.events_dict[date][i]
                event_text = event_data[0]
                event_type = event_data[4] if len(event_data) > 4 else "single"
                organizer_email = event_data[1]
                
                # Get color based on organizer email
                rect_colour = self.get_organizer_color(organizer_email)
                
                # Text will be white on colored background
                text_colour = "white"
                
                # Add visual indicators for multi-day events
                if event_type == "start":
                    event_text = "|- " + event_text
                elif event_type == "end":
                    event_text = event_text + " -|"
                elif event_type == "middle":
                    event_text = "- " + event_text + " -"
                
                # Calculate available width for text (box width minus padding)
                available_width = self.box_width - 10  # 5px padding on each side
                
                # Get text bounding box to measure width
                bbox = self.d.textbbox((0, 0), event_text, font=self.small_font)
                text_width = bbox[2] - bbox[0]
                
                # Calculate current Y position based on accumulated offset
                y_pos = self.top_padding + self.box_padding + (week*self.box_height) + current_y_offset
                
                # Calculate rectangle dimensions
                rect_x = math.floor(self.box_width*day_of_week) + 3
                rect_width = self.box_width - 6
                
                # If text fits in one line, draw it normally
                if text_width <= available_width:
                    # Draw rectangle background
                    rect_height = self.event_height + 4  # Add padding
                    self.d.rectangle([(rect_x, y_pos - 2), (rect_x + rect_width, y_pos + rect_height)], fill=rect_colour)
                    
                    # Draw text
                    self.d.text((math.floor(self.box_width*day_of_week) + 5, y_pos), event_text, font=self.small_font, fill=text_colour)
                    
                    # Move to next line for next event (add gap)
                    current_y_offset += self.event_height + event_gap
                else:
                    # Text is too long, try to split into two lines
                    words = event_text.split()
                    line1 = ""
                    line2 = ""
                    
                    # Find the best split point by trying different combinations
                    best_split = 0
                    for i in range(1, len(words)):
                        test_line1 = " ".join(words[:i])
                        test_line2 = " ".join(words[i:])
                        
                        # Check if both lines fit
                        bbox1 = self.d.textbbox((0, 0), test_line1, font=self.small_font)
                        bbox2 = self.d.textbbox((0, 0), test_line2, font=self.small_font)
                        width1 = bbox1[2] - bbox1[0]
                        width2 = bbox2[2] - bbox2[0]
                        
                        if width1 <= available_width and width2 <= available_width:
                            best_split = i
                            line1 = test_line1
                            line2 = test_line2
                            break
                    
                    # If no perfect split found, use the best one we found
                    if best_split == 0:
                        # Fall back to original logic if no good split found
                        for word in words:
                            test_line1 = line1 + (" " if line1 else "") + word
                            bbox = self.d.textbbox((0, 0), test_line1, font=self.small_font)
                            test_width = bbox[2] - bbox[0]
                            
                            if test_width <= available_width:
                                line1 = test_line1
                            else:
                                # First line is full, start second line
                                if not line2:
                                    line2 = word
                                else:
                                    line2 += " " + word
                    
                    # Check if second line is too long
                    if line2:
                        bbox = self.d.textbbox((0, 0), line2, font=self.small_font)
                        line2_width = bbox[2] - bbox[0]
                        
                        if line2_width > available_width:
                            # Second line is too long, truncate it
                            while line2 and line2_width > available_width:
                                line2 = line2[:-1]
                                bbox = self.d.textbbox((0, 0), line2 + "..", font=self.small_font)
                                line2_width = bbox[2] - bbox[0]
                            line2 += ".."
                    
                    # Draw rectangle background for two-line event
                    rect_height = (self.event_height * 2) + 4  # Two lines plus padding
                    self.d.rectangle([(rect_x, y_pos - 2), (rect_x + rect_width, y_pos + rect_height)], fill=rect_colour)
                    
                    # Draw both lines
                    self.d.text((math.floor(self.box_width*day_of_week) + 5, y_pos), line1, font=self.small_font, fill=text_colour)
                    if line2:
                        self.d.text((math.floor(self.box_width*day_of_week) + 5, y_pos + self.event_height), line2, font=self.small_font, fill=text_colour)
                    
                    # Move to next position for next event (2 lines + gap)
                    current_y_offset += (self.event_height * 2) + event_gap

    
    def save_image(self):
        self.img.save('calendar_image.png')
