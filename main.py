import subprocess

# Path to your local HTML file
html_file_path = '/home/calendar/inky-calendar/index.html'

# Path to save the screenshot
screenshot_path = '/home/calendar/inky-calendar/calendar.png'

# Command to render HTML to an image
command = f'wkhtmltoimage --quality 100 --javascript-delay 100000 {html_file_path} {screenshot_path}'

# Execute the command
subprocess.run(command, shell=True)
