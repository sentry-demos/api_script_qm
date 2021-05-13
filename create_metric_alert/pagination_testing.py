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



#Get pagination working for alert - done 
# get pagination working for projects - todo
# assign to team extract from the project get request

alert_list = []
proj_list = []

def store_alerts(json_data, alert_list):

    for item1 in json_data:
        try:
            #print(item1["id"])
            #print(item1["name"])
            alert_list.append(item1["name"])
        except:
            logging.error('create_alert: could not get exisitng alert name')
    print(alert_list)
    
def get_alerts(): 
    global alert_list
    try: 
        response = requests.get(
                f' https://sentry.io/api/0/organizations/testorg-az/alert-rules/',
                headers={'Authorization': 'Bearer ef4ced8eee04494681041f979428245001f71a86013046c1a0632fedbea25462',
                        'Content-Type' : 'application/json'})
    except:
        print('unable to do get request')
        sys.exit()

    try: 
        
        # header = response.headers
        print(response.headers["link"])
        link = response.headers["link"]
        split_link = link.split(';')[-2]
        
        # print(split_link[10:-1])
        results_tf = split_link[10:-1] 
        print('HERE')
        print(results_tf)
        # call method here. 
        #if false everything will be appended to list after first call
        store_alerts(response.json(), alert_list)

        if (results_tf == "true"):
            cursor = link.split(';')[-1]
            cursor = cursor[9:-1]
            print(cursor)

            while link is not None:
            
                try:
                    #print(f'https://sentry.io/api/0/organizations/testorg-az/alert-rules/?&cursor={cursor}')
                    response = requests.get(
                    f' https://sentry.io/api/0/organizations/testorg-az/alert-rules/?&cursor={cursor}',
                    headers={'Authorization': 'Bearer ef4ced8eee04494681041f979428245001f71a86013046c1a0632fedbea25462',
                            'Content-Type' : 'application/json'})
                    #print(response.headers)
                    store_alerts(response.json(), alert_list)
                    try:
                        link = response.headers["link"]
                    except:
                        # that means everything has been appended
                        print('could not get link')
                        link = None
                        sys.exit()

                    
                    split_link = link.split(';')[-2]

                    # print(split_link[10:-1])
                    results_tf = split_link[10:-1] 
                    # print(results_tf)
                    # print('CHECK HERE')
                    if (results_tf == "true"):
                        cursor = link.split(';')[-1]
                        cursor = cursor[9:-1]
                        print(cursor)
                    else:
                        print('setting link to none')
                        link = None # while loop needs to be none if false
                except:
                    print("got exception in inner loop")
                    sys.exit()

            
        else:
            print('extracted all alerts')
    
    except: 
        print('unable to get link')

def store_projects(json_data, proj_list):

    for item1 in json_data:
        try:
            #print(item1["id"])
            #print(item1["name"])
            proj_list.append(item1["name"])
        except:
            logging.error('create_alert: could not get exisitng project names')
    print(proj_list)

def get_projects():
    global proj_list
    try: 
        response = requests.get(
                f' https://sentry.io/api/0/organizations/testorg-az/projects/',
                headers={'Authorization': 'Bearer ef4ced8eee04494681041f979428245001f71a86013046c1a0632fedbea25462',
                        'Content-Type' : 'application/json'})
    except:
        print('unable to do get request')
        sys.exit()

    try: 
        
        # header = response.headers
        print(response.headers["link"])
        link = response.headers["link"]
        split_link = link.split(';')[-2]
        
        # print(split_link[10:-1])
        results_tf = split_link[10:-1] 
        print('HERE')
        print(results_tf)
        # call method here. 
        #if false everything will be appended to list after first call
        store_projects(response.json(), proj_list)
        print('HERE AGAIN')
        if (results_tf == "true"):
            cursor = link.split(';')[-1]
            cursor = cursor[9:-1]
            print(cursor)

            while link is not None:
            
                try:
                    response = requests.get(
                    f' https://sentry.io/api/0/organizations/testorg-az/projects/?&cursor={cursor}',
                    headers={'Authorization': 'Bearer ef4ced8eee04494681041f979428245001f71a86013046c1a0632fedbea25462',
                            'Content-Type' : 'application/json'})
                    #print(response.headers)
                    store_projects(response.json(), proj_list)
                    #print(response.headers)
                    try:
                        link = response.headers["link"]
                    except:
                        # that means everything has been appended
                        print('could not get link')
                        link = None
                        sys.exit()

                    
                    split_link = link.split(';')[-2]

                    # print(split_link[10:-1])
                    results_tf = split_link[10:-1] 
                    # print(results_tf)
                    # print('CHECK HERE')
                    if (results_tf == "true"):
                        cursor = link.split(';')[-1]
                        cursor = cursor[9:-1]
                        print(cursor)
                    else:
                        print('setting link to none')
                        link = None # while loop needs to be none if false
                except:
                    print("got exception in inner loop")
                    sys.exit()

            
        else:
            print('extracted all alerts')
    
    except: 
        print('unable to get link')


def main(argv):
    #store_alerts(json_data, alert_list)
    get_alerts()
    get_projects()
    

if __name__ == '__main__':
     main(sys.argv[1:])