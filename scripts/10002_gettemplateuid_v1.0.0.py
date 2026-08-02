####################################################################################################
# Name: Zabbix _ Get Template UID                                                                  #
# Job: This Script Connect to The Zabbix-Server and Get a UID of a Specefic Template.              #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-10-18                                                                                 #
####################################################################################################

import requests
import json

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_URL = "http://192.168.0.1/zabbix/api_jsonrpc.php"
USERNAME = "Admin"
PASSWORD = "zabbix"

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
# Step 2: Retrieve Template ID
#====================================================================================================
#The "name" Part Must be the Exact name Of The Specific Template ***

template_payload = {
    "jsonrpc": "2.0",
    "method": "template.get",
    "params": {
        "filter": {
            "name": ["Cisco IOS by SNMP"]
        },
        "output": ["templateid"]
    },
    "auth": auth_token,
    "id": 2
}

response = requests.post(ZABBIX_URL, json=template_payload)
template_id = response.json().get("result", [{}])[0].get("templateid")

#The Part In '' Must be the Exact name Of The Specific Template ***

if template_id:
    print(f"Template ID for Requsted Template is : {template_id}")
else:
    print("Template not found")

#====================================================================================================
#End

