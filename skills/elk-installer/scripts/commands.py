"""
Command builders for remote ELK installation.
"""
import json
from typing import Optional


SUPPORTED_OS = {"rhel9", "sles15", "debian12", "photon5"}


def detect_os_family(os_id: str, version_id: str) -> str:
    """Map /etc/os-release values to a supported OS family."""
    version_major = _parse_version_major(version_id)
    os_id = os_id.lower()

    if os_id in {"rhel", "ol", "rocky", "almalinux"} and version_major >= 9:
        return "rhel9"
    if os_id in {"sles", "suse"} and version_major >= 15:
        return "sles15"
    if os_id == "debian" and version_major >= 12:
        return "debian12"
    if os_id == "photon" and version_major >= 5:
        return "photon5"

    raise ValueError(f"unsupported OS: {os_id} {version_id}")


def build_update_script(os_family: str) -> str:
    if os_family == "rhel9":
        return """set -e
dnf -y update"""
    if os_family == "sles15":
        return """set -e
zypper refresh
zypper update -y"""
    if os_family == "debian12":
        return """set -e
apt-get update
apt-get -y upgrade"""
    if os_family == "photon5":
        return """set -e
tdnf -y update"""
    raise ValueError(f"unsupported OS family: {os_family}")


def build_prereq_script(os_family: str) -> str:
    if os_family == "rhel9":
        return """set -e
dnf -y install curl gnupg2"""
    if os_family == "sles15":
        return """set -e
zypper install -y curl"""
    if os_family == "debian12":
        return """set -e
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings"""
    if os_family == "photon5":
        return """set -e
tdnf -y install curl ca-certificates"""
    raise ValueError(f"unsupported OS family: {os_family}")


def build_repo_script(os_family: str, elastic_major: str) -> str:
    repo_version = f"{elastic_major}.x"
    if os_family == "rhel9":
        return f"""set -e
rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

cat <<'REPO' > /etc/yum.repos.d/elastic-{repo_version}.repo
[elastic-{repo_version}]
name=Elastic repository for {repo_version} packages
baseurl=https://artifacts.elastic.co/packages/{repo_version}/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
REPO"""
    if os_family == "sles15":
        return f"""set -e
rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
zypper addrepo -f https://artifacts.elastic.co/packages/{repo_version}/yum elastic-{repo_version}
zypper refresh"""
    if os_family == "debian12":
        return f"""set -e
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | \
  gpg --dearmor -o /etc/apt/keyrings/elastic.gpg
chmod 0644 /etc/apt/keyrings/elastic.gpg

cat <<'REPO' > /etc/apt/sources.list.d/elastic-{repo_version}.list
deb [signed-by=/etc/apt/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/{repo_version}/apt stable main
REPO

apt-get update"""
    if os_family == "photon5":
        return f"""set -e
rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

cat <<'REPO' > /etc/yum.repos.d/elastic-{repo_version}.repo
[elastic-{repo_version}]
name=Elastic repository for {repo_version} packages
baseurl=https://artifacts.elastic.co/packages/{repo_version}/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
REPO"""
    raise ValueError(f"unsupported OS family: {os_family}")


def build_install_packages_script(os_family: str) -> str:
    if os_family == "rhel9":
        return """set -e
dnf -y install elasticsearch logstash kibana"""
    if os_family == "sles15":
        return """set -e
zypper install -y elasticsearch logstash kibana"""
    if os_family == "debian12":
        return """set -e
apt-get install -y elasticsearch logstash kibana"""
    if os_family == "photon5":
        return """set -e
tdnf -y install elasticsearch logstash kibana"""
    raise ValueError(f"unsupported OS family: {os_family}")


def build_firewall_script(
    os_family: str,
    http_port: int,
    kibana_port: int,
    logstash_port: int = 5044,
    fleet_server_port: int = 8220,
) -> Optional[str]:
    if os_family in {"rhel9", "sles15"}:
        return f"""set -e
if systemctl is-active --quiet firewalld; then
  firewall-cmd --add-port={http_port}/tcp --permanent
  firewall-cmd --add-port={kibana_port}/tcp --permanent
  firewall-cmd --add-port={logstash_port}/tcp --permanent
  firewall-cmd --add-port={fleet_server_port}/tcp --permanent
  firewall-cmd --reload
fi"""
    if os_family == "debian12":
        return f"""set -e
if command -v ufw >/dev/null 2>&1; then
  ufw allow {http_port}/tcp
  ufw allow {kibana_port}/tcp
  ufw allow {logstash_port}/tcp
  ufw allow {fleet_server_port}/tcp
fi"""
    if os_family == "photon5":
        return None
    raise ValueError(f"unsupported OS family: {os_family}")


def build_elasticsearch_config_script(
    cluster_name: str,
    bind_host: str,
    http_port: int,
    elastic_major: str,
    node_mode: str,
    seed_hosts: Optional[list[str]],
    initial_masters: Optional[list[str]],
) -> str:
    lines = [
        f"cluster.name: {cluster_name}",
        "node.name: ${HOSTNAME}",
        "path.data: /var/lib/elasticsearch",
        "path.logs: /var/log/elasticsearch",
        f"network.host: {bind_host}",
        f"http.port: {http_port}",
    ]
    if node_mode == "single":
        lines.append("discovery.type: single-node")
    else:
        if seed_hosts:
            lines.append(f"discovery.seed_hosts: {json.dumps(seed_hosts)}")
        if initial_masters:
            lines.append(
                f"cluster.initial_master_nodes: {json.dumps(initial_masters)}"
            )
    if _parse_version_major(elastic_major) >= 8:
        lines.extend(
            [
                "xpack.security.enabled: true",
                "xpack.security.enrollment.enabled: true",
                "xpack.security.http.ssl:",
                "  enabled: true",
                "  keystore.path: certs/http.p12",
                "xpack.security.transport.ssl:",
                "  enabled: true",
                "  verification_mode: certificate",
                "  keystore.path: certs/transport.p12",
                "  truststore.path: certs/transport.p12",
            ]
        )
    content = "\n".join(lines) + "\n"
    return _build_here_doc("/etc/elasticsearch/elasticsearch.yml", content)


def build_jvm_options_script(heap_size: str) -> str:
    content = f"-Xms{heap_size}\n-Xmx{heap_size}\n"
    return _build_here_doc("/etc/elasticsearch/jvm.options.d/heap.options", content)


def build_kibana_config_script(
    kibana_host: str,
    kibana_port: int,
    elasticsearch_host: str,
    elasticsearch_port: int,
    elastic_major: str,
    elastic_password: Optional[str],
    service_token: Optional[str],
    fleet_server_host: str,
    fleet_server_port: int,
) -> str:
    es_host = _resolve_local_host(elasticsearch_host)
    elastic_hosts = json.dumps([f"https://{es_host}:{elasticsearch_port}"])
    fleet_server_hosts = json.dumps(
        [f"https://{fleet_server_host}:{fleet_server_port}"]
    )
    if _parse_version_major(elastic_major) >= 8:
        if not service_token:
            raise ValueError("service_token is required for Elastic 8+")
        token_value = json.dumps(service_token)
        content = (
            f"server.host: {json.dumps(kibana_host)}\n"
            f"server.port: {kibana_port}\n"
            f"elasticsearch.hosts: {elastic_hosts}\n"
            f"elasticsearch.serviceAccountToken: {token_value}\n"
            "elasticsearch.ssl.certificateAuthorities: [\"/etc/kibana/certs/http_ca.crt\"]\n"
            f"xpack.fleet.agents.fleet_server.hosts: {fleet_server_hosts}\n"
        )
    else:
        if not elastic_password:
            raise ValueError("elastic_password is required for Elastic < 8")
        password_value = json.dumps(elastic_password)
        content = (
            f"server.host: {json.dumps(kibana_host)}\n"
            f"server.port: {kibana_port}\n"
            f"elasticsearch.hosts: {elastic_hosts}\n"
            "elasticsearch.username: \"elastic\"\n"
            f"elasticsearch.password: {password_value}\n"
            "elasticsearch.ssl.certificateAuthorities: [\"/etc/kibana/certs/http_ca.crt\"]\n"
            f"xpack.fleet.agents.fleet_server.hosts: {fleet_server_hosts}\n"
        )
    return _build_here_doc("/etc/kibana/kibana.yml", content)


def build_kibana_encryption_keys_script() -> str:
    return """set -e
KEY_FILE=/etc/kibana/kibana-encryption-keys.yml
if [ ! -f "$KEY_FILE" ]; then
  /usr/share/kibana/bin/kibana-encryption-keys generate -q > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
  chown kibana:kibana "$KEY_FILE"
fi
if ! grep -q '^xpack.encryptedSavedObjects.encryptionKey:' /etc/kibana/kibana.yml; then
  cat "$KEY_FILE" >> /etc/kibana/kibana.yml
fi"""


def build_kibana_fleet_outputs_script(
    elasticsearch_host: str,
    elasticsearch_port: int,
) -> str:
    return f"""set -e
FINGERPRINT=$(openssl x509 -fingerprint -sha256 -noout \\
  -in /etc/elasticsearch/certs/http_ca.crt | \\
  awk -F= '{{print $2}}' | tr -d ':' | tr 'A-F' 'a-f')
sed -i 's/^xpack.fleet.agents.elasticsearch.hosts/#xpack.fleet.agents.elasticsearch.hosts/' \\
  /etc/kibana/kibana.yml
if ! grep -q '^xpack.fleet.outputs:' /etc/kibana/kibana.yml; then
  cat <<EOF >> /etc/kibana/kibana.yml
xpack.fleet.outputs:
  - id: fleet-default-output
    name: default
    type: elasticsearch
    hosts: ["https://{elasticsearch_host}:{elasticsearch_port}"]
    is_default: true
    is_default_monitoring: true
    ca_trusted_fingerprint: "${{FINGERPRINT}}"
EOF
fi"""


def build_logstash_pipeline_script(
    elasticsearch_host: str,
    elasticsearch_port: int,
    logstash_port: int,
) -> str:
    es_host = _resolve_local_host(elasticsearch_host)
    elastic_url = f"https://{es_host}:{elasticsearch_port}"
    content = (
        "input {\n"
        "  beats {\n"
        f"    port => {logstash_port}\n"
        "  }\n"
        "}\n\n"
        "output {\n"
        "  elasticsearch {\n"
        f"    hosts => [\"{elastic_url}\"]\n"
        "    user => \"elastic\"\n"
        "    password => \"${ES_PWD}\"\n"
        "    ssl_certificate_authorities => [\"/etc/logstash/certs/http_ca.crt\"]\n"
        "  }\n"
        "}\n"
    )
    return _build_here_doc("/etc/logstash/conf.d/elastic.conf", content)


def build_kibana_ca_script() -> str:
    return """set -e
mkdir -p /etc/kibana/certs
cp /etc/elasticsearch/certs/http_ca.crt /etc/kibana/certs/
chown -R kibana:kibana /etc/kibana/certs"""


def build_logstash_ca_script() -> str:
    return """set -e
mkdir -p /etc/logstash/certs
cp /etc/elasticsearch/certs/http_ca.crt /etc/logstash/certs/
chown -R logstash:logstash /etc/logstash/certs"""


def build_logstash_keystore_script(elastic_password: str) -> str:
    secret_block = _build_secret_variable("ES_PWD_VALUE", elastic_password)
    return f"""set -e
{secret_block}
if [ ! -f /etc/logstash/logstash.keystore ]; then
  printf 'y\\n' | /usr/share/logstash/bin/logstash-keystore create --path.settings /etc/logstash
fi
/usr/share/logstash/bin/logstash-keystore remove ES_PWD --path.settings /etc/logstash || true
printf '%s' \"${{ES_PWD_VALUE}}\" | \
  /usr/share/logstash/bin/logstash-keystore add ES_PWD --path.settings /etc/logstash --stdin
chown logstash:logstash /etc/logstash/logstash.keystore"""


def build_service_enable_script(service: str) -> str:
    return f"""set -e
systemctl enable {service}
systemctl restart {service}"""


def build_service_stop_script(service: str) -> str:
    return f"""set -e
if systemctl is-active --quiet {service}; then
  systemctl stop {service}
fi"""


def build_wait_for_service_script(service: str, wait_seconds: int) -> str:
    iterations = max(1, wait_seconds // 5)
    return f"""set -e
i=0
while [ $i -lt {iterations} ]; do
  if systemctl is-active --quiet {service}; then
    exit 0
  fi
  sleep 5
  i=$((i + 1))
done
systemctl status {service} --no-pager
exit 1"""


def build_elasticsearch_password_script() -> str:
    return """set -e
/usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic --batch"""


def build_elasticsearch_test_script(
    elasticsearch_host: str,
    elastic_password: str,
    http_port: int,
) -> str:
    es_host = _resolve_local_host(elasticsearch_host)
    secret_block = _build_secret_variable("ES_PWD_VALUE", elastic_password)
    return f"""set -e
{secret_block}
curl --cacert /etc/elasticsearch/certs/http_ca.crt \\
  -u \"elastic:${{ES_PWD_VALUE}}\" https://{es_host}:{http_port}"""


def build_kibana_test_script(kibana_host: str, kibana_port: int) -> str:
    test_host = _resolve_local_host(kibana_host)
    return f"""set -e
i=0
while [ $i -lt 30 ]; do
  if curl -fsI http://{test_host}:{kibana_port} >/dev/null; then
    exit 0
  fi
  sleep 5
  i=$((i + 1))
done
curl -I http://{test_host}:{kibana_port}
exit 1"""


def build_logstash_test_script() -> str:
    return """set -e
/usr/share/logstash/bin/logstash --path.settings /etc/logstash -t"""


def build_fleet_setup_script(
    kibana_host: str,
    kibana_port: int,
    elastic_password: str,
) -> str:
    test_host = _resolve_local_host(kibana_host)
    secret_block = _build_secret_variable("ES_PWD_VALUE", elastic_password)
    return f"""set -e
{secret_block}
KIBANA_URL="http://{test_host}:{kibana_port}"
ready=0
i=0
while [ $i -lt 30 ]; do
  if curl -fsI "${{KIBANA_URL}}/login" >/dev/null; then
    ready=1
    break
  fi
  sleep 5
  i=$((i + 1))
done
if [ $ready -ne 1 ]; then
  echo "Kibana not ready at ${{KIBANA_URL}}" >&2
  exit 1
fi
setup_response=$(curl -sS -u "elastic:${{ES_PWD_VALUE}}" -H 'kbn-xsrf: true' \\
  -X POST "${{KIBANA_URL}}/api/fleet/setup" -w 'HTTP_STATUS:%{{http_code}}')
setup_status="${{setup_response##*HTTP_STATUS:}}"
setup_body="${{setup_response%HTTP_STATUS:*}}"
if [ "$setup_status" -ge 300 ]; then
  echo "$setup_body" >&2
  exit 1
fi
response=$(curl -fsS -u "elastic:${{ES_PWD_VALUE}}" -H 'kbn-xsrf: true' \\
  "${{KIBANA_URL}}/api/fleet/agent_policies?perPage=200")
policy_id=$(echo "$response" | tr -d '\\n' | sed 's/}},{{/}}\\n{{/g' | \\
  awk '/"is_default_fleet_server":true/ {{match($0, /"id":"([^"]*)"/, m); if (m[1]) {{print m[1]; exit}}}}')
if [ -z "$policy_id" ]; then
  payload='{{"name":"fleet-server-policy","namespace":"default","description":"Fleet Server policy","is_default_fleet_server":true,"monitoring_enabled":["logs","metrics"]}}'
  create_response=$(curl -fsS -u "elastic:${{ES_PWD_VALUE}}" -H 'kbn-xsrf: true' \\
    -H 'content-type: application/json' -X POST "${{KIBANA_URL}}/api/fleet/agent_policies" \\
    -d "$payload")
  policy_id=$(echo "$create_response" | tr -d '\\n' | sed 's/}},{{/}}\\n{{/g' | \\
    awk 'match($0, /"id":"([^"]*)"/, m) {{if (m[1]) {{print m[1]; exit}}}}')
fi
if [ -z "$policy_id" ]; then
  echo "Failed to determine Fleet Server policy ID" >&2
  echo "$response" >&2
  exit 1
fi
echo "$policy_id"
"""


def build_fleet_service_token_script(token_name: str) -> str:
    return f"""set -e
export ES_PATH_CONF=/etc/elasticsearch
/usr/share/elasticsearch/bin/elasticsearch-service-tokens delete elastic/fleet-server {token_name} || true
/usr/share/elasticsearch/bin/elasticsearch-service-tokens create elastic/fleet-server {token_name}
chown root:elasticsearch /etc/elasticsearch/service_tokens
chmod 660 /etc/elasticsearch/service_tokens"""


def build_fleet_server_install_script(
    elasticsearch_host: str,
    elasticsearch_port: int,
    fleet_server_host: str,
    fleet_server_port: int,
    service_token: str,
    policy_id: str,
) -> str:
    es_host = _resolve_local_host(elasticsearch_host)
    secret_block = _build_secret_variable("FLEET_TOKEN_VALUE", service_token)
    return f"""set -e
{secret_block}
ES_VERSION=$(/usr/share/elasticsearch/bin/elasticsearch --version | \\
  awk -F'[ ,]+' '/^Version:/ {{print $2}}')
if [ -z "$ES_VERSION" ]; then
  echo "Unable to determine Elasticsearch version" >&2
  exit 1
fi
if systemctl is-active --quiet elastic-agent; then
  systemctl stop elastic-agent || true
fi
AGENT_UNINSTALL_BIN=""
if command -v elastic-agent >/dev/null 2>&1; then
  AGENT_UNINSTALL_BIN=$(command -v elastic-agent)
elif [ -x /usr/share/elastic-agent/bin/elastic-agent ]; then
  AGENT_UNINSTALL_BIN=/usr/share/elastic-agent/bin/elastic-agent
fi
if [ -n "$AGENT_UNINSTALL_BIN" ]; then
  "$AGENT_UNINSTALL_BIN" uninstall -f --skip-fleet-audit || true
fi
rm -f /usr/bin/elastic-agent
rm -rf /opt/Elastic/Agent
ARCH=$(uname -m)
case "$ARCH" in
  x86_64) PLATFORM=linux-x86_64 ;;
  aarch64) PLATFORM=linux-arm64 ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac
WORKDIR=$(mktemp -d)
TARBALL="elastic-agent-${{ES_VERSION}}-${{PLATFORM}}.tar.gz"
URL="https://artifacts.elastic.co/downloads/beats/elastic-agent/${{TARBALL}}"
curl -fsSL "$URL" -o "$WORKDIR/${{TARBALL}}"
tar -xzf "$WORKDIR/${{TARBALL}}" -C "$WORKDIR"
AGENT_DIR="$WORKDIR/elastic-agent-${{ES_VERSION}}-${{PLATFORM}}"
if [ ! -x "$AGENT_DIR/elastic-agent" ]; then
  echo "elastic-agent binary not found in $AGENT_DIR" >&2
  exit 1
fi
"$AGENT_DIR/elastic-agent" install --force \\
  --fleet-server-es=https://{es_host}:{elasticsearch_port} \\
  --fleet-server-service-token="${{FLEET_TOKEN_VALUE}}" \\
  --fleet-server-policy={policy_id} \\
  --fleet-server-host={fleet_server_host} \\
  --fleet-server-port={fleet_server_port} \\
  --fleet-server-es-ca=/etc/elasticsearch/certs/http_ca.crt \\
  --fleet-server-timeout=10m
"""


def build_fleet_server_test_script(
    fleet_server_host: str,
    fleet_server_port: int,
) -> str:
    test_host = _resolve_local_host(fleet_server_host)
    return f"""set -e
systemctl is-active --quiet elastic-agent
curl -fsS -k https://{test_host}:{fleet_server_port}/api/status >/dev/null"""


def _build_here_doc(path: str, content: str) -> str:
    return f"""set -e
cat <<'ELK_EOF' > {path}
{content}
ELK_EOF"""


def _build_secret_variable(name: str, value: str) -> str:
    return f"""{name}=$(cat <<'ELK_SECRET'
{value}
ELK_SECRET
)
"""


def _parse_version_major(version_id: str) -> int:
    try:
        return int(version_id.split(".")[0])
    except (ValueError, AttributeError, IndexError):
        return 0


def _resolve_local_host(host: str) -> str:
    if host in {"0.0.0.0", "::"}:
        return "127.0.0.1"
    return host
