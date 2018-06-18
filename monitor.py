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
import json

import logging

def emailerror(survey_name):
    sp = SparkPost(os.environ.get("SPARKPOST_KEY"))
    template = sp.templates.get(os.environ.get("SPARKPOST_TEMPLATE_ERROR_ID"))

    message = "There was a problem downloading the interactions file "

    # Send email
    sp.transmissions.send(
        recipients=EMAIL_LIST,
        html=template['content']['html'],
        from_email='NCD Survey Alerts <ncd-alerts@ictedge.org>',
        subject='Daily update for ' + survey_name,
        campaign='Surveda Alerter',
        substitution_data={
            'survey_name': survey_name,
            'message': message
        }
    )

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='run.log',
                    filemode='w')

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--project", type=int, help="this is the project id")
args = parser.parse_args()

if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)


SURVEDA_URL = os.environ.get("SURVEDA_URL")
EMAIL_LIST = str(os.environ.get("SURVEDA_EMAIL_LIST")).split()
SURVEDA_PROJECT = str(args.project)

# Get the login token
logging.debug('Starting...')
page = requests.get(SURVEDA_URL+'/sessions/new')
soup = BeautifulSoup(page.content, 'html.parser')
csrf_token = soup.find("input", {"name":"_csrf_token"})['value'] # soup.find("a", id="link3")
ask_key = page.cookies['_ask_key']

# Get the mailing stuff ready to go
sp = SparkPost(os.environ.get("SPARKPOST_KEY"))
template = sp.templates.get(os.environ.get("SPARKPOST_TEMPLATE_ID"))


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

logging.debug( 'Getting All Running Surveys ')

# Get all runnign surveys
try:
    r = s.get(
        SURVEDA_URL + '/api/v1/projects/' + SURVEDA_PROJECT + '/surveys/')
    all_surveys = r.json()['data']

    for survey in all_surveys:

        if survey['state'] == 'running':
            logging.debug("I am a runnign survey")

            # Get Survey Name
            # logging.debug( 'Getting Survey '+ SURVEDA_SURVEY)
            # https://surveda-ph.org/api/v1/projects/1/surveys/262/respondents/stats
            survey_details = s.get(SURVEDA_URL+'/api/v1/projects/'+SURVEDA_PROJECT+'/surveys/'+str(survey['id'])+'/respondents/stats')


            survey_dispositions = survey_details.json()['data']['respondents_by_disposition']

            logging.debug('Loading up previous runs activity ')

            try:
                with open('previous-' + str(survey['id']) + '.json') as json_file:

                    previous_survey_dispositions = json.load(json_file)['data']['respondents_by_disposition']

                    completed_new = survey_dispositions['responsive']['detail']['completed']['count'] \
                                    - previous_survey_dispositions['responsive']['detail']['completed']['count']

                    contacted_new = survey_dispositions['contacted']['detail']['contacted']['count'] - \
                                    previous_survey_dispositions['contacted']['detail']['contacted']['count']

                    ineligible_new = survey_dispositions['responsive']['detail']['ineligible']['count'] - \
                                     previous_survey_dispositions['responsive']['detail']['ineligible']['count']

                    interim_partial_new = survey_dispositions['responsive']['detail']['partial']['count'] - \
                                          previous_survey_dispositions['responsive']['detail']['partial']['count']

                    queued_new = survey_dispositions['uncontacted']['detail']['queued']['count'] - \
                                 previous_survey_dispositions['uncontacted']['detail']['queued']['count']

                    refused_new = survey_dispositions['responsive']['detail']['refused']['count'] - \
                                  previous_survey_dispositions['responsive']['detail']['refused']['count']

                    registered_new = survey_dispositions['uncontacted']['detail']['registered']['count'] - \
                                     previous_survey_dispositions['uncontacted']['detail']['registered']['count']

                    started_new = survey_dispositions['responsive']['detail']['started']['count'] - \
                                  previous_survey_dispositions['responsive']['detail']['started']['count']

            except IOError as e:
                logging.debug("previous run snapshot not availble.")

                completed_new = "--"
                contacted_new = "--"
                ineligible_new = "--"
                interim_partial_new = "--"
                queued_new = "--"
                refused_new = "--"
                registered_new = "--"
                started_new = "--"


            total_count = survey_dispositions['responsive']['detail']['completed']['count'] \
                          + survey_dispositions['contacted']['detail']['contacted']['count'] \
                          + survey_dispositions['responsive']['detail']['ineligible']['count'] \
                          + survey_dispositions['responsive']['detail']['partial']['count'] \
                          + survey_dispositions['uncontacted']['detail']['queued']['count'] \
                          + survey_dispositions['responsive']['detail']['refused']['count'] \
                          + survey_dispositions['uncontacted']['detail']['registered']['count'] \
                          + survey_dispositions['responsive']['detail']['started']['count']

            total_pct = survey_dispositions['responsive']['detail']['completed']['percent'] \
                        + survey_dispositions['contacted']['detail']['contacted']['percent'] \
                        + survey_dispositions['responsive']['detail']['ineligible']['percent'] \
                        + survey_dispositions['responsive']['detail']['partial']['percent'] \
                        + survey_dispositions['uncontacted']['detail']['queued']['percent'] \
                        + survey_dispositions['responsive']['detail']['refused']['percent'] \
                        + survey_dispositions['uncontacted']['detail']['registered']['percent'] \
                        + survey_dispositions['responsive']['detail']['started']['percent']


            logging.debug('Sending Email Notification ')

            sp.transmissions.send(
                recipients=EMAIL_LIST,
                html=template['content']['html'],
                from_email='NCD Survey Alerts <ncd-alerts@ictedge.org>',
                subject='Daily Snapshot for '+ survey['name'],
                substitution_data={
                    'survey_name': survey['name'],
                    'completed': survey_dispositions['responsive']['detail']['completed']['count'],
                    'completed_pct': round(survey_dispositions['responsive']['detail']['completed']['percent'],2),
                    'completed_new': completed_new,
                    'contacted': survey_dispositions['contacted']['detail']['contacted']['count'],
                    'contacted_pct': round(survey_dispositions['contacted']['detail']['contacted']['percent'],2),
                    'contacted_new': contacted_new,
                    'ineligible': survey_dispositions['responsive']['detail']['ineligible']['count'],
                    'ineligible_pct': round(survey_dispositions['responsive']['detail']['ineligible']['percent'],2),
                    'ineligible_new': ineligible_new,
                    'interim_partial': survey_dispositions['responsive']['detail']['partial']['count'],
                    'interim_partial_pct': round(survey_dispositions['responsive']['detail']['partial']['percent'],2),
                    'interim_partial_new': interim_partial_new,
                    'queued': survey_dispositions['uncontacted']['detail']['queued']['count'],
                    'queued_pct': round(survey_dispositions['uncontacted']['detail']['queued']['percent'],2),
                    'queued_new': queued_new,
                    'refused': survey_dispositions['responsive']['detail']['refused']['count'],
                    'refused_pct': round(survey_dispositions['responsive']['detail']['refused']['percent'],2),
                    'refused_new': refused_new,
                    'registered': survey_dispositions['uncontacted']['detail']['registered']['count'],
                    'registered_pct': round(survey_dispositions['uncontacted']['detail']['registered']['percent'],2),
                    'registered_new': registered_new,
                    'started': survey_dispositions['responsive']['detail']['started']['count'],
                    'started_pct': round(survey_dispositions['responsive']['detail']['started']['percent'],2),
                    'started_new': started_new,
                    'total_count': total_count,
                    'total_pct' : round(total_pct,2)
                }
            )

            # save this for later
            with open('previous-' + str(survey['id']) + '.json', 'w') as outfile:
                json.dump(survey_details.json(), outfile, indent=4)





except requests.exceptions.RequestException as e:
    logging.debug(e)
    sys.exit(1)





#########################
# Send Email notification
#########################


#########################
# Logoff
#########################

s.delete(SURVEDA_URL+'/api/v1/sessions')


