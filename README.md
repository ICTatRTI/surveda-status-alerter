# Survey Status Alerter

This is a script that gets the status of a surveda and sends out an email summary.

###  Usage
1. Configure your environment varialbes as .env (see .env.example)
2. Run `pip install -r requirements.txt` to install dependencies
3. Run the script `python monitor.py -project 25 - survey 123`

The email template is for you to copy and paste into the email service (we're using sparkpost here). With Sparkpost you'll need to specify the API key and template id in your environment variables.
