# IOS-XR 常用指令參考

適用設備：ASR 9000、NCS 系列、CRS 系列、XRv 虛擬路由器等電信級路由器。

## 提示符格式

| 模式 | 提示符 | 說明 |
|------|--------|------|
| EXEC | `RP/0/RP0/CPU0:router#` | 執行模式 |
| Global Config | `RP/0/RP0/CPU0:router(config)#` | 全域設定模式 |
| Interface Config | `RP/0/RP0/CPU0:router(config-if)#` | 介面設定模式 |
| Router Config | `RP/0/RP0/CPU0:router(config-router)#` | 路由設定模式 |

## IOS-XR 特有行為

- **Commit 機制**：設定變更需執行 `commit` 才會生效（類似 Junos）
- **`commit confirmed`**：設定在指定時間後自動回滾（除非再次 `commit`）
- **`show configuration changes`**：查看尚未 commit 的變更
- **`rollback configuration last 1`**：回滾到上一個 commit 狀態
- **IP 位址格式**：使用 `ipv4 address` 而非 `ip address`
- **無 `write memory`**：設定以 commit 寫入
- **Admin 模式**：`admin` 進入管理平面

## 常用 Show 指令

### 系統資訊

| 指令 | 說明 |
|------|------|
| `show version` | 系統版本 |
| `show inventory` | 硬體模組 |
| `show platform` | 平台狀態（LC、RP） |
| `show processes cpu` | CPU 使用率 |
| `show memory summary` | 記憶體摘要 |

### 介面

| 指令 | 說明 |
|------|------|
| `show ip interface brief` | 介面 IP 摘要 |
| `show interfaces summary` | 介面統計摘要 |
| `show interfaces <name>` | 特定介面詳細 |
| `show bundle` | Bundle 介面狀態 |

### 路由

| 指令 | 說明 |
|------|------|
| `show route` | IPv4 路由表（注意：不是 `show ip route`） |
| `show route summary` | 路由表摘要 |
| `show route ipv6` | IPv6 路由表 |

### BGP

| 指令 | 說明 |
|------|------|
| `show bgp summary` | BGP 鄰居摘要 |
| `show bgp ipv4 unicast` | BGP IPv4 表格 |
| `show bgp neighbors <ip>` | BGP 鄰居詳細 |
| `show bgp ipv4 unicast summary` | BGP IPv4 摘要 |

### OSPF

| 指令 | 說明 |
|------|------|
| `show ospf neighbor` | OSPF 鄰居 |
| `show ospf interface brief` | OSPF 介面摘要 |
| `show ospf database` | OSPF LSDB |

### IS-IS

| 指令 | 說明 |
|------|------|
| `show isis neighbors` | IS-IS 鄰居 |
| `show isis interface brief` | IS-IS 介面摘要 |
| `show isis database` | IS-IS LSDB |

### MPLS

| 指令 | 說明 |
|------|------|
| `show mpls interfaces` | MPLS 介面 |
| `show mpls forwarding` | MPLS 轉發表 |
| `show mpls ldp neighbor brief` | LDP 鄰居摘要 |
| `show mpls traffic-eng tunnels brief` | TE Tunnel 摘要 |

### Segment Routing

| 指令 | 說明 |
|------|------|
| `show segment-routing local-block` | SR Local Block |
| `show isis segment-routing label table` | SR 標籤表 |
| `show segment-routing mapping-server prefix-sid-map` | SR Mapping |

### BFD

| 指令 | 說明 |
|------|------|
| `show bfd session` | BFD 連線狀態 |
| `show bfd session detail` | BFD 詳細 |

### ACL

| 指令 | 說明 |
|------|------|
| `show access-lists` | 所有 ACL |
| `show access-lists ipv4 <name>` | 特定 IPv4 ACL |

### 其他

| 指令 | 說明 |
|------|------|
| `show cdp neighbors detail` | CDP 鄰居 |
| `show lldp neighbors detail` | LLDP 鄰居 |
| `show arp` | ARP 表格 |
| `show ntp status` | NTP 狀態 |
| `show logging` | 系統日誌 |
| `show running-config` | 運行中組態 |
| `show configuration changes` | 尚未 commit 的變更 |

## 常用 Config 指令範例

### 介面設定

```
configure terminal
interface GigabitEthernet0/0/0/0
  description Uplink to PE
  ipv4 address 10.0.0.1 255.255.255.252
  no shutdown
commit
```

### 靜態路由

```
configure terminal
router static
  address-family ipv4 unicast
    192.168.0.0/16 10.0.0.2
  exit
commit
```

### OSPF

```
configure terminal
router ospf 1
  area 0
    interface GigabitEthernet0/0/0/0
    exit
  exit
commit
```

### BGP

```
configure terminal
router bgp 65000
  neighbor 10.0.0.2
    remote-as 65001
    address-family ipv4 unicast
    exit
  exit
commit
```

### ACL

```
configure terminal
ipv4 access-list DENY_TELNET
  10 deny tcp any any eq 23
  20 permit ipv4 any any
exit
commit
```

### Commit 管理

```
commit              # 套用變更
commit confirmed 60 # 60 秒後自動回滾（除非再次 commit）
rollback configuration last 1  # 回滾到上一個版本
show configuration changes     # 查看未 commit 的變更
```
