# Display image on 7 colour inky dev screen
from PIL import Image
from draw_calendar import CalendarImage
import time
import datetime

# Conditional imports for Raspberry Pi specific modules
try:
    from inky.auto import auto
    INKY_AVAILABLE = True
except ImportError:
    INKY_AVAILABLE = False
    print("Warning: Inky library not available. Display functionality will be limited.")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. GPIO functionality will be limited.")

def getMonth(start_date=None): 
    print("Getting month...")
    cal_img = CalendarImage(start_date)

    start_time = cal_img.prev_monday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_time = (cal_img.prev_monday + datetime.timedelta(days=(cal_img.weeks * 7) - 1)).replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z"
    
    events = cal_img.get_events(start_time, end_time)
    cal_img.populate_events_dict(events)
    cal_img.print_color_mapping()  # Show which organizers got which colors
    cal_img.draw_month()
    cal_img.draw_month_events()
    cal_img.draw_color_key()  # Draw the color key at the bottom
    cal_img.save_image()


def display():
    print("Displaying calendar")
    
    if not INKY_AVAILABLE:
        print("Inky library not available. Calendar image saved as 'calendar_image.png'")
        return
    
    saturation = 1.0

    # display calendar_image.png on the screen
    try:
        inky_display = auto(ask_user=True, verbose=True)
        # inky_display.set_border(inky_display.WHITE)
        image = Image.open("calendar_image.png")
        inky_display.set_image(image, saturation=saturation)
        inky_display.set_border(inky_display.WHITE)
        inky_display.show()
    except Exception as e:
        print(f"Error displaying on Inky: {e}")
        print("Calendar image saved as 'calendar_image.png'")


if __name__ == "__main__":
    # set up GPIO buttons
    BUTTONS = [5, 6, 16, 24]
    LABELS = ["A", "B", "C", "D"]
    
    if GPIO_AVAILABLE:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            GPIO_AVAILABLE = False
    
    try:
        start_date = datetime.datetime.now()
        getMonth()  # Default behavior - shows calendar around today
        display()
        
        if GPIO_AVAILABLE:
            # Poll GPIO buttons
            while True:
                try:
                    if GPIO.input(BUTTONS[0]) == GPIO.LOW:
                        print("Button A pressed showing calendar around today")
                        getMonth()
                        display()
                        start_date = datetime.datetime.now()
                        time.sleep(0.1)  # prevent CPU overload
                    if GPIO.input(BUTTONS[1]) == GPIO.LOW:
                        print("Button B pressed showing calendar around 3 weeks from start_date")
                        start_date += datetime.timedelta(weeks=3)
                        getMonth(start_date)
                        display()   
                        time.sleep(0.1)  # prevent CPU overload
                    if GPIO.input(BUTTONS[2]) == GPIO.LOW:
                        print("Button C pressed")
                    time.sleep(0.1)  # prevent CPU overload
                except KeyboardInterrupt:
                    break
        else:
            print("GPIO not available. Running in single-shot mode.")
            print("Calendar image saved as 'calendar_image.png'")

    except Exception as error:
        print(f"Error: {error}")
        print("Exiting cleanly...")

    finally:
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except Exception:
                pass
    
    # Test on mac 
    # print("Running on mac")
    # getMonth()
    # getWeek()
