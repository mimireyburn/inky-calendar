import subprocess
from inky.auto import auto

# Path to your local HTML file
html_file_path = '/home/calendar/inky-calendar/index.html'

# Path to save the screenshot
screenshot_path = '/home/calendar/inky-calendar/calendar.png'

# Command to render HTML to an image
command = f'wkhtmltoimage --quality 100 --javascript-delay 100000 {html_file_path} {screenshot_path}'

# Execute the command
subprocess.run(command, shell=True)


print("Displaying calendar")
saturation = 1.0

# display calendar_image.png on the screen
inky_display = auto(ask_user=True, verbose=True)
# inky_display.set_border(inky_display.WHITE)s
image = Image.open("calendar.png")
inky_display.set_image(image, saturation=saturation)
inky_display.set_border(inky_display.WHITE)
inky_display.show()
