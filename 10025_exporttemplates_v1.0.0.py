####################################################################################################
# Name: Zabbix _ Export Templates                                                                  #
# Job: This Script connects to the Zabbix-Server and Export All The Valid Templates.               #
# Author: Ahmad Mojahed                                                                            #
# Date: 2025-12-18                                                                                 #
####################################################################################################

from zabbix_api import ZabbixAPI
import os

#====================================================================================================
# ZABBIX SERVER CONFIGURATION
#====================================================================================================
ZABBIX_SERVER = ""
ZABBIX_USER = ""
ZABBIX_PASSWORD = ""

#====================================================================================================
# EXPORT SETTINGS
#====================================================================================================
EXPORT_FORMAT = "xml"        # Supported by API: "xml" or "json"
EXPORT_ALL_TEMPLATES = True  # Set False to export only selected templates

TEMPLATE_NAMES = [
    # "Template Linux by Zabbix agent",
    # "Template Cisco IOS SNMP"
]

OUTPUT_DIR = "exported_templates"

#====================================================================================================
# CONNECT TO ZABBIX API
#====================================================================================================
zapi = ZabbixAPI(ZABBIX_SERVER)
zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)

print(f"Connected to Zabbix API at {ZABBIX_SERVER}")

os.makedirs(OUTPUT_DIR, exist_ok=True)

#====================================================================================================
# FETCH TEMPLATES
#====================================================================================================
if EXPORT_ALL_TEMPLATES:
    templates = zapi.template.get({
        "output": ["templateid", "name"]
    })
else:
    templates = zapi.template.get({
        "output": ["templateid", "name"],
        "filter": {"name": TEMPLATE_NAMES}
    })

if not templates:
    print("No templates found. Exiting.")
    zapi.logout()
    exit(1)

print(f"Templates to export: {len(templates)}\n")

#====================================================================================================
# EXPORT TEMPLATES (ONE FILE PER TEMPLATE)
#====================================================================================================
for tpl in templates:
    tpl_id = tpl["templateid"]
    tpl_name = tpl["name"]

    # Normalize filename (filesystem-safe)
    safe_name = (
        tpl_name
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    print(f"Exporting template: {tpl_name}")

    export_data = zapi.configuration.export({
        "format": EXPORT_FORMAT,
        "options": {
            "templates": [tpl_id]
        }
    })

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{safe_name}.{EXPORT_FORMAT}"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(export_data)

    print(f"✔ Saved: {output_file}\n")

#====================================================================================================
# CLEANUP
#====================================================================================================
zapi.logout()
print("✔ All templates exported successfully.")

# ====================================================================================================
# END
