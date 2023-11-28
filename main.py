import subprocess
from inky.auto import auto
from PIL import Image, ImageEnhance
import RPi.GPIO as GPIO 

class InkyCalendar:
    def __init__(self, html_file_path, screenshot_path, saturation=4):
        self.html_file_path = html_file_path
        self.screenshot_path = screenshot_path
        self.saturation = saturation
        self.inky_display = auto(ask_user=True, verbose=True)

    def render_html_to_image(self):
        command = f'wkhtmltoimage --quality 100 --javascript-delay 25000 --width 800 --height 530 {self.html_file_path} {self.screenshot_path}'
        subprocess.run(command, shell=True)

    def display_calendar(self):
        # Load image
        image = Image.open(self.screenshot_path)

        # Enhance color
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(self.saturation)

        # Crop image to fit screen
        buffer = 11
        image = image.crop((buffer, buffer, self.inky_display.WIDTH + buffer, self.inky_display.HEIGHT + buffer))

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
            calendar = InkyCalendar('/home/calendar/inky-calendar/month.html', '/home/calendar/inky-calendar/calendar.png')
            calendar.render_html_to_image()
            print("Displaying month")
            calendar.display_calendar()
        
        if GPIO.input(BUTTONS[1]) == GPIO.LOW:
            calendar = InkyCalendar('/home/calendar/inky-calendar/week.html', '/home/calendar/inky-calendar/calendar.png')
            calendar.render_html_to_image()
            print("Displaying week")
            calendar.display_calendar()