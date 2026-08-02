####################################################################################################
# Name: Zabbix _ User Check Authentication                                                         #
# Job: Checks user authentication status via the Zabbix API. and Return a Authentication Token.    #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-11-08                                                                                 #
####################################################################################################

import json
import requests
import sys

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_URL = "http://192.168.0.1/zabbix/api_jsonrpc.php"

#====================================================================================================
# API CALL FUNCTION
#====================================================================================================
def api_call(auth_token, method, params):
    headers = {'Content-Type': 'application/json-rpc'}
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
        "auth": auth_token
    }
    try:
        response = requests.post(ZABBIX_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            return {"error": data["error"]["data"]}
        return {"result": data.get("result")}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

#====================================================================================================
# CHECK AUTHENTICATION
#====================================================================================================
def check_auth(username, password):
    """
    Attempt to authenticate a user and return status.
    """
    headers = {'Content-Type': 'application/json-rpc'}
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": username,
            "password": password
        },
        "id": 1,
        "auth": None
    }
    try:
        response = requests.post(ZABBIX_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            return False, data["error"]["data"]
        return True, data.get("result")
    except requests.exceptions.RequestException as e:
        return False, str(e)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    print("Check Zabbix user authentication:")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    success, info = check_auth(username, password)
    if success:
        print(f"[*] Authentication successful. Token: {info}")
    else:
        print(f"[!] Authentication failed: {info}")

if __name__ == "__main__":
    main()

#====================================================================================================
#End