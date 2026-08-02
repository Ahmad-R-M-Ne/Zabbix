####################################################################################################
# Name: Zabbix _ GET API Info                                                                      #
# Job: This Script connects to the Zabbix-Server and retrieves the current API version information #
#      using the 'apiinfo.version' method of the Zabbix JSON-RPC interface.                        #
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
HEADERS = {"Content-Type": "application/json-rpc"}

#====================================================================================================
# FUNCTION: GET ZABBIX API VERSION
#====================================================================================================
def get_api_version():
    payload = {
        "jsonrpc": "2.0",
        "method": "apiinfo.version",
        "params": [],
        "id": 1
    }

    try:
        r = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload))
        result = r.json()

        if "error" in result:
            print(f"❌ Failed to get API version: {result['error']}")
            sys.exit(1)

        return result["result"]

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
if __name__ == "__main__":
    print("🔎 Retrieving Zabbix API version information...")

    api_version = get_api_version()

    print(f"✅ Zabbix API is reachable.")
    print(f"📘 Zabbix API Version: {api_version}")

#====================================================================================================
#End
