####################################################################################################
# Name: Zabbix _ Server Authentication                                                             #
# Job: This Script is just for Authentication with Zabbix-server using API and Return a Token.     #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-10-23                                                                                 #
####################################################################################################

import requests
import json
import sys

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_URL = "http://192.168.0.1/zabbix/api_jsonrpc.php"
USERNAME = "Admin"
PASSWORD = "zabbix"
HEADERS = {"Content-Type": "application/json-rpc"}

#====================================================================================================
# AUTHENTICATION FUNCTION
#====================================================================================================
payload = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
         "username": USERNAME,
        "password": PASSWORD
     },
    "id": 1
    }
r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
result = r.json()
if "error" in result:
       print(f"❌ Authentication failed: {result}")
       sys.exit(1)
print(result["result"])     #Return The Token back

#====================================================================================================
#End