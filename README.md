# Quota Alert API Script

- API script to create metric alert rules on all projects for quota management.
- When defined critical and warning thresholds are met, alerts will send email notifications to all teams assigned to that project.

## Set up

To setup the python env for thhis script:

1. Create env - ```python3 -m venv env```
2. Activate venv - ```source env/bin/activate```
3. Install requirements - ```pip install -r ./requirements.txt```

## Configure


## Run Script 

1. Create Alerts for All Projects

    > ```python3 temp.py```

2. Delete all Alert Rules:

    > ```python3 clean.py```
