from __future__ import print_function

import configparser
from datetime import datetime, timezone
import json
import os.path

# pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
# Python 3.10.7 or greater
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

connext_core_guild_id = int(c["DISCORD"]["connext_core_guild"])
connext_on_call_calendar = str(c["GENERAL"]["connext_on_call_calendar"])

import database

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def update_db_from_calendar():
    creds = check_token()
    db_connection = database.get_db_connection()
    # database.initial_setup()  ### delete this in production!

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId=connext_on_call_calendar,
                                              timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        calendar_ids = []
        for event in events:
            calendar_id = str(event["id"])
            calendar_ids.append(calendar_id)


            try:
                start = datetime.strptime(event['start'].get('dateTime', event['start'].get('date')), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                end = datetime.strptime(event['end'].get('dateTime', event['end'].get('date')), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                start = datetime.strptime(event['start'].get('dateTime', event['start'].get('date')), "%Y-%m-%dT%H:%M:%S%z")
                end = datetime.strptime(event['end'].get('dateTime', event['end'].get('date')), "%Y-%m-%dT%H:%M:%S%z")

            for attendee in event['attendees']:
                if "@connext.network" in attendee['email']:
                    user_email = attendee["email"]
                    user_response = attendee["responseStatus"]
                    user = json.load(open("usermap.json"))[user_email]

                    # if we don't already have the calendar event in our database
                    if calendar_id not in database.get_all_calendar_ids(db_connection, connext_core_guild_id):
                        success = database.add_to_schedule(db_connection, calendar_id, user, str(start), str(end), connext_core_guild_id)
                    else:
                        success = database.update_schedule(db_connection, calendar_id, user, str(start), str(end), connext_core_guild_id)

        for db_cal_id in database.get_all_calendar_ids(db_connection, connext_core_guild_id):
            if db_cal_id not in calendar_ids:
                database.remove_from_schedule_by_calendar_id(db_connection, db_cal_id)

    except HttpError as error:
        print('An error occurred: %s' % error)

    db_connection.close()


def check_token():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is created
    # automatically when the authorization flow completes for the first time.

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


update_db_from_calendar()
