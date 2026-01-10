# SUSE Linux Enterprise Server 15

## Update OS
```
zypper refresh
zypper update -y
```

## Install prerequisites
```
zypper install -y curl
```

## Add Elastic repo (8.x)
```
rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
zypper addrepo -f https://artifacts.elastic.co/packages/8.x/yum elastic-8.x
zypper refresh
```

## Install packages
```
zypper install -y elasticsearch logstash kibana
```

## Optional firewall ports
Only open ports after user approval.

```
if systemctl is-active --quiet firewalld; then
  firewall-cmd --add-port=9200/tcp --permanent
  firewall-cmd --add-port=5601/tcp --permanent
  firewall-cmd --add-port=5044/tcp --permanent
  firewall-cmd --reload
fi
```
