I've created this script to gather main headlines from news sites for further analysis.
---
The app scraps headlines and appends google spreadsheet with data.
Because of this there are few things needed before you can use this script.

Set env variable for:
- `SPREADSHEET_ID` - with ID of your google spreadsheet
- `WORKDIR` - full path to directory where the script is located

To remain logged in to Google, you need to generate service account credentials [here](https://console.developers.google.com/apis/api/sheets.googleapis.com/credentials) and put the `creds.json` in working directory.

Remember to add your service account email as an editor in your spreadsheet.

You can also run `setup_cronjob.sh` which will add a cronjob to your crontab and run this script every 10 minutes.
