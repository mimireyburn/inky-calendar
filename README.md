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

### Running automatically with cron 
Edit the `startup.sh` file to include the path to the correct path to `main.py` file. 

1. Open crontab with `crontab -e`
2. Add ``` @reboot bash /path/to/startup.sh``` to the end. Save and exit. 
3. chmod +x path/to/startup.sh

This will run the script on boot. You can also add a line to run the script at specific times of day.

## To-Do
- [ ] Add support for week view
- [ ] Add support for multi-day events
- [ ] Refactor code to plot day-by-day instead of from prev_monday

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
