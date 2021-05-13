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


# change print statements to logging.info
# add project name to "successfully created metric alert message"
# pagination for alert and project get request - test with test org and COMMENT OUT CREATE ALERT
#plan 2 - for email
# create test org, project 1, 2 - assigned to team A and 3 , 4 - assigned to team B 
# create new team in his account and jason to be the first member of the team and add new members as needed


#feedback from Jason
# who should be notified from the alert rule
#Plan 1 - slack
# dedicated slack channel - anyone can be added here

sleep_value = 0

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
        #print instead of logging.error since the error file could not be created. 
        print('do_setup: unable to create log file!')

def parse_config():
    # checks for assigned values in config file
    my_file = Path("./config.xml")
    if my_file.is_file():
        # logging.info or debug instead of print
        logging.info('config file exists!')
        try:
            mydoc = minidom.parse('config.xml')
            data = mydoc.getElementsByTagName('item')
            org_name = data[0].firstChild.data
            auth_key = data[1].firstChild.data
            #not being used currently
            team_id = data[2].firstChild.data
            critical_threshold = int(data[3].firstChild.data)
            warning_threshold = int(data[4].firstChild.data)
            sleep_time = int(data[5].firstChild.data)/1000 # given in seconds, sleep time specified in miliseconds in the config file

            
        except:
            logging.error('parse_config: check your config file. There maybe some missing fields.')
            sys.exit()

        return org_name, auth_key, team_id, sleep_time, critical_threshold, warning_threshold

    else: 
        logging.error('config file not found.')
        sys.exit()
# function to check the org name exists - call api 
# warning threshold should be less than the critical threshold
   
def check_org_name(auth_key, org_name):

    org_list = []
    response = requests.get(
            f'https://sentry.io/api/0/organizations/',
            headers={'Authorization': auth_key,
                    'Content-Type' : 'application/json'})
    json_data = response.json()
    for item0 in json_data:
        try:
            #print(item1["id"])
            #print(item1["name"])
            org_list.append(item0["name"])
        except:
            logging.error('check_org_name: was not able to get a list of orgs')
    if org_name in org_list:
        print('the org exist - just testing remove this later')
        logging.info('The org exists!')
    else:
        logging.error('The org provided does not exist. Hint: Check if you misspelled the org name in your config file.')
        sys.exit()

def check_threshold(critical_threshold, warning_threshold):

    print(critical_threshold)
    print(warning_threshold)
    if warning_threshold >= critical_threshold:
        logging.error('warning threshold should not be greater than critical threshold. Please fix assigned values.')
        sys.exit()
    else:
        logging.info('this is correct')

def check_alert(org_name, auth_key):

    alert_list = []
    response = requests.get(
            f'https://sentry.io/api/0/organizations/{org_name}/alert-rules/',
            headers={'Authorization': auth_key,
                    'Content-Type' : 'application/json'})
    json_data = response.json()
    #print(json_data)
    for item1 in json_data:
        try:
            #print(item1["id"])
            #print(item1["name"])
            alert_list.append(item1["name"])
        except:
            logging.error('create_alert: could not get exisitng alert name')
    print(alert_list)

    return alert_list

def create_alerts(org_name, auth_key, team_id, alert_list, sleep_time, critical_threshold, warning_threshold):
    # ct = critical_threshold
    # print(warning_threshold)
    # gets projects names from org and writes to proj_list
    proj_list = []
    response = requests.get(
            f'https://sentry.io/api/0/organizations/{org_name}/projects/',
            headers={'Authorization': auth_key,
                    'Content-Type' : 'application/json'})
        # if there is response data then try converting it to json
   # print(response.status_code)
    if(response.status_code == 200 and len(response.text) > 0):
        try: #checking if response has data to convert
            json_data = response.json()
        except:# if json conversion fails 
            logging.error('create_alert: could not convert http response to json object')
            sys.exit()
    else:
        logging.error('create_alert: HTTP request failed. Status : ' + str(response.status_code) )
        sys.exit()

    for item2 in json_data:
        try:
            proj_list.append(item2["name"])
        except:
            logging.error('create_alert: could not get project name from json object')
    print(proj_list)
 
    alert_creation_count = 1

    for proj_name in proj_list:
        alert_name = proj_name + '_quota_limit_0512_testing'

        if alert_name not in alert_list:

            try:
                # check for 1 horu
                # print(critical_threshold)
                json_data=jsons.dumps({"dataset":"events","eventTypes":["error","default"],"aggregate":"count()","query":"","timeWindow":60,"triggers":[{"label":"critical","alertThreshold":10000,"actions":[{"unsavedId":"ccbcf983-079a-0703-f2a6-ff12d2eb363d","unsavedDateCreated":"2021-05-07T04:35:29.966Z","type":"email","targetType":"user","targetIdentifier":"1005877","options":None}]},{"label":"warning","alertThreshold":8000,"actions":[{"unsavedId":"ccbcf983-079a-0703-f2a6-ff12d2eb363d","unsavedDateCreated":"2021-05-07T04:35:29.966Z","type":"email","targetType":"user","targetIdentifier":"1005877","options":None}]}],"projects" :[proj_name],"environment": None,"resolveThreshold": None,"thresholdType":0,"owner": None,"name":alert_name})
            except:
                logger.error('create_alert: json object creation failed for : ' + proj_name)
                sys.exit()
                
            response = requests.post(
                f'https://sentry.io/api/0/projects/nanditha-test-org/{proj_name}/alert-rules/',
                headers={'Authorization': auth_key,
                        'Content-Type' : 'application/json'}, data=json_data)
            if(response.status_code == 200 or response.status_code == 201):
                logging.info('Successfully created the metric alert for project: ' + proj_name)
            elif (response.status_code == 400):
                print(response.status_code)
                logging.error('create_alert: could not create alert for project: ' + proj_name)
            else: 
                logging.error('recieved the following status code: ' + str(response.status_code))   
            # alert_creation_count += 1

            # if alert_creation_count % 2 == 0:
            time.sleep(sleep_time)
        else:
            logging.info('alert already exists for project ' + proj_name + '!')

  

# def usage():
#     print('how to use')

# def parse_args(argv):
#     global sleep_value
#     #parsing command line arguments
#     try:
#         opts, args = getopt.getopt(argv, "ho:s:v", ["help", "output=", "sleep="])
#     except getopt.GetoptError as err:
#         # print help information and exit:
#         print(err)  # will print something like "option -a not recognized"
#         usage()
#         sys.exit(2)
#     output = None
#     verbose = False
#     for o, a in opts:
#         if o == "-v":
#             verbose = True
#         elif o in ("-h", "--help"):
#             usage()
#             sys.exit()
#         elif o in ("-o", "--output"):
#             output = a
#         elif o in ("-s", "--sleep"):
#             sleep_value = int(a)/1000.0 # user to assign new sleep value using -s 
#         else:
#             assert False, "unhandled option"
#     # ...

 
def main(argv):

    # parse_args(argv)
    current_datetime = get_datetime()
    do_setup(current_datetime)
    org_name, auth_key, team_id, sleep_time, critical_threshold, warning_threshold = parse_config()

    #override value in config file
    # if(sleep_value > 0):
    #     sleep_time = sleep_value

    check_org_name(auth_key, org_name)
    check_threshold(critical_threshold, warning_threshold)
    alert_list = check_alert(org_name, auth_key)
    create_alerts(org_name, auth_key, team_id, alert_list, sleep_time, critical_threshold, warning_threshold)
    

if __name__ == '__main__':
     main(sys.argv[1:])
