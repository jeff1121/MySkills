# Debian 12

## Update OS
```
apt-get update
apt-get -y upgrade
```

## Install prerequisites
```
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
```

## Add Elastic repo (8.x)
```
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /etc/apt/keyrings/elastic.gpg
chmod 0644 /etc/apt/keyrings/elastic.gpg

echo "deb [signed-by=/etc/apt/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" \
  > /etc/apt/sources.list.d/elastic-8.x.list

apt-get update
```

## Install packages
```
apt-get install -y elasticsearch logstash kibana
```

## Optional firewall ports
Only open ports after user approval.

```
if command -v ufw >/dev/null 2>&1; then
  ufw allow 9200/tcp
  ufw allow 5601/tcp
  ufw allow 5044/tcp
fi
```
