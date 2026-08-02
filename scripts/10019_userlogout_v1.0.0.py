####################################################################################################
# Name: Zabbix _ User Logout                                                                       #
# Job: Logs Out a User Session from Zabbix Server.                                                 #
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
# USER LOGIN FUNCTION
#====================================================================================================
def user_login(username, password):
    """
    Authenticate a user and return token.
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
# USER LOGOUT FUNCTION
#====================================================================================================
def user_logout(auth_token):
    """
    Logs out the user session identified by auth_token.
    """
    headers = {'Content-Type': 'application/json-rpc'}
    payload = {
        "jsonrpc": "2.0",
        "method": "user.logout",
        "params": [],
        "id": 1,
        "auth": auth_token
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
    print("Zabbix User Login & Logout")
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    token, error = user_login(username, password)
    if not token:
        print(f"[!] Login failed: {error}")
        return

    print(f"[*] Login successful. Token: {token}")

    confirm = input("Do you want to log out this session? [y/N]: ").strip().lower()
    if confirm != "y":
        print("[*] Logout canceled.")
        return

    success, info = user_logout(token)
    if success:
        print("[*] User logged out successfully.")
    else:
        print(f"[!] Logout failed: {info}")

if __name__ == "__main__":
    main()

#====================================================================================================
#End