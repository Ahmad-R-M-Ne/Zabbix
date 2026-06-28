####################################################################################################
# Name: Zabbix _ Get All Templates                                                                 #
# Job: This Script Connects to The Zabbix-Server and Retrieves a Full List of Templates            #
#      Along With Their Corresponding UIDs.                                                        #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-01-04                                                                                 #
####################################################################################################

import requests
import json

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_URL = "http://192.168.0.1/zabbix/api_jsonrpc.php"
USERNAME = ""
PASSWORD = ""

#====================================================================================================
# AUTHENTICATION FUNCTION
#====================================================================================================
# Step 1: Authenticate
auth_payload = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
        "username": USERNAME,
        "password": PASSWORD
    },
    "id": 1
}

response = requests.post(ZABBIX_URL, json=auth_payload)
auth_token = response.json().get("result")

if not auth_token:
    print("Authentication failed")
    exit()

#====================================================================================================
# Step 2: Retrieve All Templates And Their UIDs
#====================================================================================================

template_payload = {
    "jsonrpc": "2.0",
    "method": "template.get",
    "params": {
        "output": ["templateid", "name"]
    },
    "auth": auth_token,
    "id": 2
}

response = requests.post(ZABBIX_URL, json=template_payload)
templates = response.json().get("result", [])

if not templates:
    print("No templates found")
    exit()

print("Templates List And Their UIDs :\n")

for template in templates:
    template_name = template.get("name")
    template_id = template.get("templateid")
    print(f"Template Name : {template_name}  |  Template UID : {template_id}")

#====================================================================================================
#End
