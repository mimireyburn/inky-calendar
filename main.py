# Display image on 7 colour inky dev screen
from PIL import Image
from draw_calendar import CalendarImage
import time
import datetime
import threading

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
    cal_img.draw_last_updated()  # Draw the last updated timestamp
    cal_img.save_image()

    # Fingerprint of what's currently on screen, so callers can tell whether
    # a future fetch actually changed anything before refreshing the e-ink display.
    return hash(tuple(sorted((e.get("id"), e.get("updated")) for e in events)))


def display():
    print("Displaying calendar")
    
    if not INKY_AVAILABLE:
        print("Inky library not available. Calendar image saved as 'calendar_image.png'")
        return
    
    saturation = 1.0

    # display calendar_image.png on the screen
    try:
        inky_display = auto(ask_user=False, verbose=True)
        # inky_display.set_border(inky_display.WHITE)
        image = Image.open("calendar_image.png")
        inky_display.set_image(image, saturation=saturation)
        inky_display.set_border(inky_display.WHITE)
        inky_display.show()
    except SystemExit as e:
        # Pimoroni's gpiodevice library calls sys.exit() instead of raising
        # when a required pin (e.g. Chip Select) is already claimed elsewhere,
        # so this must be caught separately from Exception.
        print(f"Error displaying on Inky: pin conflict ({e})")
        print("Calendar image saved as 'calendar_image.png'")
    except Exception as e:
        print(f"Error displaying on Inky: {e}")
        print("Calendar image saved as 'calendar_image.png'")


CALENDAR_CHECK_INTERVAL_SECONDS = 5 * 60  # how often to check Google Calendar for changes


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

    # Shared state, read/written from both the main thread (periodic calendar
    # check) and the GPIO interrupt callbacks (button presses), so it's guarded
    # by a lock rather than relying on the two never overlapping.
    state_lock = threading.Lock()
    start_date = datetime.datetime.now()
    last_fingerprint = None
    last_rendered_date = None

    def refresh_calendar(new_start_date):
        global start_date, last_fingerprint, last_rendered_date
        with state_lock:
            start_date = new_start_date
            last_fingerprint = getMonth(start_date)
            display()
            last_rendered_date = datetime.datetime.now().date()

    def on_button_a(channel):
        print("Button A pressed showing calendar around today")
        refresh_calendar(datetime.datetime.now())

    def on_button_b(channel):
        print("Button B pressed showing calendar around 3 weeks from start_date")
        with state_lock:
            next_start_date = start_date + datetime.timedelta(weeks=3)
        refresh_calendar(next_start_date)

    def on_button_c(channel):
        print("Button C pressed")

    try:
        refresh_calendar(start_date)  # Default behavior - shows calendar around today

        if GPIO_AVAILABLE:
            # Interrupt-driven buttons: the Pi sleeps instead of busy-polling
            # the pins, and a press wakes the matching callback immediately.
            GPIO.add_event_detect(BUTTONS[0], GPIO.FALLING, callback=on_button_a, bouncetime=300)
            GPIO.add_event_detect(BUTTONS[1], GPIO.FALLING, callback=on_button_b, bouncetime=300)
            GPIO.add_event_detect(BUTTONS[2], GPIO.FALLING, callback=on_button_c, bouncetime=300)

            while True:
                try:
                    time.sleep(CALENDAR_CHECK_INTERVAL_SECONDS)
                    print("Checking Google Calendar for updates...")

                    with state_lock:
                        current_start_date = start_date
                        previous_fingerprint = last_fingerprint
                        previous_rendered_date = last_rendered_date

                    new_fingerprint = getMonth(current_start_date)
                    today_changed = datetime.datetime.now().date() != previous_rendered_date

                    if new_fingerprint != previous_fingerprint or today_changed:
                        print("Calendar changed, refreshing display...")
                        with state_lock:
                            display()
                            last_fingerprint = new_fingerprint
                            last_rendered_date = datetime.datetime.now().date()
                    else:
                        print("No changes detected.")
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
