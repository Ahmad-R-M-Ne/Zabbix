####################################################################################################
# Name: Zabbix _ Get All Templates                                                                 #
# Job: Export all Zabbix templates using Zabbix API and save them as import-ready files.           #
#  - Compatible with Zabbix Version 5.0.4                                                          #
#  - configuration.export                                                                          #
#   Output:                                                                                        #
#    1. One all-in-one XML file containing all templates                                           #
#    2. One XML file per template                                                                  #
#    3. One manifest TXT file                                                                      #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-06-30                                                                                 #
####################################################################################################

import requests
import json
import getpass
import sys
import os
import re
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
            timeout=120
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
# Create Safe File Name
#====================================================================================================

def make_safe_filename(name):
    """
    Convert template name to a safe filename.

    Example:
        Template Net Cisco IOS by SNMP
    becomes:
        Template_Net_Cisco_IOS_by_SNMP
    """
    name = name.strip()

    # Replace invalid Windows/Linux filename characters with underscore
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)

    # Replace spaces with underscore
    name = re.sub(r"\s+", "_", name)

    # Remove duplicate underscores
    name = re.sub(r"_+", "_", name)

    # Limit filename length
    return name[:150]

#====================================================================================================
# Prepare Output Directories
#====================================================================================================

def prepare_output_directories(base_directory):            # Create main output directory and subdirectory for individual template exports.

    individual_directory = os.path.join(base_directory, "Individual_Templates")

    try:
        os.makedirs(base_directory, exist_ok=True)
        os.makedirs(individual_directory, exist_ok=True)

    except OSError as error:
        print(f"[ERROR] Could not create output directory: {error}")
        sys.exit(1)

    return individual_directory

#====================================================================================================
# Get All Templates
#====================================================================================================

def get_all_templates(api_url, auth_token):
    """
    Get all templates from Zabbix.
    We only need template IDs for configuration.export,
    but we also collect host/name/groups for the manifest file.
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
# Export Templates
#====================================================================================================

def export_templates(api_url, auth_token, template_ids, export_format="xml"):
    """
    Export one or more templates.
    Zabbix 5.0.4 supported export formats:
      - xml
      - json
    For migration/import usage, XML is recommended.
    """

    params = {
        "options": {
            "templates": template_ids
        },
        "format": export_format
    }

    exported_data = zabbix_api_request(
        api_url=api_url,
        method="configuration.export",
        params=params,
        auth_token=auth_token,
        request_id=3
    )

    return exported_data

#====================================================================================================
# Save Text File
#====================================================================================================

def save_text_file(file_path, content):
    """
    Save text content to file.
    """

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

    except OSError as error:
        print(f"[ERROR] Could not write file {file_path}: {error}")
        sys.exit(1)

#====================================================================================================
# Create Manifest File
#====================================================================================================

def create_manifest(zabbix_url, templates, exported_files, failed_exports):
    """
    Create a manifest TXT file for documentation.
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []

    lines.append("#" * 100)
    lines.append("#" + "ZABBIX TEMPLATES EXPORT MANIFEST".center(98) + "#")
    lines.append("#" * 100)
    lines.append(f"Report Date           : {now}")
    lines.append(f"Zabbix URL            : {zabbix_url}")
    lines.append(f"Compatibility         : Zabbix Server 5.0.4")
    lines.append(f"Export Method         : configuration.export")
    lines.append(f"Export Format         : XML")
    lines.append(f"Total Templates       : {len(templates)}")
    lines.append(f"Successful Exports    : {len(exported_files)}")
    lines.append(f"Failed Exports        : {len(failed_exports)}")
    lines.append("=" * 100)
    lines.append("EXPORTED TEMPLATES".center(100))
    lines.append("=" * 100)

    for template in templates:
        template_id = template.get("templateid", "")
        template_host = template.get("host", "")
        template_name = template.get("name", "")
        description = template.get("description", "")

        groups = template.get("groups", [])
        parent_templates = template.get("parentTemplates", [])

        group_names = [group.get("name", "") for group in groups if group.get("name")]
        parent_names = [parent.get("name", "") for parent in parent_templates if parent.get("name")]

        exported_file = exported_files.get(template_id, "FAILED / NOT EXPORTED")

        lines.append("-" * 100)
        lines.append(f"Template ID       : {template_id}")
        lines.append(f"Template Host     : {template_host}")
        lines.append(f"Template Name     : {template_name}")
        lines.append(f"Groups            : {', '.join(group_names) if group_names else 'None'}")
        lines.append(f"Parent Templates  : {', '.join(parent_names) if parent_names else 'None'}")
        lines.append(f"Export File       : {exported_file}")
        lines.append(f"Description       : {description}")

    if failed_exports:
        lines.append("=" * 100)
        lines.append("FAILED EXPORTS".center(100))
        lines.append("=" * 100)
        lines.append("")

        for item in failed_exports:
            lines.append(f"Template ID   : {item.get('templateid')}")
            lines.append(f"Template Name : {item.get('name')}")
            lines.append(f"Error         : {item.get('error')}")
            lines.append("-" * 100)

    lines.append("")
    lines.append("=" * 100)
    lines.append("END OF MANIFEST".center(100))
    lines.append("=" * 100)

    return "\n".join(lines)

#====================================================================================================
# Export All Templates as One File
#====================================================================================================

def export_all_templates_single_file(api_url, auth_token, templates, base_directory):
    """
    Export all templates into one XML file.
    This file is the best file for importing into another Zabbix server,
    because all template relationships are exported together.
    """

    template_ids = [template.get("templateid") for template in templates]

    print("[+] Exporting all templates into one import-ready XML file...")

    exported_data = export_templates(
        api_url=api_url,
        auth_token=auth_token,
        template_ids=template_ids,
        export_format="xml"
    )

    all_in_one_file = os.path.join(
        base_directory,
        "Zabbix_All_Templates_Import_Ready.xml"
    )

    save_text_file(all_in_one_file, exported_data)

    return all_in_one_file

#====================================================================================================
# Export Each Template Separately
#====================================================================================================

def export_each_template(api_url, auth_token, templates, individual_directory):
    """
    Export each template into a separate XML file.
    Important:
        Individual template files are useful for backup and selective import.
        But if a template depends on another linked template, import may require
        importing the parent/base template first.
    """

    exported_files = {}
    failed_exports = []

    total = len(templates)

    for index, template in enumerate(templates, start=1):
        template_id = template.get("templateid", "")
        template_host = template.get("host", "")
        template_name = template.get("name", template_host)

        print(f"[+] Exporting template {index}/{total}: {template_name}")

        safe_name = make_safe_filename(template_name or template_host)

        file_name = f"{template_id}_{safe_name}.xml"
        file_path = os.path.join(individual_directory, file_name)

        try:
            exported_data = export_templates(
                api_url=api_url,
                auth_token=auth_token,
                template_ids=[template_id],
                export_format="xml"
            )

            save_text_file(file_path, exported_data)
            exported_files[template_id] = file_path

        except SystemExit:
            raise

        except Exception as error:
            failed_exports.append({
                "templateid": template_id,
                "name": template_name,
                "error": str(error)
            })

    return exported_files, failed_exports

#====================================================================================================
# Print Final Summary
#====================================================================================================

def print_summary(base_directory, all_in_one_file, templates, exported_files, failed_exports):

    print("=" * 100)
    print("ZABBIX TEMPLATE EXPORT SUMMARY".center(100))
    print("=" * 100)
    print(f"Output Directory       : {base_directory}")
    print(f"All-in-One Import File : {all_in_one_file}")
    print(f"Total Templates        : {len(templates)}")
    print(f"Individual Exported    : {len(exported_files)}")
    print(f"Failed Exports         : {len(failed_exports)}")
    print("=" * 100)

#====================================================================================================
# Main Function
#====================================================================================================

def main():

    print("[+] Zabbix API All Templates Exporter")
    print("[+] Compatible with Zabbix Server 5.0.4")
    print("[+] Export format: XML")
    print("[+] Files will be ready for import into another Zabbix server.\n")

    zabbix_url = input("Enter Zabbix URL, example http://192.168.0.1/zabbix: ")
    username = input("Enter Zabbix username: ")
    password = getpass.getpass("Enter Zabbix password: ")

    output_dir_input = input("Enter output directory name, default: Zabbix_Template_Exports: ").strip()

    if output_dir_input == "":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_directory = f"Zabbix_Template_Exports_{timestamp}"
    else:
        base_directory = output_dir_input

    individual_directory = prepare_output_directories(base_directory)

    api_url = normalize_zabbix_url(zabbix_url)

    print("\n[+] Connecting to Zabbix API...")

    auth_token = zabbix_login(api_url, username, password)

    print("[+] Authentication successful.")
    print("[+] Getting all templates...")

    templates = get_all_templates(api_url, auth_token)

    if not templates:
        print("[!] No templates found.")
        zabbix_logout(api_url, auth_token)
        sys.exit(0)

    print(f"[+] Total templates found: {len(templates)}")

    all_in_one_file = export_all_templates_single_file(
        api_url=api_url,
        auth_token=auth_token,
        templates=templates,
        base_directory=base_directory
    )

    print("[+] Exporting individual template files...")

    exported_files, failed_exports = export_each_template(
        api_url=api_url,
        auth_token=auth_token,
        templates=templates,
        individual_directory=individual_directory
    )

    print("[+] Creating export manifest...")

    manifest_content = create_manifest(
        zabbix_url=zabbix_url,
        templates=templates,
        exported_files=exported_files,
        failed_exports=failed_exports
    )

    manifest_file = os.path.join(base_directory, "Zabbix_Template_Export_Manifest.txt")
    save_text_file(manifest_file, manifest_content)

    zabbix_logout(api_url, auth_token)

    print_summary(
        base_directory=base_directory,
        all_in_one_file=all_in_one_file,
        templates=templates,
        exported_files=exported_files,
        failed_exports=failed_exports
    )

    print("\n[+] Manifest saved successfully:")
    print(f"    {manifest_file}")

    print("\n[+] Logged out from Zabbix API.")
    print("[+] Script finished successfully.")

#====================================================================================================
# Start Script
#====================================================================================================

if __name__ == "__main__":
    main()

#====================================================================================================
#End

