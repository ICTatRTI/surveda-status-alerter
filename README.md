# Survey Status Alerter

This is a script that gets the status of a [Surveda](https://github.com/instedd/ask) and sends out an email summary.

###  Usage
1. Configure your environment variables as .env (see .env.example)
2. Run `pip install -r requirements.txt` to install dependencies
3. Run the script `python monitor.py -project 25`

### Other Notes
* The email template is for you to copy and paste into the email service (we're using sparkpost here). With Sparkpost you'll need to specify the API key and template id in your environment variables.
* This has been designed to be run as a scheduled job somewhere (i.e. cron). Here is how to run this every day at 5am using cron
`0 5 * * * python /opt/surveda-status-alerter/monitor.py --project 25`
