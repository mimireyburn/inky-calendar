# Inky Calendar
*An e-ink display for Google Calendar*

![Drawing of Calendar x Website](https://github.com/mimireyburn/inky-calendar/assets/79009541/5161818a-04b5-40b5-a4ee-51c97a323698)

## About

Paper calendars are great: they're nice to look at and easy to read, but as the days of the month go on, they get less and less useful. Google Calendar is good too - it automatically adds events from emails, you can integrate your friends' calendars into your own and it's always up to date. But keeping both of these up to date is a pain, and I don't want to have to look at my phone or computer to see what I have upcoming. 

This project aims to combine the best of both worlds: a calendar that's always up to date, but more of a pleasure to look at than a screen.

![eInk Calendar](https://github.com/mimireyburn/inky-calendar/assets/79009541/458e3851-9ae8-4452-9013-441e98c1f31d)

## Setup

### Setting up a service account for Google Calendar
1. Go to the Google Cloud Console
2. Create a new project
3. Go to the APIs & Services > Credentials
4. Create a new service account (+ Create Credientials -> Service account) 
5. Add new KEY in JSON format (It will download automatically)
5. Save it as `KEY.json` in the root directory of this project
6. Add a key-value pair to KEY.json, as follows:
   ```"calendar_id": "<your-google-email-address>"```

### Add service account to your calendar
1. Go to your Google Calendar
2. Got to '...' on the chosen Calendar (usually in sidebar) then Settings and Sharing
3. Scroll down to 'Share with specific people or groups' and click 'Add people and groups'
4. Add the service account email (something@somethingelse.gserviceaccount.com) as a new person with 'See all event details' permissions

### Create a virtual environment and install dependencies
1. Create a virtual environment with `python -m venv .venv`
2. Activate the virtual environment with `source .venv/bin/activate`
3. Install dependencies with `pip install -r requirements.txt`

### Run the script
1. Run `python main.py`

### Running automatically with systemd 
This is a simple script that runs the `main.py` file on the Raspberry Pi. You can edit it to run at specific times of day and on boot. 

> **Removing cronjobs:**  
> Previously, I used cron to run the script, but systemd is more robust and easier to manage. The `startup.sh` script remains in the repo for reference, but it's not needed when using systemd. If you were using cronjobs before, you can remove them by running `crontab -e` and deleting the relevant lines at the end of the file.

1. Create a new systemd service file with `sudo nano /etc/systemd/system/inky-calendar.service`
2. Add the following content:

```
[Unit]
Description=Inky Calendar (Google Calendar to Inky display)
# Wait until the network is actually up (for Google Calendar calls)
Wants=network-online.target
After=network-online.target
After=systemd-networkd-wait-online.service  # Ensures actual network connectivity

[Service]
Type=simple
User=pi # Change to your username
Group=pi # Change to your group (usually same as username)
# Run inside your project folder so relative paths (e.g. KEY.json) work
WorkingDirectory=/home/pi/inky-calendar # Change to your project folder, remember this will change if you change the username

# Use the Python from your venv directly (no need to "activate")
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/pi/inky-calendar/.venv/bin/python /home/pi/inky-calendar/main.py

# Auto-restart on crashes; space out retries
Restart=on-failure
RestartSec=10

# Send logs to the journal
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

3. Save and exit.
4. Reload systemd with `sudo systemctl daemon-reload`
5. Restart the service with `sudo systemctl restart inky-calendar.service`
6. Check the status of the service with `sudo systemctl status inky-calendar.service`
7. Check the logs of the service with `journalctl -u inky-calendar.service -e`


## FAQ

#### Why use Pillow?
I could use pre-exisiting calendar libraries but I want to be able to customise the calendar to my liking. This is particularly important for 4-week view, instead of the standard month view and ensuring the formatting is appropriate for the e-ink display. 

It also means I can use Python instead of Javascript. This makes prototyping across OSs a lot easier and, since I don't need dynamic web rendering (selenium), it makes the code simpler, faster and more robust.


#### Why use Google Calendar?
I use Google Calendar for my personal calendar, and it's easy to integrate with other calendars. I'm also familiar with the API.

#### Why use an e-ink display?
E-ink displays are like original Kindle displays - they have a paper-like 'quality'. They also don't require power to maintain an image. This means that the calendar can be updated once a day, and then turned off or even unplugged and moved around the home.

#### Why use an Inky over a Waveshare?
Inkys have better documentation, support and easier set-up for R-Pi imo. I tried to use a Waveshare but massively preferred Inky. Inky also has a 7-colour display, which is fun.

## Contributing 
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
