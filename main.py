import webbrowser
import pyautogui
import time

# Path to your local HTML file
html_file_path = '/home/calendar/inky-calendar/index.html'

# Open the HTML file in the default web browser
webbrowser.open('file://' + html_file_path)

# Wait for the browser to load the page
time.sleep(5)  # Adjust the delay as needed

# Take a screenshot
screenshot = pyautogui.screenshot()

# Save the screenshot
screenshot.save('/path/to/save/screenshot.png')
