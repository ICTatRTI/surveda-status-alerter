import requests
from bs4 import BeautifulSoup
import argparse
import sys
import os
import pandas as pd
import io
from sparkpost import SparkPost
from os.path import join, dirname
from dotenv import load_dotenv

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='run.log',
                    filemode='w')

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--project", type=int, help="this is the project id")
parser.add_argument("-s", "--survey", type=int, help="this is the survey id")
args = parser.parse_args()

if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)


SURVEDA_URL = os.environ.get("SURVEDA_URL")
EMAIL_LIST = str(os.environ.get("SURVEDA_EMAIL_LIST")).split()
SURVEDA_PROJECT = str(args.project)
SURVEDA_SURVEY = str(args.survey)

# Get the login token
logging.debug('Starting...')
page = requests.get(SURVEDA_URL+'/sessions/new')
soup = BeautifulSoup(page.content, 'html.parser')
csrf_token = soup.find("input", {"name":"_csrf_token"})['value'] # soup.find("a", id="link3")
ask_key = page.cookies['_ask_key']


#########################
# Authentication
#########################


# Prepare post data
data = {}
data["_csrf_token"]=csrf_token
data["session[email]"]=os.environ.get("SURVEDA_USER")
data["session[password]"]=os.environ.get("SURVEDA_PASS")

# login
logging.debug('Login as '+ os.environ.get("SURVEDA_USER"))
s = requests.session()
headers = {'Cookie': '_ask_key='+ask_key}
response = s.post(SURVEDA_URL+'/sessions', data=data, headers=headers)

# Get authenticated ask key and coherence_login (this ask token is different)
ask_key = s.cookies['_ask_key']
coherence_login = s.cookies['coherence_login']
headers = {'Cookie': '_ask_key='+ask_key}
s.headers.update(headers)


#########################
# Get Data
#########################


# Get Survey Name
logging.debug( 'Getting Survey '+ SURVEDA_SURVEY)
survey = s.get(SURVEDA_URL+'/api/v1/projects/'+SURVEDA_PROJECT+'/surveys/'+SURVEDA_SURVEY)
survey_name = survey.json()['data']['name']

# Get Interactions
logging.debug('Getting Interactions File ')
r = s.get(SURVEDA_URL+'/api/v1/projects/'+SURVEDA_PROJECT+'/surveys/'+SURVEDA_SURVEY+'/respondents/interactions?_format=csv')
interactions=pd.read_csv(io.StringIO(r.content.decode('utf-8')))

# Prepare data for notification
logging.debug('Transformign results ')
interactions['Timestamp'] = pd.to_datetime(interactions['Timestamp']);
interactions = interactions.set_index('Timestamp')
timegrouped = interactions.groupby([pd.TimeGrouper('1D'), 'Channel'])
dataframe = timegrouped['Respondent ID'].count().to_frame()
dataframe = dataframe.reset_index()

channel_data = []
for index, row in dataframe.iterrows():
    channel = {}
    channel['date'] = row["Timestamp"].strftime("%Y-%m-%d")
    channel['name'] = row["Channel"]
    channel['count'] = row["Respondent ID"]
    channel_data.append(channel)



#########################
# Send Email notification
#########################
logging.debug('Sending Email Notification ')
sp = SparkPost(os.environ.get("SPARKPOST_KEY"))
template = sp.templates.get(os.environ.get("SPARKPOST_TEMPLATE_ID"))


# Send email
sp.transmissions.send(
    recipients=EMAIL_LIST,
    html=template['content']['html'],
    from_email='NCD Survey Alerts <ncd-alerts@ictedge.org>',
    subject='Daily update for '+survey_name,
    substitution_data={
        'survey_name': survey_name,
        'channels': channel_data
    }
)

#########################
# Logoff
#########################

s.delete(SURVEDA_URL+'/api/v1/sessions')