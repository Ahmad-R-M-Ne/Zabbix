####################################################################################################
# Name: Zabbix _ Collect Triggers                                                                  #
# Job: This Script Collects All the Existing Triggers from Zabbix Server.                          #
# Author: Ahmad Mojahed                                                                            #
# Date: 2026-02-06                                                                                 #
####################################################################################################

from zabbix_api import ZabbixAPI
import json
import os
from datetime import datetime

#====================================================================================================
# ZABBIX CONNECTION CONFIG
#====================================================================================================
ZABBIX_SERVER = "http://192.168.0.1/zabbix"
ZABBIX_USER = ""
ZABBIX_PASSWORD = ""

#====================================================================================================
# EXPORT CONFIG
#====================================================================================================
OUTPUT_DIR = "zabbix_exports"
OUTPUT_FILE = "zabbix_template_triggers_only.json"

BATCH_SIZE = 10000
API_TIMEOUT = 120

#====================================================================================================
# CONNECT TO ZABBIX
#====================================================================================================
zapi = ZabbixAPI(ZABBIX_SERVER, timeout=API_TIMEOUT)
zapi.login(ZABBIX_USER, ZABBIX_PASSWORD)

print(f"[+] Connected to Zabbix API at {ZABBIX_SERVER}")

os.makedirs(OUTPUT_DIR, exist_ok=True)

#====================================================================================================
# STEP 1 : GET ALL TEMPLATE IDS
#====================================================================================================
templates = zapi.template.get({
    "output": ["templateid", "name"]
})

template_ids = [t["templateid"] for t in templates]

print(f"[+] Found {len(template_ids)} templates")

#====================================================================================================
# STEP 2 : FETCH TRIGGERS FROM TEMPLATES ONLY (SAFE PAGINATION)
#====================================================================================================
all_triggers = []
offset = 0
seen_trigger_ids = set()

print("[*] Fetching triggers from templates only...")

while True:
    batch = zapi.trigger.get({
        "output": [
            "triggerid",
            "description",
            "expression",
            "recovery_expression",
            "priority",
            "status",
            "manual_close",
            "comments"
        ],
        "expandExpression": True,
        "templateids": template_ids,
        "sortfield": "triggerid",
        "sortorder": "ASC",
        "limit": BATCH_SIZE,
        "offset": offset
    })

    if not batch:
        break

    new_count = 0

    for t in batch:
        tid = t["triggerid"]
        if tid not in seen_trigger_ids:
            seen_trigger_ids.add(tid)
            all_triggers.append(t)
            new_count += 1

    print(f"[+] Collected {len(all_triggers)} unique template triggers so far...")

    # CORRECT TERMINATION CONDITION
    if len(batch) < BATCH_SIZE:
        break

    offset += BATCH_SIZE

print(f"[✔] Final template trigger count: {len(all_triggers)}")

#====================================================================================================
# NORMALIZE EXPORT DATA
#====================================================================================================
export_data = {
    "metadata": {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "zabbix_server": ZABBIX_SERVER,
        "total_template_triggers": len(all_triggers)
    },
    "triggers": []
}

for t in all_triggers:
    export_data["triggers"].append({
        "triggerid": t.get("triggerid"),
        "name": t.get("description"),
        "problem_expression": t.get("expression"),
        "recovery_expression": t.get("recovery_expression"),
        "severity": t.get("priority"),
        "status": "enabled" if t.get("status") == "0" else "disabled",
        "manual_close": "yes" if t.get("manual_close") == "1" else "no",
        "comments": t.get("comments")
    })

#====================================================================================================
# SAVE OUTPUT
#====================================================================================================
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(export_data, f, indent=2)

print(f"[✔] Export completed successfully")
print(f"[✔] File saved to: {output_path}")

zapi.logout()
print("[+] Disconnected from Zabbix API")

#====================================================================================================
#End