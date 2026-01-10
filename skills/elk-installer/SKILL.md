---
name: elk-installer
description: Install and configure the Elastic Stack (Elasticsearch, Logstash, Kibana) on remote Linux servers via bundled Python SSH installer scripts, including OS updates, repo setup, configuration, service startup, testing, and reporting. Use when a user provides production server SSH access and wants automated ELK/Elastic Stack installation on RHEL 9+, Oracle Linux 9+, SLES 15+, Debian 12+, or Photon OS 5+.
---

# ELK Installer

## Overview
Install, configure, and validate Elasticsearch, Logstash, and Kibana on a remote Linux host by running the bundled Python SSH installer scripts. Run commands from the agent machine; do not install locally.

## Supported Platforms
- Red Hat Enterprise Linux 9+
- Oracle Linux 9+
- SUSE Linux Enterprise Server 15+
- Debian Linux 12+
- Photon OS 5+

## Required Inputs
Collect SSH connection info before any changes:

- HostAddr: address or IP
- HostPort: SSH port
- HostUser: login user
- HostPass: login password

Collect configuration choices when not provided:
- Elastic major version (default 8)
- Node mode (single or multi)
- Bind address for Elasticsearch and Kibana
- JVM heap size (default 2g)
- Whether to open firewall ports 9200, 5601, 5044
- Seed hosts and initial masters for multi-node

Example prompt:

```
Please provide SSH access details:
HostAddr:
HostPort:
HostUser:
HostPass:
```

## Workflow
### 1. Install prerequisites on the agent machine
- Install Python dependencies for the SSH installer:
  - `python3 -m pip install -r scripts/requirements.txt`

### 2. Run the SSH installer (preferred)
- Run `python3 scripts/main.py` to launch interactive prompts, or pass flags directly.
- Confirm the configuration summary before applying changes.
- Require root or passwordless sudo on the target host.
- For multi-node, run the script once per node with the same seed host and initial master values.

Example command:
```
python3 scripts/main.py \
  --host 10.0.0.10 \
  --user root \
  --open-firewall
```

### 3. Report results
- Capture the output summary from the script:
  - Elasticsearch URL
  - Kibana URL
  - Generated elastic password
- Remind the user to store the password securely.
- If firewall rules are skipped for Photon OS, call it out explicitly.

### 4. Fallback (only if scripts are blocked)
- Use the OS-specific references for manual steps:
  - `references/os-rhel9-oracle9.md`
  - `references/os-sles15.md`
  - `references/os-debian12.md`
  - `references/os-photon5.md`
- Use `references/elastic-config.md` for configuration templates.

## Troubleshooting Guide (quick)
- SSH failures: confirm network, credentials, and sudo access.
- Elasticsearch fails to start: check `journalctl -u elasticsearch` and config syntax.
- Kibana cannot connect: verify credentials, CA, and `elasticsearch.hosts`.
- Logstash pipeline errors: run config test and review `/var/log/logstash/logstash-plain.log`.

## Scripts
- `scripts/main.py` - CLI entrypoint for SSH-based installation
- `scripts/installer.py` - Orchestrates remote install steps
- `scripts/commands.py` - OS-specific command templates and configs
- `scripts/ssh_client.py` - SSH client wrapper
- `scripts/requirements.txt` - Python dependencies

## References
- `references/os-rhel9-oracle9.md`
- `references/os-sles15.md`
- `references/os-debian12.md`
- `references/os-photon5.md`
- `references/elastic-config.md`
