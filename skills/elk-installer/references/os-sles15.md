# SUSE Linux Enterprise Server 15

## 更新系統
```
zypper refresh
zypper update -y
```

## 安裝前置套件
```
zypper install -y curl
```

## 加入 Elastic 套件庫（8.x）
```
rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
zypper addrepo -f https://artifacts.elastic.co/packages/8.x/yum elastic-8.x
zypper refresh
```

## 安裝套件
```
zypper install -y elasticsearch logstash kibana
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
