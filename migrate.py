import os
import boto3
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account

load_dotenv()


# Define news sites and headline class.
SITES = {'tvn24':
         {
             'url': 'https://tvn24.pl',
             'headline_selector': 'top-story__header'
         },
         'tvp.info':
         {
             'url': 'https://tvp.info/',
             'headline_selector': 'main-module__news-title'}
         }

# Define Google Spreadsheets const.
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets']

# Define DB config.
ENDPOINT = os.getenv('AWS_ENDPOINT')
USR = os.getenv('AWS_USER')
REGION = os.getenv('AWS_REGION')
DBNAME = "news-db"
PORT = "5432"

# gets the credentials from .aws/credentials
session = boto3.Session(profile_name='default')
client = boto3.client('rds')


# Generates AWS RDS token.
def get_db_token():
    t = client.generate_db_auth_token(
        DBHostname=ENDPOINT,
        Port=PORT,
        DBUsername=USR,
        Region=REGION)
    return t


# DB helper class
class DB:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=ENDPOINT,
                port=PORT,
                database=DBNAME,
                user=USR,
                password=get_db_token())
        except Exception as e:
            print("Database connection failed due to {}".format(e))

    def shutdown(self):
        self.conn.close()


def login_to_google_sheets():
    creds = service_account.Credentials.from_service_account_file(
        f'{os.getcwd()}/creds.json', scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return service, sheet


def import_to_db(app, values):
    try:
        cursor = app.conn.cursor()
        query = f"INSERT INTO headlines (headline, time_stamp, site) VALUES %s"
        execute_values(cursor, query, values)
        app.conn.commit()
        cursor.close()
    except Exception as e:
        print("Can't connect. Invalid dbname, user or password?")
        print(e)


def migrate():
    app = DB()
    service, sheet = login_to_google_sheets()
    for site in SITES.keys():
        app.shutdown()
        app = DB()
        range_name = f'{site}!A:B'
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=range_name).execute()
        vals = result.get('values', [])
        site = site.replace('.', '')
        t_format = '%m/%d/%Y, %H:%M:%S'
        inp = [(h, datetime.strptime(t, t_format), site) for h, t in vals[1:]]
        import_to_db(app, inp)


if __name__ == "__main__":
    migrate()
