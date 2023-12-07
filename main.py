from inky.auto import auto
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageEnhance
import RPi.GPIO as GPIO
import time

class InkyCalendar:
    def __init__(self, html_file_path, screenshot_path, saturation=6.5):
        self.html_file_path = html_file_path
        self.screenshot_path = screenshot_path
        self.saturation = saturation
        self.inky_display = auto(ask_user=True, verbose=True)

    def render_html_to_image(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=800,510")
        chrome_options.add_argument("--disable-gpu")

        browser_driver = Service('/usr/lib/chromium-browser/chromedriver')
        
        with webdriver.Chrome(service=browser_driver, options=chrome_options) as browser:
            browser.get("file://" + self.html_file_path)
            # Wait for JavaScript rendering
            time.sleep(5)
            browser.save_screenshot(self.screenshot_path)

    def display_calendar(self):
        # Load image
        image = Image.open(self.screenshot_path)

        # Enhance color
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(self.saturation)
        
        # Crop image to fit screen
        buffer = 10
        image = image.crop((buffer, buffer, self.inky_display.WIDTH + buffer, self.inky_display.HEIGHT+ buffer))

        # Save image for debugging
        image.save(self.screenshot_path)

        # Display image
        self.inky_display.set_image(image)
        self.inky_display.show()


if __name__ == "__main__":
    # set up GPIO buttons
    BUTTONS = [5, 6, 16, 24]
    LABELS = ["A", "B", "C", "D"]
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print("Waiting for button press...")

    # Poll GPIO buttons
    while True:
        # if BUTTON A is pressed, display calendar
        if GPIO.input(BUTTONS[0]) == GPIO.LOW:
            calendar = InkyCalendar('/home/calendar/inky-calendar/calendar.html', '/home/calendar/inky-calendar/calendar.png')
            calendar.render_html_to_image()
            print("Displaying month")
            calendar.display_calendar()
        
        if GPIO.input(BUTTONS[1]) == GPIO.LOW:
            calendar = InkyCalendar('/home/calendar/inky-calendar/week.html', '/home/calendar/inky-calendar/calendar.png')
            calendar.render_html_to_image()
            print("Displaying week")
            calendar.display_calendar()