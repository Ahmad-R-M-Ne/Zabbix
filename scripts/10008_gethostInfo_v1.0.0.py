####################################################################################################
# Name: Zabbix _ GET Host Info                                                                     #
# Job: This Script connects to the Zabbix-Server API and retrieves information about a specific    #
#      host using the 'host.get' method. It displays Host ID, Visible Name, IP address, Group,     #
#      Template, and monitoring status.                                                            #
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
# FUNCTION: GET SPECIFIC HOST INFO
#====================================================================================================
def get_host_info(auth_token, host_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name", "status"],
            "filter": {"host": [host_name]},
            "selectInterfaces": ["ip"],
            "selectGroups": ["name"],
            "selectParentTemplates": ["name"]
        },
        "auth": auth_token,
        "id": 2
    }

    r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
    result = r.json()

    if "error" in result:
        print(f"❌ Failed to get host info: {result['error']}")
        sys.exit(1)

    if len(result["result"]) == 0:
        print(f"⚠️ No host found with name '{host_name}'.")
        sys.exit(0)

    return result["result"][0]

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
if __name__ == "__main__":
    print("🔎 Zabbix Host Information Lookup")
    host_name = input("Enter the exact Host name: ").strip()

    # Authenticate
    token = authenticate()
    print("✅ Authenticated successfully.")

    # Get host info
    host_info = get_host_info(token, host_name)

    # Extract information
    host_id = host_info.get("hostid", "N/A")
    visible_name = host_info.get("name", "N/A")
    status = "Enabled" if host_info.get("status") == "0" else "Disabled"
    ip_addresses = [iface.get("ip", "N/A") for iface in host_info.get("interfaces", [])]
    group_names = [grp.get("name", "N/A") for grp in host_info.get("groups", [])]
    templates = [tpl.get("name", "N/A") for tpl in host_info.get("parentTemplates", [])]

    # Display host details
    print("\n========================================")
    print(f"🖥️  Host Information for: {host_name}")
    print("========================================")
    print(f"🔹 Host ID       : {host_id}")
    print(f"🔹 Visible Name  : {visible_name}")
    print(f"🔹 IP Address(es): {', '.join(ip_addresses) if ip_addresses else 'No IP'}")
    print(f"🔹 Group(s)      : {', '.join(group_names) if group_names else 'No Group'}")
    print(f"🔹 Template(s)   : {', '.join(templates) if templates else 'No Template'}")
    print(f"🔹 Status        : {status}")
    print("========================================\n")
    print("✅ Host information retrieved successfully.")

#====================================================================================================
#End
