# Inky Calendar
*An e-ink display for Google Calendar*

![Drawing of Calendar x Website](https://github.com/mimireyburn/inky-calendar/assets/79009541/5161818a-04b5-40b5-a4ee-51c97a323698)

## About

Paper calendars are great: they're nice to look at and easy to read, but as the days of the month go on, they get less and less useful. Google Calendar is good too - it automatically adds events from emails, you can integrate your friends' calendars into your own and it's always up to date. But keeping both of these up to date is a pain, and I don't want to have to look at my phone or computer to see what I have upcoming. 

This project aims to combine the best of both worlds: a calendar that's always up to date, but more of a pleasure to look at than a screen.

## Setup

### Running automatically with cron 
1. Open crontab with `crontab -e`
2. Add @reboot /path/to/startup.sh. Save and exit.
3. chmod +x path/to/startup.shs

## To-Do
- [ ] Add support for week view
- [ ] Add support for multi-day events

## FAQ

#### Why use Pillow?
I could use pre-exisiting calendar libraries but I want to be able to customise the calendar to my liking. This is particularly important for 4-week view, instead of the standard month view and ensuring the formatting is appropriate for the e-ink display.

#### Why use Google Calendar?
I use Google Calendar for my personal calendar, and it's easy to integrate with other calendars. I'm also familiar with the API.

#### Why use an e-ink display?
E-ink displays are like original Kindle displays - they have a paper-like 'quality'. They also don't require power to maintain an image. This means that the calendar can be updated once a day, and then turned off or even unplugged and moved around the home.

#### Why use an Inky over a Waveshare?
IMO Inkys have better documentation, support and easier set-up for R-Pi. I tried to use a Waveshare but massively preferred Inky. Inky also has a 7-colour display, which is fun.

## Contributing 
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
