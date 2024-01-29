# Display image on 7 colour inky dev screen
import sys
from PIL import Image
# from inky.auto import auto
from draw_calendar import CalendarImage
import time
import signal 
# import RPi.GPIO as GPIO 
import datetime

def getMonth(): 
    print("Getting month...")
    cal_img = CalendarImage()

    start_time = cal_img.prev_monday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_time = (cal_img.prev_monday + datetime.timedelta(days=(cal_img.weeks * 7) - 1)).replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z"
    
    events = cal_img.get_events(start_time, end_time)
    cal_img.populate_events_dict(events)
    cal_img.draw_month()
    cal_img.draw_month_events()
    cal_img.save_image()


def getWeek(): 
    print("Getting week...")
    cal_img = CalendarImage()

    start_time = (datetime.datetime.utcnow() - datetime.timedelta(days=datetime.datetime.utcnow().weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_time = (datetime.datetime.utcnow() + datetime.timedelta(days=6-datetime.datetime.utcnow().weekday())).replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z" 
    
    events = cal_img.get_events(start_time, end_time)
    cal_img.populate_events_dict(events)

    cal_img.draw_week()
    cal_img.draw_week_events()
    cal_img.save_image()


def display():
    print("Displaying calendar")
    saturation = 1.0

    # display calendar_image.png on the screen
    inky_display = auto(ask_user=True, verbose=True)
    # inky_display.set_border(inky_display.WHITE)
    image = Image.open("calendar_image.png")
    inky_display.set_image(image, saturation=saturation)
    inky_display.set_border(inky_display.WHITE)
    inky_display.show()


if __name__ == "__main__":
    # set up GPIO buttons
    BUTTONS = [5, 6, 16, 24]
    LABELS = ["A", "B", "C", "D"]
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Poll GPIO buttons
    while True:
        # if BUTTON A is pressed, display calendar
        if GPIO.input(BUTTONS[0]) == GPIO.LOW:
            print("Button A pressed")
            getMonth()
            display()
        
        if GPIO.input(BUTTONS[1]) == GPIO.LOW:
            print("Button B pressed")
            getWeek()
            display()

    # Test on mac 
    # print("Running on mac")
    # getMonth()