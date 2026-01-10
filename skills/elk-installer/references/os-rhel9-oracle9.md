# RHEL 9 and Oracle Linux 9

## Update OS
```
dnf -y update
```

## Install prerequisites
```
dnf -y install curl gnupg2
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
dnf -y install elasticsearch logstash kibana
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
