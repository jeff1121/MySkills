# IOS / IOS-XE 常用指令參考

適用設備：Catalyst 交換機、ISR 路由器、CSR 虛擬路由器等。

## 提示符格式

| 模式 | 提示符 | 說明 |
|------|--------|------|
| User EXEC | `Router>` | 受限指令模式 |
| Privileged EXEC | `Router#` | 完整指令模式 |
| Global Config | `Router(config)#` | 全域設定模式 |
| Interface Config | `Router(config-if)#` | 介面設定模式 |
| Router Config | `Router(config-router)#` | 路由協定設定模式 |

## 常用 Show 指令

### 系統資訊

| 指令 | 說明 |
|------|------|
| `show version` | 系統版本、啟動時間、硬體資訊 |
| `show inventory` | 硬體模組庫存 |
| `show processes cpu` | CPU 使用率 |
| `show memory statistics` | 記憶體狀態 |
| `show clock` | 系統時間 |

### 介面

| 指令 | 說明 |
|------|------|
| `show ip interface brief` | 介面 IP 與狀態摘要 |
| `show interfaces status` | 交換機連接埠狀態（speed/duplex/VLAN） |
| `show interfaces <name>` | 特定介面詳細資訊 |
| `show ip interface <name>` | 特定介面 L3 資訊 |
| `show interfaces trunk` | Trunk 連接埠資訊 |
| `show interfaces counters` | 介面計數器 |

### VLAN

| 指令 | 說明 |
|------|------|
| `show vlan brief` | VLAN 清單與連接埠分配 |
| `show vlan id <id>` | 特定 VLAN 詳細資訊 |

### 路由

| 指令 | 說明 |
|------|------|
| `show ip route` | IPv4 路由表 |
| `show ip route summary` | 路由表摘要 |
| `show ip protocols` | 路由協定狀態 |

### BGP

| 指令 | 說明 |
|------|------|
| `show ip bgp summary` | BGP 鄰居摘要 |
| `show ip bgp` | BGP 表格 |
| `show ip bgp neighbors <ip>` | BGP 鄰居詳細 |

### OSPF

| 指令 | 說明 |
|------|------|
| `show ip ospf neighbor` | OSPF 鄰居 |
| `show ip ospf interface brief` | OSPF 介面摘要 |
| `show ip ospf database` | OSPF LSDB |

### Spanning Tree

| 指令 | 說明 |
|------|------|
| `show spanning-tree summary` | STP 摘要 |
| `show spanning-tree vlan <id>` | 特定 VLAN 的 STP |

### ACL

| 指令 | 說明 |
|------|------|
| `show access-lists` | 所有 ACL |
| `show ip access-lists <name>` | 特定 ACL |

### 其他

| 指令 | 說明 |
|------|------|
| `show cdp neighbors detail` | CDP 鄰居 |
| `show lldp neighbors detail` | LLDP 鄰居 |
| `show ip arp` | ARP 表格 |
| `show mac address-table` | MAC 位址表 |
| `show ntp status` | NTP 同步狀態 |
| `show logging` | 系統日誌 |
| `show running-config` | 運行中組態 |
| `show startup-config` | 啟動組態 |
| `show etherchannel summary` | EtherChannel 摘要 |

## 常用 Config 指令範例

### VLAN 建立

```
configure terminal
vlan 100
  name DATA
exit
```

### 介面設定

```
configure terminal
interface GigabitEthernet0/1
  description Uplink to Core
  ip address 10.0.0.1 255.255.255.0
  no shutdown
exit
```

### 靜態路由

```
configure terminal
ip route 192.168.0.0 255.255.0.0 10.0.0.254
```

### OSPF

```
configure terminal
router ospf 1
  network 10.0.0.0 0.0.0.255 area 0
exit
```

### ACL

```
configure terminal
ip access-list extended BLOCK_TELNET
  deny tcp any any eq 23
  permit ip any any
exit
```
