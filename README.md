# Quota Alert API Script

## Summary:

- API script to create metric alert rules on all projects for quota management.
- When defined critical and warning thresholds are met, alerts will send email notifications to all teams assigned to that project.

## Initial Setup

To setup the python env for this script:

1. Create env - ```python3 -m venv env```
2. Activate venv - ```source env/bin/activate```
3. Install requirements - ```pip install -r ./requirements.txt```

## Configure

Prior to running create_alerts.py, you can configure the following fields in the config.properties file:

1. `ORG_NAME= <org name> ` - This should be assigned to your Organization Slug, found under Settings --> General Settings.

2. `AUTH_KEY= <auth_key>` - Your **org level** auth key can be found under Settings --> Developer Settings --> Internal Integrations.

    a. If you don't have Internal Integrations set up, select New Internal Integrations and provide a Name for your integration. 

    b. The Project and Organization permissions should be set to Read & Write. 
    <img width="957" alt="Screen Shot 2021-05-17 at 2 29 02 PM" src="https://user-images.githubusercontent.com/82904656/118559227-7849c580-b71c-11eb-83ea-2b7fcdbe9461.png">
    
    c. Once the above fields have been configured, click on Save Changes.

    d. This should redirect you to your Internal Integrations page with a token. This token is your **org level** auth key. 

3. `CRITICAL=10000` - Critical threshold is set in the config file. No need to modify this value. 
4. `WARNING=8000` - Warning threshold is set in the config file. No need to modify this value. 
5. `SLEEP_TIME=<milliseconds>` - When updating sleep time, please provide this value in milliseconds.
6. `ALERT_RULE_SUFFIX=_quota_limit` - If you would like to rename the alert rule suffix, this can be done in the config file. 


## Run Script 

1. Create Alerts for All Projects

    > ```python3 create_alerts.py```

2. Delete all Alert Rules:

    > ```python3 clean.py```


## Confirm Alert Creation

1. To confirm via UI navigate to the Alerts page to view the created alerts.
2. By running python3 create_alerts.py a second time you can confirm if the alert already exists. (Check the log file for `"alert already exists for + [project name]!"`)

## Debug and Logging

After running the script you will see a log file created with the following naming convention - `alert_logfile_{current_datetime}.log`

Potential error and info logs will be displayed here. 

## Reminder

To successfully create a metric alert make sure each project has at least one team assigned to it! 
