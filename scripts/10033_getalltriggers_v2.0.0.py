####################################################################################################
# Name: Zabbix _ Get All Triggers                                                                  #
# Job: Get all Zabbix triggers from templates only using Zabbix API.                               #
#      - Compatible with Zabbix Version 5.0.4                                                      #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-06-30                                                                                 #
####################################################################################################

import requests
import json
import getpass
import sys
from datetime import datetime

#====================================================================================================
# Script Behavior
#====================================================================================================

# True  = Skip inherited template triggers.
#         This avoids duplicates when one template is linked to another template.
# False = Include inherited template triggers too.
SKIP_INHERITED_TEMPLATE_TRIGGERS = True

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
            timeout=60
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
# Convert Trigger Severity to Name
#====================================================================================================

def severity_to_name(priority):

    severities = {
        "0": "Not classified",
        "1": "Information",
        "2": "Warning",
        "3": "Average",
        "4": "High",
        "5": "Disaster"
    }

    return severities.get(str(priority), "Unknown")

#====================================================================================================
# Convert Trigger Status to Name
#====================================================================================================

def trigger_status_to_name(status):

    statuses = {
        "0": "Enabled",
        "1": "Disabled"
    }

    return statuses.get(str(status), "Unknown")

#====================================================================================================
# Convert Trigger State to Name
#====================================================================================================

def trigger_state_to_name(state):

    states = {
        "0": "Normal",
        "1": "Unknown"
    }

    return states.get(str(state), "Unknown")

#====================================================================================================
# Convert Trigger Value to Name
#====================================================================================================

def trigger_value_to_name(value):

    values = {
        "0": "OK",
        "1": "PROBLEM"
    }

    return values.get(str(value), "Unknown")

#====================================================================================================
# Convert Recovery Mode to Name
#====================================================================================================

def recovery_mode_to_name(recovery_mode):

    modes = {
        "0": "Expression",
        "1": "Recovery expression",
        "2": "None"
    }

    return modes.get(str(recovery_mode), "Unknown")

#====================================================================================================
# Convert Manual Close to Name
#====================================================================================================

def manual_close_to_name(manual_close):

    values = {
        "0": "No",
        "1": "Yes"
    }

    return values.get(str(manual_close), "Unknown")

#====================================================================================================
# Get Templates and Their Triggers
#====================================================================================================

def get_templates_with_triggers(api_url, auth_token):
    """
    Get all templates and their triggers.
    Important:
        We use template.get, not host.get.
    This means:
        - Triggers are collected from templates.
        - Host-level inherited trigger duplicates are avoided.
    """
    params = {
        "output": [
            "templateid",
            "host",
            "name",
            "description"
        ],

        "selectGroups": [
            "groupid",
            "name"
        ],

        "selectParentTemplates": [
            "templateid",
            "host",
            "name"
        ],

        "selectTriggers": [
            "triggerid",
            "description",
            "expression",
            "recovery_expression",
            "recovery_mode",
            "priority",
            "status",
            "state",
            "value",
            "comments",
            "url",
            "type",
            "templateid",
            "manual_close"
        ],

        "sortfield": "host",
        "sortorder": "ASC"
    }

    templates = zabbix_api_request(
        api_url=api_url,
        method="template.get",
        params=params,
        auth_token=auth_token,
        request_id=2
    )

    return templates

#====================================================================================================
# Build Unique Trigger List
#====================================================================================================

def build_unique_template_trigger_list(templates):
    """
    Build a clean list of template triggers.
    Why de-duplication is needed:
        - Host trigger collection creates duplicates per host.
        - Template inheritance can also create inherited copies.
        - This function keeps trigger collection clean.
    Important field:
        trigger["templateid"]
    Meaning:
        templateid = 0
            Original trigger.
        templateid != 0
            Inherited trigger copy from another template.
    With SKIP_INHERITED_TEMPLATE_TRIGGERS=True:
        inherited copies are skipped.
    """
    unique_triggers = {}

    skipped_inherited_count = 0

    for template in templates:
        template_id = template.get("templateid", "")
        template_host = template.get("host", "")
        template_name = template.get("name", "")
        template_description = template.get("description", "")

        groups = template.get("groups", [])
        parent_templates = template.get("parentTemplates", [])
        triggers = template.get("triggers", [])

        group_names = []

        for group in groups:
            group_name = group.get("name", "")
            if group_name:
                group_names.append(group_name)

        parent_template_names = []

        for parent_template in parent_templates:
            parent_name = parent_template.get("name", "")
            if parent_name:
                parent_template_names.append(parent_name)

        for trigger in triggers:
            trigger_id = trigger.get("triggerid", "")

            if not trigger_id:
                continue

            parent_trigger_id = trigger.get("templateid", "0")

            # Skip inherited template trigger copies if enabled.
            if SKIP_INHERITED_TEMPLATE_TRIGGERS and parent_trigger_id != "0":
                skipped_inherited_count += 1
                continue

            # Extra safety: avoid duplicate trigger IDs.
            if trigger_id in unique_triggers:
                continue

            unique_triggers[trigger_id] = {
                "template_id": template_id,
                "template_host": template_host,
                "template_name": template_name,
                "template_description": template_description,
                "template_groups": group_names,
                "parent_templates": parent_template_names,
                "trigger": trigger
            }

    return unique_triggers, skipped_inherited_count

#====================================================================================================
# Create TXT Report Header
#====================================================================================================

def create_report_header(zabbix_url, total_templates, total_triggers, skipped_inherited_count):
    """
    Create Phoenix-style report header.
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []

    lines.append("#" * 100)
    lines.append("#" + "ZABBIX TEMPLATE TRIGGERS REPORT".center(98) + "#")
    lines.append("#" * 100)
    lines.append(f"Report Date                 : {now}")
    lines.append(f"Zabbix URL                  : {zabbix_url}")
    lines.append(f"Compatibility               : Zabbix Server 5.0.4")
    lines.append(f"Collection Method           : template.get + selectTriggers")
    lines.append(f"Collected From              : Templates only")
    lines.append(f"Host Trigger Collection     : Disabled")
    lines.append(f"Skip Inherited Triggers     : {SKIP_INHERITED_TEMPLATE_TRIGGERS}")
    lines.append(f"Total Templates             : {total_templates}")
    lines.append(f"Total Unique Triggers       : {total_triggers}")
    lines.append(f"Skipped Inherited Triggers  : {skipped_inherited_count}")
    lines.append("#" * 100)

    return lines

#====================================================================================================
# Add Triggers to Report
#====================================================================================================

def add_triggers_to_report(lines, unique_triggers):        # Add all collected template triggers to TXT report.

    lines.append("=" * 100)
    lines.append("TEMPLATE TRIGGERS".center(100))
    lines.append("=" * 100)
    lines.append("")

    if not unique_triggers:
        lines.append("No template triggers found.")
        return lines

    # Sort by template name, then severity, then trigger description.
    sorted_trigger_items = sorted(
        unique_triggers.values(),
        key=lambda item: (
            item.get("template_name", ""),
            item.get("trigger", {}).get("priority", "0"),
            item.get("trigger", {}).get("description", "")
        )
    )

    for item in sorted_trigger_items:
        trigger = item.get("trigger", {})

        template_groups = item.get("template_groups", [])
        parent_templates = item.get("parent_templates", [])

        lines.append("-" * 100)
        lines.append(f"Template ID          : {item.get('template_id', '')}")
        lines.append(f"Template Host        : {item.get('template_host', '')}")
        lines.append(f"Template Name        : {item.get('template_name', '')}")

        if template_groups:
            lines.append(f"Template Groups      : {', '.join(template_groups)}")
        else:
            lines.append("Template Groups      : None")

        if parent_templates:
            lines.append(f"Parent Templates     : {', '.join(parent_templates)}")
        else:
            lines.append("Parent Templates     : None")

        lines.append(f"Trigger ID           : {trigger.get('triggerid', '')}")
        lines.append(f"Parent Trigger ID    : {trigger.get('templateid', '0')}")
        lines.append(f"Trigger Name         : {trigger.get('description', '')}")
        lines.append(f"Severity             : {severity_to_name(trigger.get('priority'))}")
        lines.append(f"Status               : {trigger_status_to_name(trigger.get('status'))}")
        lines.append(f"State                : {trigger_state_to_name(trigger.get('state'))}")
        lines.append(f"Current Value        : {trigger_value_to_name(trigger.get('value'))}")
        lines.append(f"Multiple Events      : {'Yes' if trigger.get('type') == '1' else 'No'}")
        lines.append(f"Manual Close         : {manual_close_to_name(trigger.get('manual_close'))}")
        lines.append(f"Expression           : {trigger.get('expression', '')}")
        lines.append(f"Recovery Mode        : {recovery_mode_to_name(trigger.get('recovery_mode'))}")
        lines.append(f"Recovery Expression  : {trigger.get('recovery_expression', '')}")
        lines.append(f"URL                  : {trigger.get('url', '')}")
        lines.append(f"Comments             : {trigger.get('comments', '')}")
        lines.append("-" * 100)

    lines.append("=" * 100)
    lines.append("END OF REPORT".center(100))
    lines.append("=" * 100)

    return lines

#====================================================================================================
# Save Report to TXT File
#====================================================================================================

def save_report_to_file(lines, output_file):               # Save final report to TXT file.

    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

    except OSError as error:
        print(f"[ERROR] Could not write report file: {error}")
        sys.exit(1)

#====================================================================================================
# Print Short Summary
#====================================================================================================

def print_short_summary(total_templates, total_triggers, skipped_inherited_count, output_file):

    print("=" * 100)
    print("ZABBIX TEMPLATE TRIGGERS SUMMARY".center(100))
    print("=" * 100)
    print(f"Total Templates            : {total_templates}")
    print(f"Total Unique Triggers      : {total_triggers}")
    print(f"Skipped Inherited Triggers : {skipped_inherited_count}")
    print(f"Output File                : {output_file}")
    print("=" * 100)

#====================================================================================================
# Main Function
#====================================================================================================

def main():

    print("[+] Zabbix API Template Triggers Collector")
    print("[+] Compatible with Zabbix Server 5.0.4")
    print("[+] Collecting triggers from templates only, not hosts.\n")

    zabbix_url = input("Enter Zabbix URL, example http://192.168.0.1/zabbix: ")
    username = input("Enter Zabbix username: ")
    password = getpass.getpass("Enter Zabbix password: ")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"Zabbix_Template_Triggers_Report_{timestamp}.txt"

    api_url = normalize_zabbix_url(zabbix_url)

    print("\n[+] Connecting to Zabbix API...")

    auth_token = zabbix_login(api_url, username, password)

    print("[+] Authentication successful.")
    print("[+] Getting templates and template triggers...")

    templates = get_templates_with_triggers(api_url, auth_token)

    print("[+] Building unique trigger list...")

    unique_triggers, skipped_inherited_count = build_unique_template_trigger_list(templates)

    print("[+] Creating TXT report...")

    report_lines = create_report_header(
        zabbix_url=zabbix_url,
        total_templates=len(templates),
        total_triggers=len(unique_triggers),
        skipped_inherited_count=skipped_inherited_count
    )

    report_lines = add_triggers_to_report(report_lines, unique_triggers)

    save_report_to_file(report_lines, output_file)

    zabbix_logout(api_url, auth_token)

    print_short_summary(
        total_templates=len(templates),
        total_triggers=len(unique_triggers),
        skipped_inherited_count=skipped_inherited_count,
        output_file=output_file
    )

    print("\n[+] Logged out from Zabbix API.")
    print("[+] Script finished successfully.")

#====================================================================================================
# Start Script
#====================================================================================================

if __name__ == "__main__":
    main()

#====================================================================================================
#End