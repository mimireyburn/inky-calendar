from PIL import Image, ImageDraw, ImageFont
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from pilmoji import Pilmoji
from pilmoji.source import TwitterEmojiSource
import emoji as emoji_lib
import datetime
import calendar
import math
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class CalendarImage:
    def __init__(self, start_date=None):
        self.start_date = start_date
        self.load_credentials()
        self.initialize_variables()        

    def initialize_variables(self):
        # ===== CALENDAR DIMENSIONS =====
        self.width = 1600
        self.height = 1200
        self.weeks = 4
        
        # ===== PADDING AND SPACING =====
        self.top_padding = 55
        self.box_padding = 55
        self.calendar_height = self.height - self.top_padding - 1
        self.box_height = math.floor(self.calendar_height / self.weeks) - 10
        self.box_width = math.floor(self.width / 7)
        
        # ===== EVENT SETTINGS =====
        self.event_height = 24
        self.event_gap = 9  # Gap between events in pixels
        self.event_padding = 5  # Padding inside event boxes
        self.event_rect_padding = 2  # Padding around event rectangles
        
        # ===== FONT SETTINGS =====
        self.font_size = 28
        self.small_font_size = self.event_height
        
        # ===== TODAY CIRCLE SETTINGS =====
        self.today_circle_radius = 24
        self.today_circle_offset_y = 2.5  # Vertical offset adjustment for circle positioning
        
        # ===== DAY NUMBER POSITIONING =====
        self.day_number_x_offset = 35  # Distance from right edge of box
        self.day_number_y_offset = 5   # Distance from top of box
        
        # ===== DAYS OF WEEK POSITIONING =====
        self.days_of_week_y_offset = 1.1  # Multiplier for event_height
        
        # ===== COLOR KEY SETTINGS =====
        self.color_key_height = 40
        self.color_key_padding = 10
        self.color_key_square_size = 20
        self.color_key_text_spacing = 25
        self.color_key_wrap_margin = 50
        
        # ===== CALENDAR COLORS =====
        self.colors = {
            # Colour options are: "black", "white", "green", "blue", "red", "yellow"
            'outline': "black",
            'days': "black", # days of the week text
            'number': "black",
            'today_text': "white",
            'today_circle': "red",
            'background': "white",
        }
        
        # ===== ORGANIZER COLORS =====
        # Available colors for different organizers
        self.organizer_colors = ["blue", "green", "brown", "yellow", "gray", "olive"]
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

        # ===== EMOJI SUPPORT (Twemoji via pilmoji) =====
        self.emoji_source = TwitterEmojiSource()
        self._emoji_support_cache = {}

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
        
        with open(key_file_path) as credentials_file:
            credentials_data = json.load(credentials_file)
        self.cal_id = credentials_data["calendar_id"]
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


    def filter_unsupported_emoji(self, text):
        for match in emoji_lib.emoji_list(text):
            char = match["emoji"]
            if char not in self._emoji_support_cache:
                try:
                    self._emoji_support_cache[char] = self.emoji_source.get_emoji(char) is not None
                except Exception:
                    self._emoji_support_cache[char] = False
            if not self._emoji_support_cache[char]:
                text = text.replace(char, "")
        return text.strip()


    def populate_events_dict(self, events):
        for event in events:
            start_date, end_date, start_time, end_time, duration_days = self.extract_event_details(event)
            
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
                    self.filter_unsupported_emoji(event.get("summary", "No title")),
                    event.get("creator", {}).get("email", "unknown"), 
                    start_time, 
                    end_time, 
                    event_type,
                    duration_days
                ])


    def extract_event_details(self, event):
        is_all_day = False
        try:
            event_start_datetime = event["start"]["dateTime"]
            event_end_datetime = event["end"]["dateTime"]
            start_date, start_time = event_start_datetime[:10], event_start_datetime
            end_date, end_time = event_end_datetime[:10], event_end_datetime
        except KeyError:
            # This is an all-day event
            start_date = event["start"]["date"]
            end_date = event["end"]["date"]
            start_time = "06:00"
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
        
        return start_date, end_date, start_time, end_time, duration_days


    def add_event_to_dict(self, date, event_details):
        if date in self.events_dict:
            self.events_dict[date].append(event_details)
        else:
            self.events_dict[date] = [event_details]

    def get_text_color_for_background(self, background_color):
        """Return black text for light backgrounds, white text otherwise"""
        light_colors = {"orange", "yellow", "gold", "khaki", "tan", "wheat", "pink", "lightgray", "lightgrey"}
        return "black" if background_color in light_colors else "white"

    def get_text_stroke_for_color(self, text_color):
        """Black text needs a stroke to match the visual weight of white text"""
        return (1, "black") if text_color == "black" else (0, None)

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
        
        # Draw background for the key area
        self.d.rectangle([(0, key_start_y), (self.width, key_start_y + self.color_key_height)], 
                        fill=self.colors['background'])
        
        # Draw "Key:" label
        key_label = "Key:"
        self.d.text((self.color_key_padding, key_start_y + 5), key_label, font=self.small_font, fill=self.colors['number'])
        
        # Calculate positions for color squares and labels
        start_x = self.color_key_padding + 50  # Start after "Key:" label
        
        current_x = start_x
        
        for email, color in self.organizer_color_map.items():
            # Truncate email at the "@" symbol
            display_text = email.split('@')[0] if '@' in email else email
            
            # Draw color square
            square_y = key_start_y + 10
            self.d.rectangle([(current_x, square_y), (current_x + self.color_key_square_size, square_y + self.color_key_square_size)], 
                           fill=color, outline=self.colors['outline'], width=1)
            
            # Draw email label (truncated before @)
            label_y = key_start_y + 5
            self.d.text((current_x + self.color_key_square_size + 5, label_y), display_text, font=self.small_font, fill=self.colors['number'])
            
            # Move to next position
            current_x += self.color_key_square_size + self.color_key_text_spacing + len(display_text) * 14  # Approximate text width
            
            # If we're running out of space, wrap to next line
            if current_x > self.width - self.color_key_wrap_margin:
                current_x = start_x
                key_start_y += 25
                square_y = key_start_y + 10
                label_y = key_start_y + 15


    def draw_last_updated(self):
        """Draw a 'last updated' timestamp inline with the color key, bottom right"""
        timestamp_text = "Updated " + datetime.datetime.now().strftime("%a %d %b, %H:%M")

        text_bbox = self.d.textbbox((0, 0), timestamp_text, font=self.small_font)
        text_width = text_bbox[2] - text_bbox[0]

        key_start_y = self.top_padding + (self.weeks * self.box_height) + 1
        label_y = key_start_y + 5  # Same baseline as the "Key:" label text

        x = self.width - text_width - self.color_key_padding

        self.d.text((x, label_y), timestamp_text, font=self.small_font, fill=self.colors['number'])


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
            for day_index in range(7):
                self.d.text((math.floor((self.width/7)*day_index) + math.floor(self.width/14), self.top_padding-(self.event_height*self.days_of_week_y_offset)), self.days_of_week[day_index], font=self.small_font, fill=self.colors['days'])

            # Draw all grid cell outlines first, so day numbers/circles can be drawn on top of every line
            for week_index in range(self.weeks):
                for day_index in range(7):
                    self.d.rectangle([(math.floor(self.box_width*day_index)+1, self.top_padding + (week_index*self.box_height)), (math.floor(self.box_width*(day_index+1))+1, self.top_padding + ((week_index+1)*self.box_height))], outline=self.colors['outline'], width=1)

            # Draw calendar days with labels from start_time to end_time
            for week_index in range(self.weeks):
                for day_index in range(7):
                    text_color = self.colors['number']

                    today = datetime.datetime.now().date()
                    box_date = self.prev_monday.date() + datetime.timedelta(days=(week_index*7) + day_index)
                    
                    should_show_red_circle = (box_date == today)
                    
                    # Calculate day number text
                    if self.prev_monday.day + (week_index*7) + day_index > calendar.monthrange(self.prev_monday.year, self.prev_monday.month)[1]:
                        day_text = str(self.prev_monday.day + (week_index*7) + day_index - calendar.monthrange(self.prev_monday.year, self.prev_monday.month)[1])
                    else:
                        day_text = str(self.prev_monday.day + (week_index*7) + day_index)
                    
                    if should_show_red_circle:
                        # Calculate text bounding box first
                        text_bounding_box = self.d.textbbox((0, 0), day_text, font=self.font)
                        text_width = text_bounding_box[2] - text_bounding_box[0]
                        text_height = text_bounding_box[3] - text_bounding_box[1]
                        
                        # Position text at the normal location (same as non-today days)
                        text_x = math.floor(self.box_width*(day_index+1) - self.day_number_x_offset)
                        text_y = self.top_padding + (week_index*self.box_height) + self.day_number_y_offset
                        
                        # Calculate circle center based on text position
                        circle_center_x = text_x + (text_width // 2)
                        circle_center_y = text_y + (text_height // 2)
                        
                        # Draw the circle centered around the text
                        self.d.ellipse([
                            (circle_center_x - self.today_circle_radius, circle_center_y - self.today_circle_radius + self.today_circle_radius/self.today_circle_offset_y), 
                            (circle_center_x + self.today_circle_radius, circle_center_y + self.today_circle_radius + self.today_circle_radius/self.today_circle_offset_y)], fill=self.colors['today_circle'])
                        
                        text_color = self.colors['today_text']
                        self.d.text((text_x, text_y), day_text, font=self.font, fill=text_color)
                    else:
                        # Draw text normally for non-today days
                        self.d.text((math.floor(self.box_width*(day_index+1) - self.day_number_x_offset), self.top_padding + (week_index*self.box_height) + self.day_number_y_offset), day_text, font=self.font, fill=text_color)

            # Draw horizontal line at the bottom of the calendar grid, aligned with the grid cell edges
            calendar_bottom = self.top_padding + (self.weeks * self.box_height)
            self.d.rectangle([(1, calendar_bottom), (self.box_width*7 + 1, calendar_bottom + 1)], fill=self.colors['outline'])


    def draw_month_events(self):
        with Pilmoji(self.img, source=self.emoji_source) as pilmoji_draw:
            self._draw_month_events(pilmoji_draw)


    def _draw_month_events(self, pilmoji_draw):
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
            
            # Draw each event
            for event_index in range(num_events):
                event_data = self.events_dict[date][event_index]
                event_text = event_data[0]
                event_type = event_data[4] if len(event_data) > 4 else "single"
                organizer_email = event_data[1]
                
                # Get color based on organizer email
                rectangle_color = self.get_organizer_color(organizer_email)
                
                # Use black text on light backgrounds, white otherwise
                text_color = self.get_text_color_for_background(rectangle_color)
                stroke_width, stroke_fill = self.get_text_stroke_for_color(text_color)
                
                # Add visual indicators for multi-day events
                if event_type == "start":
                    event_text = "|- " + event_text
                elif event_type == "end":
                    event_text = event_text + " -|"
                elif event_type == "middle":
                    event_text = "- " + event_text + " -"
                
                # Calculate available width for text (box width minus padding)
                available_width = self.box_width - (self.event_padding * 2)
                
                # Get text width (emoji-aware)
                text_width, _ = pilmoji_draw.getsize(event_text, font=self.small_font)
                
                # Calculate current Y position based on accumulated offset
                y_pos = self.top_padding + self.box_padding + (week*self.box_height) + current_y_offset
                
                # Calculate rectangle dimensions
                rect_x = math.floor(self.box_width*day_of_week) + self.event_rect_padding
                rect_width = self.box_width - (self.event_rect_padding * 2)
                
                # If text fits in one line, draw it normally
                if text_width <= available_width:
                    # Draw rectangle background
                    rectangle_height = self.event_height + 4  # Add padding
                    self.d.rectangle([(rect_x, y_pos - 2), (rect_x + rect_width, y_pos + rectangle_height)], fill=rectangle_color)
                    
                    # Draw text
                    pilmoji_draw.text((math.floor(self.box_width*day_of_week) + self.event_padding, y_pos), event_text, font=self.small_font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_fill, emoji_position_offset=(0, -3))
                    
                    # Move to next line for next event (add gap)
                    current_y_offset += self.event_height + self.event_gap
                else:
                    # Text is too long, try to split into two lines
                    words = event_text.split()
                    first_line = ""
                    second_line = ""
                    
                    # Find the best split point by trying different combinations
                    best_split_index = 0
                    for word_index in range(1, len(words)):
                        test_first_line = " ".join(words[:word_index])
                        test_second_line = " ".join(words[word_index:])
                        
                        # Check if both lines fit
                        first_line_width, _ = pilmoji_draw.getsize(test_first_line, font=self.small_font)
                        second_line_width, _ = pilmoji_draw.getsize(test_second_line, font=self.small_font)
                        
                        if first_line_width <= available_width and second_line_width <= available_width:
                            best_split_index = word_index
                            first_line = test_first_line
                            second_line = test_second_line
                            break
                    
                    # If no perfect split found, use the best one we found
                    if best_split_index == 0:
                        # Fall back to original logic if no good split found
                        for word in words:
                            test_first_line = first_line + (" " if first_line else "") + word
                            test_width, _ = pilmoji_draw.getsize(test_first_line, font=self.small_font)
                            
                            if test_width <= available_width:
                                first_line = test_first_line
                            else:
                                # First line is full, start second line
                                if not second_line:
                                    second_line = word
                                else:
                                    second_line += " " + word
                    
                    # Check if second line is too long
                    if second_line:
                        second_line_width, _ = pilmoji_draw.getsize(second_line, font=self.small_font)

                        if second_line_width > available_width:
                            # Second line is too long, truncate it
                            while second_line and second_line_width > available_width:
                                second_line = second_line[:-1]
                                second_line_width, _ = pilmoji_draw.getsize(second_line + "..", font=self.small_font)
                            second_line += ".."
                    
                    # Draw rectangle background for two-line event
                    rectangle_height = (self.event_height * 2) + 4  # Two lines plus padding
                    self.d.rectangle([(rect_x, y_pos - 2), (rect_x + rect_width, y_pos + rectangle_height)], fill=rectangle_color)
                    
                    # Draw both lines
                    pilmoji_draw.text((math.floor(self.box_width*day_of_week) + self.event_padding, y_pos), first_line, font=self.small_font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_fill, emoji_position_offset=(0, -2))
                    if second_line:
                        pilmoji_draw.text((math.floor(self.box_width*day_of_week) + self.event_padding, y_pos + self.event_height), second_line, font=self.small_font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_fill, emoji_position_offset=(0, -2))
                    
                    # Move to next position for next event (2 lines + gap)
                    current_y_offset += (self.event_height * 2) + self.event_gap

    
    def save_image(self):
        self.img.save('calendar_image.png')
