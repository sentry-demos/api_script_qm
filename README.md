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


Required:

1. `ORG_NAME= <org name> ` - This should be assigned to your Organization Slug, found under Settings --> General Settings.
3. `AUTH_KEY= <auth_key>` - Your auth key can be found under Settings --> Account --> API --> Auth Tokens.

Optional:

5. `SLEEP_TIME=<milliseconds>` = When updating sleep time, please provide this value in milliseconds.
6. `ALERT_RULE_SUFFIX=_quota_limit` - If you would like to rename the alert rule suffix, this can be done in the config file. 


## Run Script 

1. Create Alerts for All Projects

    > ```python3 create_alerts.py```

2. Delete all Alert Rules:

    > ```python3 clean.py```


## Confirm Alert Creation

1. To confirm via UI navigate to the Alerts page to view the created alerts.
2. By running python3 create_alerts.py a second time you can confirm if the alert already exists. (Check the log file for "alert already exists for + [project name]!")
