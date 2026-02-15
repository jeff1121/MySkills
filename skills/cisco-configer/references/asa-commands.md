# ASA 常用指令參考

適用設備：Cisco ASA 5500 系列、ASA-X 系列、Firepower 上的 ASA 映像檔。

## 提示符格式

| 模式 | 提示符 | 說明 |
|------|--------|------|
| User EXEC | `ciscoasa>` | 受限模式 |
| Privileged EXEC | `ciscoasa#` | 完整指令模式 |
| Global Config | `ciscoasa(config)#` | 全域設定模式 |
| Interface Config | `ciscoasa(config-if)#` | 介面設定模式 |

## ASA 特有行為

- **Security Level**：每個介面需設定 `nameif` 與 `security-level`（0=outside, 100=inside）
- **Context 模式**：多 context 模式下使用 `changeto context <name>` 切換
- **NAT 語法**：與 IOS 不同，使用 `nat (inside,outside)` 格式
- **ACL 應用**：透過 `access-group` 綁定到介面
- **無 VLAN 設定**：ASA 使用 sub-interface + VLAN tag

## 常用 Show 指令

### 系統資訊

| 指令 | 說明 |
|------|------|
| `show version` | 系統版本、授權、啟動時間 |
| `show cpu usage` | CPU 使用率 |
| `show memory` | 記憶體使用 |
| `show firewall` | 防火牆模式（routed/transparent） |

### 介面

| 指令 | 說明 |
|------|------|
| `show interface ip brief` | 介面 IP 摘要 |
| `show interface summary` | 介面流量摘要 |
| `show interface <name>` | 特定介面詳細 |

### 安全性

| 指令 | 說明 |
|------|------|
| `show access-list` | 所有 ACL（含命中計數） |
| `show access-list <name>` | 特定 ACL |
| `show xlate` | NAT 轉譯表 |
| `show xlate count` | NAT 轉譯計數 |
| `show nat` | NAT 規則 |
| `show nat detail` | NAT 規則詳細 |
| `show service-policy` | 服務策略統計 |

### 連線

| 指令 | 說明 |
|------|------|
| `show conn count` | 連線計數 |
| `show conn` | 作用中連線 |
| `show conn detail` | 連線詳細資訊 |
| `show local-host` | 本地主機連線追蹤 |

### VPN

| 指令 | 說明 |
|------|------|
| `show vpn-sessiondb summary` | VPN 連線摘要 |
| `show vpn-sessiondb anyconnect` | AnyConnect 連線 |
| `show crypto ipsec sa` | IPsec SA 狀態 |
| `show crypto isakmp sa` | IKE SA 狀態 |
| `show crypto ikev2 sa` | IKEv2 SA 狀態 |

### 高可用性

| 指令 | 說明 |
|------|------|
| `show failover` | Failover 狀態 |
| `show failover state` | Failover 角色 |

### Context

| 指令 | 說明 |
|------|------|
| `show context` | Context 清單 |
| `show context detail` | Context 詳細 |
| `changeto context <name>` | 切換 Context |
| `changeto system` | 切換到系統 Context |

### 其他

| 指令 | 說明 |
|------|------|
| `show route` | 路由表（注意：不是 `show ip route`） |
| `show arp` | ARP 表格 |
| `show ntp status` | NTP 狀態 |
| `show logging` | 日誌 |
| `show running-config` | 運行中組態 |

## 常用 Config 指令範例

### 介面設定

```
configure terminal
interface GigabitEthernet0/0
  nameif outside
  security-level 0
  ip address 203.0.113.1 255.255.255.0
  no shutdown
exit
```

### ACL

```
configure terminal
access-list OUTSIDE_IN extended permit tcp any host 10.0.0.100 eq 443
access-list OUTSIDE_IN extended deny ip any any log
access-group OUTSIDE_IN in interface outside
```

### NAT（靜態）

```
configure terminal
object network WEB_SERVER
  host 10.0.0.100
  nat (inside,outside) static 203.0.113.100
exit
```

### 路由

```
configure terminal
route outside 0.0.0.0 0.0.0.0 203.0.113.254
```

### Site-to-Site VPN（IKEv2）

```
configure terminal
crypto ikev2 policy 10
  encryption aes-256
  integrity sha256
  group 14
  prf sha256
  lifetime seconds 86400
exit
```
