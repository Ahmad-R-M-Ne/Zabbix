####################################################################################################
# Name: Zabbix _ Set Host Status                                                                   #
# Job: This Script connects to the Zabbix Server API and allows the user to enable or disable a    #
#      host by entering the hostname. The script authenticates, retrieves the host ID, and updates #
#      its monitoring status using the Zabbix API "host.update" method.                            #
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
# FUNCTION: GET HOST ID BY HOSTNAME
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
        print(f"❌ Failed to retrieve host: {result['error']}")
        sys.exit(1)

    if len(result["result"]) == 0:
        print(f"❌ Host '{host_name}' not found in Zabbix.")
        sys.exit(1)

    return result["result"][0]["hostid"]

#====================================================================================================
# FUNCTION: SET HOST STATUS
#====================================================================================================
def set_host_status(auth_token, host_id, status_value):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
            "hostid": host_id,
            "status": status_value
        },
        "auth": auth_token,
        "id": 3
    }

    r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
    result = r.json()

    if "error" in result:
        print(f"❌ Failed to update host status: {result['error']}")
        sys.exit(1)
    else:
        print(f"✅ Host status updated successfully (hostid={host_id}).")

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
if __name__ == "__main__":
    print("=== Zabbix Server Host Status Control ===")
    host_name = input("Enter the Hostname: ").strip()                                                   # 0 = Enable  Host  (Active Monitoring)
    action = input("Do you want to enable or disable the host? (enable/disable): ").strip().lower()     # 1 = Disable Host  (Pause Monitoring)

    if action not in ["enable", "disable"]:
        print("❌ Invalid input! Please type 'enable' or 'disable'.")
        sys.exit(1)

    status_value = 0 if action == "enable" else 1

    # Authenticate with Zabbix Server
    token = authenticate()
    print("✅ Authenticated successfully.")

    # Get host ID
    host_id = get_host_id(token, host_name)
    print(f"✅ Host '{host_name}' found with ID: {host_id}")

    # Update host status
    set_host_status(token, host_id, status_value)

#====================================================================================================
#End
