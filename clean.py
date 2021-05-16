# TODO: some imports might be redundant 
import requests
import jsons
from xml.dom import minidom
# import xmltodict
import sys
import getopt
import logging
from datetime import datetime
from pytz import timezone
import pytz
from pathlib import Path
import time
import json
from jproperties import Properties

alert_list = []
headers = {}
script_report = {}
configs = Properties() 

def do_setup():
    global configs
    global headers
    try:
        # Init logger
        current_datetime = datetime.now().strftime('%m-%d-%Y_%I:%M:%S %Z')
        logging.basicConfig(filename=f'alert_clean_logfile_{current_datetime}.log', format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %I:%M:%S')
        logging.getLogger().setLevel(logging.ERROR)
        logging.getLogger().setLevel(logging.INFO)

        # Read configuration
        with open('config.properties', 'rb') as config_file:
            configs.load(config_file)
        
        # Init request headers
        headers = {'Authorization': "Bearer " + configs.get("AUTH_KEY").data, 'Content-Type' : 'application/json'}
    except Exception as e: 
        print(f'failed to setup - {e}')
        sys.exit()


def handle_alerts(): 
    global alert_list
    global configs
    global headers
    global script_report

    script_report = {"quota_alerts_found": 0, "delete_success": 0, "delete_fail": 0}
    alerts_json_arr=[]
    alert_rule_suffix = configs.get("ALERT_RULE_SUFFIX").data

    try: 
        response = requests.get(
            f'https://sentry.io/api/0/organizations/{configs.get("ORG_NAME").data}/alert-rules/', 
            headers = headers)        
        alerts_json_arr += response.json()

        #Get all alerts
        while response.links["next"]["results"] == "true":
            response = requests.get(response.links["next"]["url"], headers = headers)
            alerts_json_arr += response.json()

        logging.info(f'handle_alerts: Found a total number of: {len(alerts_json_arr)} alerts.')

        # Filter and delete quota alerts
        for alert in alerts_json_arr:
            if "name" not in alert: 
                logging.error(f'handle_alerts: Ignoring alert, no name for {alert}')

            elif alert["name"].endswith(alert_rule_suffix):
                script_report["quota_alerts_found"] += 1
                #print(f'Found alert: {alert["name"]} in Project - {alert["projects"][0]}')
                delete_alert(alert["name"], alert["id"], alert["projects"][0])
                time.sleep(int(configs.get("SLEEP_TIME").data)/1000)
            else:
                logging.info(f'handle_alerts: Not deleting alert {alert["name"]}')

    except Exception as e:
        print(f'failed to call alert rules api - {e}')
        sys.exit()

def delete_alert(alert_name, alert_id, project_slug):
    global headers
    global configs
    global script_report

    try:
        response = requests.delete(
            f'https://sentry.io/api/0/projects/{configs.get("ORG_NAME").data}/{project_slug}/alert-rules/{alert_id}/', 
            headers = headers)

        if(response.status_code in [200, 204]):
            script_report["delete_success"] += 1
            logging.info('Successfully deleted metric alert ' + alert_name + ' for project: ' + project_slug)
        elif (response.status_code == 400):
            script_report["delete_fail"] += 1
            logging.error('delete_alert: could not delete alert for project: ' + project_slug)
            logging.error(str(response.json()) + project_slug)
        else: 
            script_report["delete_fail"] += 1
            logging.error('delete_alert: received the following status code: ' + str(response.status_code) + ' for project: ' + project_slug)   

    except Exception as e:
        print(f'failed to delete alert rule - {alert_name}')
        script_report["delete_fail"] += 1
        
        
def main(argv):
    global alert_list
    global configs
    global headers
    global script_report
    
    do_setup()    
    handle_alerts()

    # Print final script status
    print("Script report:  ", script_report)
    
if __name__ == '__main__':
     main(sys.argv[1:])
