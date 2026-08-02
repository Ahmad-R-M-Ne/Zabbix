####################################################################################################
# Name: Zabbix _ Add New Host                                                                      #
# Job: This Script makes a API to Adding a new host to the zabbix-server, it requires Hostname,    #
#      ip, SNMP Version, Community, and One or More Template UIDs.                                 #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-01-04                                                                                 #
####################################################################################################

import requests
import json
import sys

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_URL = "http://192.168.0.1/zabbix/api_jsonrpc.php"
USERNAME = ""
PASSWORD = ""
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
def create_host(auth_token, host_name, visible_name, group_id, template_ids, ip_address, snmp_version, snmp_community, description):

    templates_list = []
    for tid in template_ids:
        templates_list.append({"templateid": tid})

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
            "templates": templates_list,
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

    host_name = input("Host name: ")
    visible_name = input("Visible name: ")
    group_name = input("Host group name: ")
    ip_address = input("Host IP: ")
    snmp_version = input("SNMP version (1 or 2): ")
    snmp_community = input("SNMP community: ")
    description = input("Description: ")

    template_ids_input = input("Template ID (numeric) (Seperate Multiple Templates with comma): ")

    # Convert comma-separated input into clean list
    template_ids = [tid.strip() for tid in template_ids_input.split(",") if tid.strip()]

    if not template_ids:
        print("❌ No valid Template IDs provided")
        sys.exit(1)

    token = authenticate()
    print("✅ Authenticated successfully.")

    group_id = get_hostgroup_id(token, group_name)
    print(f"✅ Host group ID: {group_id}")

    result = create_host(
        token,
        host_name,
        visible_name,
        group_id,
        template_ids,
        ip_address,
        snmp_version,
        snmp_community,
        description
    )

    if "error" in result:
        print(f"❌ Host creation failed: {result['error']}")
    else:
        print(f"✅ Host '{host_name}' created successfully with ID: {result['result']['hostids'][0]}")

#====================================================================================================
#End
