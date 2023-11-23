import subprocess
from inky.auto import auto
from PIL import Image

# Path to your local HTML file
html_file_path = '/home/calendar/inky-calendar/index.html'

# Path to save the screenshot
screenshot_path = '/home/calendar/inky-calendar/calendar.png'

# Command to render HTML to an image
command = f'wkhtmltoimage --quality 100 --javascript-delay 100000 --width 800 --height 480 {html_file_path} {screenshot_path}'

# Execute the command
subprocess.run(command, shell=True)


print("Displaying calendar")

# display calendar.png on the screen
inky_display = auto(ask_user=True, verbose=True)

# Adjust saturation
saturation = 1.5  # Adjust this value as needed

# Load image
image = Image.open("calendar.png")

# Enhance color
enhancer = ImageEnhance.Color(image)
image = enhancer.enhance(saturation)

# Resize image to fit screen
image = image.resize((inky_display.WIDTH, inky_display.HEIGHT))

# Display image
inky_display.set_image(image)
inky_display.set_border(inky_display.WHITE)
inky_display.show()
