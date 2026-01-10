# Photon OS 5

## Update OS
```
tdnf -y update
```

## Install prerequisites
```
tdnf -y install curl ca-certificates
```

## Add Elastic repo (8.x)
```
rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

cat <<'REPO' > /etc/yum.repos.d/elastic-8.x.repo
[elastic-8.x]
name=Elastic repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
REPO
```

## Install packages
```
tdnf -y install elasticsearch logstash kibana
```

## Optional firewall ports
Only open ports after user approval.

If iptables is in use, add rules for 9200, 5601, and 5044 as needed.
