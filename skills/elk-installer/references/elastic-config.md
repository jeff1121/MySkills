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
xpack.fleet.agents.elasticsearch.hosts: ["https://localhost:9200"]
xpack.fleet.agents.fleet_server.hosts: ["https://FLEET_HOST:8220"]
```
提示: 若設定了不同的 Elasticsearch HTTP 連接埠，請替換 `9200`。

複製 CA 檔案:
```
mkdir -p /etc/kibana/certs
cp /etc/elasticsearch/certs/http_ca.crt /etc/kibana/certs/
chown -R kibana:kibana /etc/kibana/certs
```

## Fleet Server（Elastic Agent）
Fleet Server 需要 Kibana 已完成啟動並可登入。
提示: 套件庫安裝的 elastic-agent 為 basic flavor，Fleet Server 需要 complete flavor。建議使用 Elastic Agent tarball 版本安裝。

初始化 Fleet:
```
curl -u elastic:PASSWORD -H 'kbn-xsrf: true' -X POST http://localhost:5601/api/fleet/setup
```

取得 Fleet Server policy ID:
```
curl -u elastic:PASSWORD -H 'kbn-xsrf: true' http://localhost:5601/api/fleet/agent_policies?perPage=200
```
提示: 找到 `is_default_fleet_server` 為 `true` 的 policy id。

建立 Fleet Server service token:
```
export ES_PATH_CONF=/etc/elasticsearch
/usr/share/elasticsearch/bin/elasticsearch-service-tokens create elastic/fleet-server fleet-server-token
```

安裝並啟動 Fleet Server:
```
elastic-agent install \
  --fleet-server-es=https://localhost:9200 \
  --fleet-server-service-token=SERVICE_TOKEN \
  --fleet-server-policy=FLEET_POLICY_ID \
  --fleet-server-host=FLEET_HOST \
  --fleet-server-port=8220 \
  --fleet-server-es-ca=/etc/elasticsearch/certs/http_ca.crt
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
systemctl enable --now elastic-agent
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

Fleet Server 測試:
```
systemctl is-active --quiet elastic-agent
curl -k https://localhost:8220/api/status
```
