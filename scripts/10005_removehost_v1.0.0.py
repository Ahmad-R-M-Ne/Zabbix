####################################################################################################
# Name: Zabbix _ Remove Host                                                                       #
# Job: This Script makes an API call to remove a host from the Zabbix-Server.                      #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-10-24                                                                                 #
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
def authenticate():
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
    return result["result"]

#====================================================================================================
# FUNCTION: GET HOST ID BY NAME
#====================================================================================================
def get_host_id(auth_token, host_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host"],
            "filter": {"host": [host_name]}
        },
        "auth": auth_token,
        "id": 2
    }
    r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
    result = r.json()

    if "error" in result:
        print(f"❌ Error while fetching host: {result['error']}")
        sys.exit(1)

    if len(result["result"]) == 0:
        print(f"❌ No host found with name '{host_name}'.")
        sys.exit(1)

    return result["result"][0]["hostid"]

#====================================================================================================
# FUNCTION: DELETE HOST
#====================================================================================================
def delete_host(auth_token, host_id):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.delete",
        "params": [host_id],
        "auth": auth_token,
        "id": 3
    }
    r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
    return r.json()

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
if __name__ == "__main__":
    # User input
    host_name = input("Host name to delete: ")

    # Authenticate
    token = authenticate()
    print("✅ Authenticated successfully.")

    # Get host ID
    host_id = get_host_id(token, host_name)
    print(f"✅ Host '{host_name}' found with ID: {host_id}")

    # Confirm deletion
    confirm = input(f"⚠️ Are you sure you want to delete host '{host_name}' (yes/no)? ").strip().lower()
    if confirm != "yes":
        print("❌ Deletion cancelled by user.")
        sys.exit(0)

    # Delete host
    result = delete_host(token, host_id)

    if "error" in result:
        print(f"❌ Host deletion failed: {result['error']}")
    else:
        print(f"✅ Host '{host_name}' deleted successfully from Zabbix Server.")

#====================================================================================================
#End
