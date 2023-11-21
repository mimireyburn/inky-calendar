from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import time
from inky import InkyPHAT

# Selenium Configuration
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=800x600')  # Adjust to your e-ink display size

# Here, you can directly use ChromeDriverManager without specifying ChromeType
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Replace this with the path to your chromedriver and the path to your local HTML file
chromedriver_path = '/usr/bin/chromedriver'
html_file_path = '/home/pi/inky-calendar/index.html'

driver.get(html_file_path)
time.sleep(2)  # Wait for the page to load

# Screenshot and Save as PNG
screenshot_path = '/home/pi/inky-calendar/cal.png'
driver.save_screenshot(screenshot_path)
driver.quit()

# Open Image and Convert for E-ink Display
image = Image.open(screenshot_path)
# Convert to grayscale and resize if necessary
image = image.convert('L')
# Resize or other image processing here

# Display on E-ink
# Initialize your e-ink display and display the image
print("Displaying calendar")
saturation = 1.0

# display calendar_image.png on the screen
inky_display = auto(ask_user=True, verbose=True)
# inky_display.set_border(inky_display.WHITE)s
image = Image.open("cal.png")
inky_display.set_image(image, saturation=saturation)
inky_display.set_border(inky_display.WHITE)
inky_display.show()

# Make sure to handle exceptions and errors as needed
