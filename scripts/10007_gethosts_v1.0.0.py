####################################################################################################
# Name: Zabbix _ GET Hosts                                                                         #
# Job: This Script connects to the Zabbix-Server via API and retrieves all host information using  #
#      the 'host.get' method. It displays each host's name, visible name, and IP address from the  #
#      system.                                                                                     #
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
# FUNCTION: GET HOST LIST
#====================================================================================================
def get_all_hosts(auth_token):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name"],
            "selectInterfaces": ["ip"]
        },
        "auth": auth_token,
        "id": 2
    }

    r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
    result = r.json()

    if "error" in result:
        print(f"❌ Failed to get hosts: {result['error']}")
        sys.exit(1)

    return result["result"]

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
if __name__ == "__main__":
    print("🔎 Retrieving hosts from Zabbix Server...")

    # Authenticate
    token = authenticate()
    print("✅ Authenticated successfully.")

    # Get all hosts
    hosts = get_all_hosts(token)

    if len(hosts) == 0:
        print("⚠️ No hosts found in Zabbix.")
        sys.exit(0)

    print(f"✅ Found {len(hosts)} hosts:\n")

    for host in hosts:
        ip_list = [iface.get("ip", "N/A") for iface in host.get("interfaces", [])]
        ip_display = ", ".join(ip_list) if ip_list else "No IP"
        print(f"🔹 HostID: {host['hostid']} | Hostname: {host['host']} | Visible Name: {host['name']} | IP: {ip_display}")

    print("\n✅ Host information retrieved successfully.")

#====================================================================================================
#End