####################################################################################################
# Name: Zabbix _ Create New Host                                                                   #
# Job: This Script makes a API to Adding a new host to the zabbix-server                           #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-10-18                                                                                 #
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
# FUNCTION: GET HOST GROUP ID
#====================================================================================================
def get_hostgroup_id(auth_token, group_name):
    payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "filter": {"name": [group_name]}
        },
        "auth": auth_token,
        "id": 2
    }
    r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
    result = r.json()

    if len(result["result"]) == 0:
        # Create the host group if it doesn't exist
        create_payload = {
            "jsonrpc": "2.0",
            "method": "hostgroup.create",
            "params": {"name": group_name},
            "auth": auth_token,
            "id": 3
        }
        r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(create_payload))
        create_result = r.json()
        return create_result["result"]["groupids"][0]
    else:
        return result["result"][0]["groupid"]

#====================================================================================================
# FUNCTION: CREATE HOST
#====================================================================================================
def create_host(auth_token, host_name, visible_name, group_id, template_id, ip_address, snmp_version, snmp_community, description):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.create",
        "params": {
            "host": host_name,
            "name": visible_name,
            "interfaces": [{
                "type": 2,  # 1=Agent, 2=SNMP
                "main": 1,
                "useip": 1,
                "ip": ip_address,
                "dns": "",
                "port": "161",
                "details": {
                    "version": int(snmp_version),
                    "community": snmp_community
                }
            }],
            "groups": [{"groupid": group_id}],
            "templates": [{"templateid": template_id}],
            "description": description
        },
        "auth": auth_token,
        "id": 4
    }
    r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
    return r.json()

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
if __name__ == "__main__":
    # User input
    host_name = input("Host name: ")
    visible_name = input("Visible name: ")
    group_name = input("Host group name: ")
    ip_address = input("Host IP: ")
    snmp_version = input("SNMP version (1 or 2): ")
    snmp_community = input("SNMP community: ")
    description = input("Description: ")
    template_id = input("Template ID (numeric): ")

    # Authenticate
    token = authenticate()
    print("✅ Authenticated successfully.")

    # Get or create host group
    group_id = get_hostgroup_id(token, group_name)
    print(f"✅ Host group ID: {group_id}")

    # Create host
    result = create_host(token, host_name, visible_name, group_id, template_id, ip_address, snmp_version, snmp_community, description)

    if "error" in result:
        print(f"❌ Host creation failed: {result['error']}")
    else:
        print(f"✅ Host '{host_name}' created successfully with ID: {result['result']['hostids'][0]}")
        
#====================================================================================================
#End
