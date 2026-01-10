# RHEL 9 與 Oracle Linux 9

## 更新系統
```
dnf -y update
```

## 安裝前置套件
```
dnf -y install curl gnupg2
```

## 加入 Elastic 套件庫（8.x）
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

## 安裝套件
```
dnf -y install elasticsearch logstash kibana
```

## 可選的防火牆連接埠
提示: 僅在使用者同意後才開放連接埠。
提示: 若設定不同埠號請替換。

```
if systemctl is-active --quiet firewalld; then
  firewall-cmd --add-port=9200/tcp --permanent
  firewall-cmd --add-port=5601/tcp --permanent
  firewall-cmd --add-port=5044/tcp --permanent
  firewall-cmd --reload
fi
```
