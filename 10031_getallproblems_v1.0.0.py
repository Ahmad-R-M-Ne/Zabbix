####################################################################################################
# Name: Zabbix _ Get All Problems                                                                  #
# Job: Get all Zabbix trigger problems in the last X hours using Zabbix API.                       #
#      - Compatible with Zabbix Version 5.0.4                                                      #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-06-30                                                                                 #
####################################################################################################

import requests
import json
import getpass
import sys
import time
from datetime import datetime

#====================================================================================================
# Normalize Zabbix API URL
#====================================================================================================

def normalize_zabbix_url(url):                             # Convert normal Zabbix frontend URL to Zabbix API URL.

    url = url.strip().rstrip("/")

    if url.endswith("api_jsonrpc.php"):
        return url

    return url + "/api_jsonrpc.php"

#====================================================================================================
# Send Request to Zabbix API
#====================================================================================================

def zabbix_api_request(api_url, method, params, auth_token=None, request_id=1):     # Send JSON-RPC request to Zabbix API.

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }

    # user.login does not need auth token
    if auth_token:
        payload["auth"] = auth_token

    headers = {
        "Content-Type": "application/json-rpc"
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

    except requests.exceptions.RequestException as error:
        print(f"[ERROR] Connection error: {error}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("[ERROR] Invalid JSON response from Zabbix server.")
        sys.exit(1)

    if "error" in result:
        error_data = result["error"]

        print("[ERROR] Zabbix API Error")
        print(f"Code    : {error_data.get('code')}")
        print(f"Message : {error_data.get('message')}")
        print(f"Data    : {error_data.get('data')}")

        sys.exit(1)

    return result.get("result")

#====================================================================================================
# Login to Zabbix
#====================================================================================================

def zabbix_login(api_url, username, password):

    params = {
        "user": username,                                  # "user" in zabbix version 5.0.4 API
        "password": password
    }

    token = zabbix_api_request(
        api_url=api_url,
        method="user.login",
        params=params,
        request_id=1
    )

    return token

#====================================================================================================
# Logout from Zabbix
#====================================================================================================

def zabbix_logout(api_url, auth_token):

    try:
        zabbix_api_request(
            api_url=api_url,
            method="user.logout",
            params=[],
            auth_token=auth_token,
            request_id=99
        )
    except Exception:
        pass

#====================================================================================================
# Convert Severity Number to Name
#====================================================================================================

def severity_to_name(severity):

    severities = {
        "0": "Not classified",
        "1": "Information",
        "2": "Warning",
        "3": "Average",
        "4": "High",
        "5": "Disaster"
    }

    return severities.get(str(severity), "Unknown")

#====================================================================================================
# Convert Unix Timestamp to Human-Readable Time
#====================================================================================================

def timestamp_to_datetime(timestamp_value):                # Convert Unix timestamp to readable local datetime.

    if not timestamp_value:
        return "N/A"

    try:
        timestamp_value = int(timestamp_value)
    except ValueError:
        return "N/A"

    if timestamp_value == 0:
        return "N/A"

    return datetime.fromtimestamp(timestamp_value).strftime("%Y-%m-%d %H:%M:%S")

#====================================================================================================
# Convert Seconds to Human-Readable Duration
#====================================================================================================

def seconds_to_duration(seconds):
    """
    Convert seconds to readable duration.
    Example: 93784 seconds -> 1d 02h 03m 04s
    """
    try:
        seconds = int(seconds)
    except ValueError:
        return "N/A"

    days = seconds // 86400
    seconds = seconds % 86400

    hours = seconds // 3600
    seconds = seconds % 3600

    minutes = seconds // 60
    seconds = seconds % 60

    return f"{days}d {hours:02d}h {minutes:02d}m {seconds:02d}s"

#====================================================================================================
# Get Problems From Last X Hours
#====================================================================================================

def get_problem_events(api_url, auth_token, hours):
    """
    Get all trigger PROBLEM events from the last X hours.
    Important Zabbix event fields:
        source = 0  -> Trigger event
        object = 0  -> Trigger object
        value  = 1  -> Problem event
    """

    current_time = int(time.time())
    time_from = current_time - int(hours * 3600)

    params = {
        "output": [
            "eventid",
            "source",
            "object",
            "objectid",
            "clock",
            "value",
            "name",
            "severity",
            "acknowledged",
            "r_eventid"
        ],

        "selectHosts": [
            "hostid",
            "host",
            "name"
        ],

        "selectRelatedObject": [
            "triggerid",
            "description",
            "priority",
            "expression",
            "status",
            "value"
        ],

        "selectAcknowledges": [
            "acknowledgeid",
            "userid",
            "clock",
            "message",
            "action"
        ],

        "selectTags": "extend",

        "filter": {
            "source": "0",
            "object": "0",
            "value": "1"
        },

        "time_from": time_from,
        "time_till": current_time,

        "sortfield": "clock",
        "sortorder": "DESC"
    }

    events = zabbix_api_request(
        api_url=api_url,
        method="event.get",
        params=params,
        auth_token=auth_token,
        request_id=2
    )

    return events, time_from, current_time

#====================================================================================================
# Get Recovery Events
#====================================================================================================

def get_recovery_events(api_url, auth_token, problem_events):
    """
    Get recovery OK events for resolved problems.
    A problem event has r_eventid.
    If r_eventid is 0, the problem is still active.
    If r_eventid is not 0, that ID points to the recovery event.
    """
    recovery_event_ids = []

    for event in problem_events:
        r_eventid = event.get("r_eventid")

        if r_eventid and r_eventid != "0":
            recovery_event_ids.append(r_eventid)

    if not recovery_event_ids:
        return {}

    params = {
        "output": [
            "eventid",
            "clock",
            "name",
            "value"
        ],
        "eventids": recovery_event_ids
    }

    recovery_events = zabbix_api_request(
        api_url=api_url,
        method="event.get",
        params=params,
        auth_token=auth_token,
        request_id=3
    )

    recovery_map = {}

    for recovery_event in recovery_events:
        recovery_map[recovery_event.get("eventid")] = recovery_event

    return recovery_map

#====================================================================================================
# Create Report Lines
#====================================================================================================

def create_report_lines(zabbix_url, hours, time_from, time_till, events, recovery_map):

    report_lines = []
    report_lines.append("#" * 100)
    report_lines.append("#" + "ZABBIX PROBLEMS HISTORY REPORT".center(98) + "#")
    report_lines.append("#" * 100)
    report_lines.append(f"Zabbix URL        : {zabbix_url}")
    report_lines.append(f"Compatibility     : Zabbix Server 5.0.4")
    report_lines.append(f"Report Type       : Trigger Problem Events")
    report_lines.append(f"Time Range        : Last {hours} hour(s)")
    report_lines.append(f"From              : {timestamp_to_datetime(time_from)}")
    report_lines.append(f"To                : {timestamp_to_datetime(time_till)}")
    report_lines.append(f"Total Problems    : {len(events)}")

    report_lines.append("=" * 100)
    report_lines.append("PROBLEM EVENTS".center(100))
    report_lines.append("=" * 100)

    if not events:
        report_lines.append("No problems found in the selected time range.")
        return report_lines

    for event in events:
        event_id = event.get("eventid", "")
        event_name = event.get("name", "")
        event_clock = int(event.get("clock", 0))
        severity = severity_to_name(event.get("severity", "0"))

        acknowledged = "Yes" if event.get("acknowledged") == "1" else "No"

        r_eventid = event.get("r_eventid", "0")

        if r_eventid and r_eventid != "0":
            problem_status = "Resolved"
            recovery_event = recovery_map.get(r_eventid, {})
            recovery_clock = int(recovery_event.get("clock", 0))
            recovery_time = timestamp_to_datetime(recovery_clock)
            duration = seconds_to_duration(recovery_clock - event_clock)
        else:
            problem_status = "Active"
            recovery_time = "N/A"
            duration = seconds_to_duration(int(time.time()) - event_clock)

        hosts = event.get("hosts", [])
        related_object = event.get("relatedObject", {})
        acknowledges = event.get("acknowledges", [])
        tags = event.get("tags", [])

        if hosts:
            host_name = hosts[0].get("host", "Unknown")
            visible_name = hosts[0].get("name", "Unknown")
            host_id = hosts[0].get("hostid", "Unknown")
        else:
            host_name = "Unknown"
            visible_name = "Unknown"
            host_id = "Unknown"

        trigger_id = related_object.get("triggerid", event.get("objectid", "Unknown"))
        trigger_description = related_object.get("description", "Unknown")
        trigger_expression = related_object.get("expression", "Unknown")

        report_lines.append("-" * 100)
        report_lines.append(f"Event ID          : {event_id}")
        report_lines.append(f"Problem Name      : {event_name}")
        report_lines.append(f"Problem Status    : {problem_status}")
        report_lines.append(f"Severity          : {severity}")
        report_lines.append(f"Acknowledged      : {acknowledged}")
        report_lines.append(f"Host ID           : {host_id}")
        report_lines.append(f"Hostname          : {host_name}")
        report_lines.append(f"Visible Name      : {visible_name}")
        report_lines.append(f"Trigger ID        : {trigger_id}")
        report_lines.append(f"Trigger Name      : {trigger_description}")
        report_lines.append(f"Trigger Expression: {trigger_expression}")
        report_lines.append(f"Problem Time      : {timestamp_to_datetime(event_clock)}")
        report_lines.append(f"Recovery Event ID : {r_eventid}")
        report_lines.append(f"Recovery Time     : {recovery_time}")
        report_lines.append(f"Duration          : {duration}")

        if tags:
            report_lines.append("Tags              :")

            for tag in tags:
                tag_name = tag.get("tag", "")
                tag_value = tag.get("value", "")
                report_lines.append(f"  - {tag_name}: {tag_value}")

        if acknowledges:
            report_lines.append("Acknowledgements  :")

            for ack in acknowledges:
                ack_time = timestamp_to_datetime(ack.get("clock"))
                ack_message = ack.get("message", "")
                report_lines.append(f"  - Time    : {ack_time}")
                report_lines.append(f"    User ID : {ack.get('userid', '')}")
                report_lines.append(f"    Message : {ack_message}")
        else:
            report_lines.append("Acknowledgements  : None")

    report_lines.append("=" * 100)
    report_lines.append("END OF REPORT".center(100))
    report_lines.append("=" * 100)

    return report_lines

#====================================================================================================
# Save Report to TXT File
#====================================================================================================

def save_report_to_file(report_lines, output_file):        # Save report to TXT file.
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(report_lines))

    except OSError as error:
        print(f"[ERROR] Could not write report file: {error}")
        sys.exit(1)

#====================================================================================================
# Print Short Summary
#====================================================================================================

def print_short_summary(events):

    active_count = 0
    resolved_count = 0

    for event in events:
        r_eventid = event.get("r_eventid", "0")

        if r_eventid and r_eventid != "0":
            resolved_count += 1
        else:
            active_count += 1

    print("")
    print("=" * 100)
    print("ZABBIX PROBLEMS SUMMARY".center(100))
    print("=" * 100)
    print(f"Total Problems   : {len(events)}")
    print(f"Active Problems  : {active_count}")
    print(f"Resolved Problems: {resolved_count}")
    print("=" * 100)

#====================================================================================================
# Main Function
#====================================================================================================

def main():

    print("[+] Zabbix API Problems History Collector")
    print("[+] Compatible with Zabbix Server 5.0.4\n")

    zabbix_url = input("Enter Zabbix URL, example http://192.168.0.1/zabbix: ")
    username = input("Enter Zabbix username: ")
    password = getpass.getpass("Enter Zabbix password: ")

    hours_input = input("Enter time range in hours, default 24: ").strip()

    if hours_input == "":
        hours = 24
    else:
        try:
            hours = float(hours_input)
        except ValueError:
            print("[ERROR] Invalid time range. Please enter a number like 24, 12, 6, or 1.")
            sys.exit(1)

    if hours <= 0:
        print("[ERROR] Time range must be greater than 0.")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"Zabbix_Problems_Last_{hours}_Hours_{timestamp}.txt"

    api_url = normalize_zabbix_url(zabbix_url)

    print("\n[+] Connecting to Zabbix API...")

    auth_token = zabbix_login(api_url, username, password)

    print("[+] Authentication successful.")
    print(f"[+] Getting problem events from last {hours} hour(s)...")

    problem_events, time_from, time_till = get_problem_events(api_url, auth_token, hours)

    print("[+] Getting recovery events...")
    recovery_map = get_recovery_events(api_url, auth_token, problem_events)

    print("[+] Creating TXT report...")

    report_lines = create_report_lines(
        zabbix_url=zabbix_url,
        hours=hours,
        time_from=time_from,
        time_till=time_till,
        events=problem_events,
        recovery_map=recovery_map
    )

    save_report_to_file(report_lines, output_file)

    zabbix_logout(api_url, auth_token)

    print_short_summary(problem_events)

    print(f"\n[+] Report saved successfully: {output_file}")
    print("[+] Logged out from Zabbix API.")
    print("[+] Script finished successfully.")

#====================================================================================================
# Start Script
#====================================================================================================

if __name__ == "__main__":
    main()

#====================================================================================================
#End