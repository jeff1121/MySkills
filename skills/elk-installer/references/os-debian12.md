# Debian 12

## 更新系統
```
apt-get update
apt-get -y upgrade
```

## 安裝前置套件
```
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
```

## 加入 Elastic 套件庫（8.x）
```
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /etc/apt/keyrings/elastic.gpg
chmod 0644 /etc/apt/keyrings/elastic.gpg

echo "deb [signed-by=/etc/apt/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" \
  > /etc/apt/sources.list.d/elastic-8.x.list

apt-get update
```

## 安裝套件
```
apt-get install -y elasticsearch logstash kibana
```

## 可選的防火牆連接埠
提示: 僅在使用者同意後才開放連接埠。
提示: 若設定不同埠號請替換。

```
if command -v ufw >/dev/null 2>&1; then
  ufw allow 9200/tcp
  ufw allow 5601/tcp
  ufw allow 5044/tcp
fi
```
