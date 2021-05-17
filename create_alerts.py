# TODO: some imports might be redundant 
import requests
import jsons
from xml.dom import minidom
import sys
# import getopt
import logging
from datetime import datetime
from pytz import timezone
import pytz
from pathlib import Path
import time
import json
from jproperties import Properties

alert_list = []
projects_dict = {}
headers = {}
configs = Properties()   
script_report = {}

def do_setup():
    global configs
    global headers
    global current_datetime
    required_config_keys = ["ORG_NAME", "AUTH_KEY", "CRITICAL", "WARNING", "SLEEP_TIME", "ALERT_RULE_SUFFIX"]
    try:
        # Init logger
        current_datetime = datetime.now().strftime('%m-%d-%Y_%I:%M:%S %Z')
        logging.basicConfig(filename=f'alert_logfile_{current_datetime}.log', format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %I:%M:%S')
        logging.getLogger().setLevel(logging.ERROR)
        logging.getLogger().setLevel(logging.INFO)

        # Read configuration
        with open('config.properties', 'rb') as config_file:
            configs.load(config_file)

        keys = configs.__dict__
        keys = keys['_key_order']
       
        diff = [i for i in required_config_keys + keys if i not in required_config_keys or i not in keys]
        result = len(diff) == 0
        if not result:
            #print(diff)
            logging.error(f'These config {len(diff)} key(s) are missing from config file: {diff[:5]}')
            sys.exit()

        # for item in required_config_keys:
        #     if item not in keys:
        #         print(item)
        #         logging.error(item + ' is a missing key in your config file.')
        #         logging.error()
                
      
        for key, value in configs.items():
            if(value.data == ''):
                logging.error('Value for ' + key + ' is missing.')
                sys.exit()
            

        # Init request headers
        headers = {'Authorization': "Bearer " + configs.get("AUTH_KEY").data, 'Content-Type' : 'application/json'}
    except Exception as e: 
        print(f'do_setup: failed to setup - {e}')
        sys.exit()

    
def get_alerts(): 
    global alert_list
    global configs
    global headers
    try: 
        response = requests.get(f'https://sentry.io/api/0/organizations/{configs.get("ORG_NAME").data}/alert-rules/', headers = headers)
        store_alerts(response.json())
        while response.links["next"]["results"] == "true":
            response = requests.get(response.links["next"]["url"], headers = headers)
            store_alerts(response.json())   
    except Exception as e:
        print(f'get_alerts: failed to call alert rules api - {e}')
        sys.exit()


def store_alerts(json_data):
    for alert in json_data:
        if "name" in alert:
            alert_list.append(alert["name"])
        else:
            logging.error('store_alerts: could not get existing alert name')


def get_projects():
    global headers
    try: 
        response = requests.get(f' https://sentry.io/api/0/organizations/{configs.get("ORG_NAME").data}/projects/', headers = headers)
        store_projects(response.json())

        while response.links["next"]["results"] == "true":
            response = requests.get(response.links["next"]["url"], headers = headers)
            store_projects(response.json()) 
    except Exception as e:
        logging.error(f'get_project: unable to do get request - {e}')
        sys.exit()


def store_projects(json_data):
    global projects_dict

    for project in json_data:
        try:
            project_name = project["slug"]
            teams = project["teams"]
            projects_dict[project_name] = list()
       
            for team in teams:
                team_id = team["id"]
                projects_dict[project_name].append(team_id)
        except Exception as e:
            logging.error(f'create_project: could not get existing project names - {e}')


def create_alerts():
    global headers
    global projects_dict
    global alert_list
    global script_report
    proj_team_list = []
    team_list = []
    script_report = {"success": 0, "failed": 0, "exists": 0}
    alert_rule_suffix = configs.get("ALERT_RULE_SUFFIX").data

    print('about to create alerts..')
    for proj_name, teams in projects_dict.items():
        alert_name = proj_name.lower() + alert_rule_suffix
        
        if len(teams) == 0:
            script_report["failed"] += 1
            logging.error(f'create_alert: failed to create alert for project: {proj_name} - No teams assigned to project')

        elif alert_name not in alert_list:
            try:
                json_data = build_alert_json(proj_name.lower(), alert_name, teams)
                response = requests.post(
                            f'https://sentry.io/api/0/projects/{configs.get("ORG_NAME").data}/{proj_name}/alert-rules/',
                            headers = headers, 
                            data=json_data)

                if(response.status_code in [200, 201]):
                    script_report["success"] += 1
                    logging.info('create_alert: Successfully created the metric alert ' + alert_name + ' for project: ' + proj_name)
                elif (response.status_code == 400):
                    script_report["failed"] += 1
                    logging.error('create_alert: could not create alert for project: ' + proj_name)
                    logging.error(str(response.json()) + proj_name)
                elif (response.status_code == 403):
                    logging.error('create_alerts: received the following status code: ' + str(response.status_code) + ' \nYou may be using your user level token without the necessary permissions.  \nPlease assign the AUTH_KEY to your org level token and refer to the README on how to create one.')
                    sys.exit()
                else: 
                    script_report["failed"] += 1
                    logging.error('create_alert: received the following status code: ' + str(response.status_code) + ' for project: ' + proj_name)   

            except Exception as e:
                script_report["failed"] += 1
                logging.error(f'create_alert: failed to create alert for project : {proj_name} - {e}')
                           
            time.sleep(int(configs.get("SLEEP_TIME").data)/1000)

        else:
            script_report["exists"] += 1
            logging.info('create_alert: alert already exists for project ' + proj_name + '!') 

def build_alert_json(proj_name_lower, alert_name, teams):
    critical_actions = []
    warning_actions = []
    alert_payload_json = jsons.dumps({"dataset":"events","eventTypes":["error","default"],"aggregate":"count()","query":"","timeWindow":60,"triggers":[{"label":"critical","alertThreshold":int(configs.get("CRITICAL").data),"actions":[]},{"label":"warning","alertThreshold":int(configs.get("WARNING").data),"actions":[]}],"projects" : [proj_name_lower],"environment": None ,"resolveThreshold": None,"thresholdType":0,"owner": None,"name":alert_name})
    json_data = json.loads(alert_payload_json)

    for team_id in teams:
        action = json.loads(jsons.dumps({"type":"email", "targetType":"team", "targetIdentifier": team_id, "options":None}))
        critical_actions.append(action)
        warning_actions.append(action)

    json_data["triggers"][0]["actions"] = critical_actions
    json_data["triggers"][1]["actions"] = warning_actions
    json_data = json.dumps(json_data)
    return json_data


def main(argv):
    global alert_list
    global configs
    global headers
    global script_report
    global current_datetime

    do_setup()    
    get_alerts()
    get_projects()
    create_alerts()

    # Print final script status
    print("Script report:  ", script_report)
    print(f"Check log file alert_logfile_{current_datetime}.log for details.")
    
if __name__ == '__main__':
     main(sys.argv[1:])
