![Zabbix Logo](assets/Zabbix_Logo_1.jpeg)
# 🤖 Zabbix Automation Scripts

## Python scripts to automate Zabbix monitoring tasks.

Using Python with the Zabbix API allows automation of monitoring operations through
JSON-RPC requests. The script first authenticates to the Zabbix server using `user.login`
and receives an API token.
After authentication, Python sends structured API calls such as `host.get`, `template.get`,
`event.get`, `usermacro.get` and `configuration.export`.
Host information can be collected with interfaces, templates, groups, macros, inventory,
SNMP parameters, and descriptions.
Templates should be queried directly to avoid duplicated inherited objects from monitored hosts.
Problems and historical events are collected through `event.get` using timestamp filters
such as the last 24 hours.
Macros can be collected from global, host, and template scopes, but sensitive values must be protected.
Templates can be exported with `configuration.export` into import-ready XML files for migration or backup.
All outputs should be saved into reports or export directories instead of printing large data in the terminal.
Finally, the script should logout using `user.logout` to invalidate the active API session.

![Zabbix Logo](assets/Zabbix_Logo_3.png)

## 🚀 Quick Start

```bash
git clone https://github.com/Ahmad-R-M-Ne/Zabbix.git
pip install -r requirements.txt
