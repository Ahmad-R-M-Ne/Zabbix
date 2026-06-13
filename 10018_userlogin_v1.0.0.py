####################################################################################################
# Name: Zabbix _ User Login                                                                        #
# Job: Authenticates a user via Zabbix API and prints the authentication token.                    #
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
# CHECK AUTHENTICATION
#====================================================================================================
def user_login(username, password):
    """
    Authenticate a user via Zabbix API and return token or error.
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
            return None, data["error"]["data"]
        return data.get("result"), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

#====================================================================================================
# MAIN SCRIPT EXECUTION
#====================================================================================================
def main():
    print("Zabbix User Login")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    token, error = user_login(username, password)
    if token:
        print(f"[*] Authentication successful. Token: {token}")
    else:
        print(f"[!] Authentication failed: {error}")

if __name__ == "__main__":
    main()

#====================================================================================================
#End