# Elastic Stack Configuration Notes

## Elasticsearch baseline (single-node)
File: `/etc/elasticsearch/elasticsearch.yml`

Example:
```
cluster.name: elk-cluster
node.name: ${HOSTNAME}
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
```

## Elasticsearch heap
File: `/etc/elasticsearch/jvm.options.d/heap.options`

Example:
```
-Xms2g
-Xmx2g
```

## Security (Elastic 8.x defaults)
- Keep security enabled for production.
- After starting Elasticsearch, set a known password:
```
/usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic
```
- Generate a Kibana enrollment token when preferred:
```
/usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana
```

## Kibana
File: `/etc/kibana/kibana.yml`

Example:
```
server.host: "0.0.0.0"
server.port: 5601
elasticsearch.hosts: ["https://localhost:9200"]
elasticsearch.username: "elastic"
elasticsearch.password: "set_this_value"
elasticsearch.ssl.certificateAuthorities: ["/etc/kibana/certs/http_ca.crt"]
```

Copy the CA file:
```
mkdir -p /etc/kibana/certs
cp /etc/elasticsearch/certs/http_ca.crt /etc/kibana/certs/
chown -R kibana:kibana /etc/kibana/certs
```

## Logstash
Pipeline directory: `/etc/logstash/conf.d/`

Example output to Elasticsearch:
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

Store the password in the Logstash keystore:
```
/usr/share/logstash/bin/logstash-keystore create
/usr/share/logstash/bin/logstash-keystore add ES_PWD
```

Copy the CA file:
```
mkdir -p /etc/logstash/certs
cp /etc/elasticsearch/certs/http_ca.crt /etc/logstash/certs/
chown -R logstash:logstash /etc/logstash/certs
```

## Service start order
```
systemctl enable --now elasticsearch
systemctl enable --now kibana
systemctl enable --now logstash
```

## Tests
Elasticsearch:
```
curl --cacert /etc/elasticsearch/certs/http_ca.crt -u elastic:PASSWORD https://localhost:9200
```

Kibana:
```
curl -I http://localhost:5601
```

Logstash config test:
```
/usr/share/logstash/bin/logstash --path.settings /etc/logstash -t
```
