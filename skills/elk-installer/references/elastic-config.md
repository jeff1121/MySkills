# Elastic Stack 組態備註

## Elasticsearch 基本設定（單節點）
檔案: `/etc/elasticsearch/elasticsearch.yml`

範例:
```
cluster.name: elk-cluster
node.name: ${HOSTNAME}
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
```
提示: 若更改 HTTP 連接埠，請同步更新 Kibana、Logstash 與測試指令。

## Elasticsearch heap 設定
檔案: `/etc/elasticsearch/jvm.options.d/heap.options`

範例:
```
-Xms2g
-Xmx2g
```

## 安全性（Elastic 8.x 預設）
- 正式環境請保留安全性為啟用。
- 啟動 Elasticsearch 後，設定既定密碼:
```
/usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic
```
- 需要時產生 Kibana 註冊權杖:
```
/usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana
```

## Kibana
檔案: `/etc/kibana/kibana.yml`

範例:
```
server.host: "0.0.0.0"
server.port: 5601
elasticsearch.hosts: ["https://localhost:9200"]
elasticsearch.username: "elastic"
elasticsearch.password: "set_this_value"
elasticsearch.ssl.certificateAuthorities: ["/etc/kibana/certs/http_ca.crt"]
```
提示: 若設定了不同的 Elasticsearch HTTP 連接埠，請替換 `9200`。

複製 CA 檔案:
```
mkdir -p /etc/kibana/certs
cp /etc/elasticsearch/certs/http_ca.crt /etc/kibana/certs/
chown -R kibana:kibana /etc/kibana/certs
```

## Logstash
Pipeline 目錄: `/etc/logstash/conf.d/`

輸出到 Elasticsearch 的範例:
```
output {
  elasticsearch {
    hosts => ["https://localhost:9200"]
    user => "elastic"
    password => "${ES_PWD}"
    cacert => "/etc/logstash/certs/http_ca.crt"
  }
}
```
提示: 若設定不同的 Elasticsearch HTTP 連接埠請替換 `9200`；若有變更 Beats 輸入埠，請同步更新 `5044`。

將密碼存入 Logstash keystore:
```
/usr/share/logstash/bin/logstash-keystore create
/usr/share/logstash/bin/logstash-keystore add ES_PWD
```

複製 CA 檔案:
```
mkdir -p /etc/logstash/certs
cp /etc/elasticsearch/certs/http_ca.crt /etc/logstash/certs/
chown -R logstash:logstash /etc/logstash/certs
```

## 服務啟動順序
```
systemctl enable --now elasticsearch
systemctl enable --now kibana
systemctl enable --now logstash
```

## 測試
Elasticsearch:
```
curl --cacert /etc/elasticsearch/certs/http_ca.crt -u elastic:PASSWORD https://localhost:9200
```

Kibana:
```
curl -I http://localhost:5601
```
提示: 若使用非預設連接埠，請替換對應的埠號。

Logstash 組態測試:
```
/usr/share/logstash/bin/logstash --path.settings /etc/logstash -t
```
