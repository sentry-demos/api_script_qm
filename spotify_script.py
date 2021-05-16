import requests
import jsons
from xml.dom import minidom
import xmltodict
import sys
import getopt
import logging
from datetime import datetime
from pytz import timezone
import pytz
from pathlib import Path
import time
import json

alert_list = []
proj_list = []
sample_dict = {}

def get_datetime():
    date_format='%m-%d-%Y_%I:%M:%S %Z'
    date = datetime.now()

    my_timezone=timezone('US/Pacific')

    date = my_timezone.localize(date)
    date = date.astimezone(my_timezone)
    current_datetime = date.strftime(date_format)

    return current_datetime


def do_setup(current_datetime):

    try:
        logging.basicConfig(filename=f'alert_logfile_{current_datetime}.log', format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %I:%M:%S')
        logging.getLogger().setLevel(logging.ERROR)
        logging.getLogger().setLevel(logging.INFO)
    
    except: 
        print('do_setup: unable to create log file!')

def parse_config():
    my_file = Path("./config.xml")
    if my_file.is_file():
        logging.info('config file exists!')
        try:
            mydoc = minidom.parse('config.xml')
            data = mydoc.getElementsByTagName('item')
            org_name = data[0].firstChild.data
            auth_key = data[1].firstChild.data
 
            team_id = data[2].firstChild.data
            critical_threshold = int(data[3].firstChild.data)
            warning_threshold = int(data[4].firstChild.data)
            sleep_time = int(data[5].firstChild.data)/1000 

            
        except:
            logging.error('parse_config: check your config file. There maybe some missing fields.')
            sys.exit()

        return org_name, auth_key, team_id, sleep_time, critical_threshold, warning_threshold

    else: 
        logging.error('config file not found.')
        sys.exit()


def check_threshold(critical_threshold, warning_threshold):

    print(critical_threshold)
    print(warning_threshold)
    if warning_threshold >= critical_threshold:
        logging.error('warning threshold should not be greater than critical threshold. Please fix assigned values.')
        sys.exit()
    else:
        logging.info('this is correct')


def store_alerts(json_data, alert_list):

    for item1 in json_data:
        try:
            alert_list.append(item1["name"])
        except:
            logging.error('store_alerts: could not get exisitng alert name')
    print(alert_list)
    
def get_alerts(auth_key, org_name): 
    global alert_list
    try: 
        response = requests.get(
                f' https://sentry.io/api/0/organizations/{org_name}/alert-rules/',
                headers={'Authorization': auth_key,
                        'Content-Type' : 'application/json'})
    except:
        logging.error('get_alerts: unable to do get request')
        sys.exit()

    try: 
        
    
        #print(response.headers["link"])
        link = response.headers["link"]
        split_link = link.split(';')[-2]
        

        results_tf = split_link[10:-1] 
        #print(results_tf)
        store_alerts(response.json(), alert_list)

        if (results_tf == "true"):
            cursor = link.split(';')[-1]
            cursor = cursor[9:-1]
            print(cursor)

            while link is not None:
            
                try:
                    response = requests.get(
                    f' https://sentry.io/api/0/organizations/{org_name}/alert-rules/?&cursor={cursor}',
                    headers={'Authorization': auth_key,
                            'Content-Type' : 'application/json'})
           
                    store_alerts(response.json(), alert_list)
                    try:
                        link = response.headers["link"]
                    except:
                        logging.info('could not get link')
                        link = None
                        sys.exit()

                    
                    split_link = link.split(';')[-2]

                   
                    results_tf = split_link[10:-1] 
                   
                    if (results_tf == "true"):
                        cursor = link.split(';')[-1]
                        cursor = cursor[9:-1]
                        print(cursor)
                    else:
                        print('setting link to none')
                        link = None 
                except:
                    print("got exception in inner loop")
                    sys.exit()

            
        else:
            print('extracted all alerts')
    
    except: 
        print('unable to get link')

def store_projects(json_data, proj_list):
    global sample_dict
   
    for item1 in json_data:
        try:

            project_name = item1["slug"]
            teams = item1["teams"]
            sample_dict[project_name] = list()
       
            for team in teams:
                team_id = team["id"]
                sample_dict[project_name].append(team_id)
        except:
            logging.error('create_alert: could not get exisitng project names')
    #print(proj_list)
    #print(sample_dict)

def get_projects(auth_key, org_name):
    global proj_list
    try: 
        response = requests.get(
                f' https://sentry.io/api/0/organizations/{org_name}/projects/',
                headers={'Authorization': auth_key,
                        'Content-Type' : 'application/json'})
    except:
        #print('unable to do get request')
        logging.error('unable to do get request')
        sys.exit()

    try: 
        #print(response.headers["link"])
        link = response.headers["link"]
        split_link = link.split(';')[-2]
        

        results_tf = split_link[10:-1] 
        print(results_tf)
        #if false everything will be appended to list after first call
        store_projects(response.json(), proj_list)
        print("\n\n\n")
        if (results_tf == "true"):
            cursor = link.split(';')[-1]
            cursor = cursor[9:-1]
            #print(cursor)

            while link is not None:
            
                try:
                    response = requests.get(
                    f' https://sentry.io/api/0/organizations/{org_name}/projects/?&cursor={cursor}',
                    headers={'Authorization': auth_key,
                            'Content-Type' : 'application/json'})
  
                    store_projects(response.json(), proj_list)
             
                    try:
                        link = response.headers["link"]
                    except:
                        # this means everything has been appended
                        print('could not get link')
                        link = None
                        sys.exit()
                    
                    split_link = link.split(';')[-2]
                    results_tf = split_link[10:-1] 
                
                    if (results_tf == "true"):
                        cursor = link.split(';')[-1]
                        cursor = cursor[9:-1]
                        #print(cursor)
                    else:
                        print('pagination is complete - setting link to none')
                        link = None # while loop needs to be none if false
                except:
                    print("got exception in inner loop")
                    sys.exit()

            
        else:
            print('extracted all alerts')
    
    except: 
        print('unable to get link')



def create_alerts(org_name, auth_key, sleep_time, critical_threshold, warning_threshold, proj_teams_dict, alert_list):
 
    proj_team_list = []
    sample_dict = {}
    team_list = []
    critical_actions = []
    warning_actions = []
    
 
    for proj_name, teams in proj_teams_dict.items():
        critical_actions = []
        warning_actions = []
        proj_lower = proj_name.lower()
        alert_name = proj_lower + '_quota_limit_0515'
        
        if alert_name not in alert_list:

            try:
                x = jsons.dumps({"dataset":"events","eventTypes":["error","default"],"aggregate":"count()","query":"","timeWindow":60,"triggers":[{"label":"critical","alertThreshold":10000,"actions":[]},{"label":"warning","alertThreshold":8000,"actions":[]}],"projects" : [proj_lower],"environment": None ,"resolveThreshold": None,"thresholdType":0,"owner": None,"name":alert_name})
                json_data = json.loads(x)

                for team_id in teams:

                    action = jsons.dumps({"unsavedId":"ccbcf983-079a-0703-f2a6-ff12d2eb363d","unsavedDateCreated":"2021-05-07T04:35:29.966Z","type":"email","targetType":"team","targetIdentifier": team_id,"options":None})
                    action = json.loads(action)
                    critical_actions.append(action)
                    warning_actions.append(action)
                json_data["triggers"][0]["actions"] = critical_actions
                json_data["triggers"][1]["actions"] = warning_actions
                json_data = json.dumps(json_data)
                response = requests.post(
                            f'https://sentry.io/api/0/projects/{org_name}/{proj_name}/alert-rules/',
                            headers={'Authorization': auth_key,
                                    'Content-Type' : 'application/json'}, data=json_data)
                
            except:
                logging.error('create_alert: json object creation failed for : ' + proj_name)
                sys.exit()
                
            if(response.status_code == 200 or response.status_code == 201):
                print('Successfully created the metric alert ' + alert_name + ' for project: ' + proj_lower)
                logging.info('Successfully created the metric alert ' + alert_name + ' for project: ' + proj_lower)
            elif (response.status_code == 400):
                # print(response.status_code)
                #print(response.json())
                logging.error('create_alert: could not create alert for project: ' + proj_lower)
                logging.error(str(response.json()) + proj_lower)
            else: 
                print("alert name: " + alert_name)
                print(response.status_code)
                # print(response.json())
                print('recieved the following status code: ' + str(response.status_code) + ' for project: ' + proj_lower) 
                logging.error('recieved the following status code: ' + str(response.status_code) + ' for project: ' + proj_lower)   
           
            time.sleep(sleep_time)
        else:
            print('alert already exists for project ' + proj_name + '!')
            logging.info('alert already exists for project ' + proj_name + '!')

  
 
def main(argv):

    global alert_list
    global proj_list
    current_datetime = get_datetime()
    do_setup(current_datetime)
    org_name, auth_key, team_id, sleep_time, critical_threshold, warning_threshold = parse_config()

    # # check_org_name(auth_key, org_name)
    # check_threshold(critical_threshold, warning_threshold)
    
    get_alerts(auth_key, org_name)
    get_projects(auth_key, org_name)

    create_alerts(org_name, auth_key, sleep_time, critical_threshold, warning_threshold, sample_dict, alert_list)
    

if __name__ == '__main__':
     main(sys.argv[1:])
