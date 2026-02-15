# NX-OS 常用指令參考

適用設備：Nexus 3000/5000/7000/9000 系列資料中心交換機。

## 提示符格式

| 模式 | 提示符 | 說明 |
|------|--------|------|
| User EXEC | `switch>` | 受限模式（少用） |
| Privileged EXEC | `switch#` | 完整指令模式 |
| Global Config | `switch(config)#` | 全域設定模式 |
| Interface Config | `switch(config-if)#` | 介面設定模式 |

## NX-OS 特有行為

- **Feature 啟用**：NX-OS 多數功能需先執行 `feature <name>` 啟用（如 `feature vpc`、`feature ospf`、`feature bgp`）
- **VDC**：Nexus 7000 支援 Virtual Device Context 虛擬裝置
- **無 `write memory`**：使用 `copy running-config startup-config` 儲存

## 常用 Show 指令

### 系統資訊

| 指令 | 說明 |
|------|------|
| `show version` | 系統版本與硬體 |
| `show inventory` | 模組庫存 |
| `show module` | 模組狀態 |
| `show feature` | 已啟用的功能清單 |
| `show system resources` | CPU/記憶體使用率 |

### 介面

| 指令 | 說明 |
|------|------|
| `show ip interface brief` | 介面 IP 摘要（含 mgmt0） |
| `show interface status` | 連接埠狀態 |
| `show interface <name>` | 特定介面詳細 |
| `show interface trunk` | Trunk 資訊 |

### VLAN

| 指令 | 說明 |
|------|------|
| `show vlan brief` | VLAN 清單 |
| `show vlan id <id>` | 特定 VLAN |

### 路由

| 指令 | 說明 |
|------|------|
| `show ip route` | IPv4 路由表 |
| `show ip route summary` | 路由表摘要 |

### vPC

| 指令 | 說明 |
|------|------|
| `show vpc` | vPC 狀態 |
| `show vpc brief` | vPC 摘要 |
| `show vpc consistency-parameters global` | vPC 一致性 |
| `show port-channel summary` | Port-Channel 摘要 |

### BGP

| 指令 | 說明 |
|------|------|
| `show ip bgp summary` | BGP 鄰居摘要 |
| `show ip bgp` | BGP 表格 |

### OSPF

| 指令 | 說明 |
|------|------|
| `show ip ospf neighbors` | OSPF 鄰居 |
| `show ip ospf interface brief` | OSPF 介面摘要 |

### 其他

| 指令 | 說明 |
|------|------|
| `show cdp neighbors detail` | CDP 鄰居 |
| `show lldp neighbors detail` | LLDP 鄰居 |
| `show ip arp` | ARP 表格 |
| `show mac address-table` | MAC 位址表 |
| `show ntp peer-status` | NTP 同步狀態 |
| `show logging last 50` | 最近日誌 |
| `show running-config` | 運行中組態 |
| `show hsrp brief` | HSRP 狀態 |

## 常用 Config 指令範例

### 啟用功能

```
configure terminal
feature vpc
feature ospf
feature bgp
feature lacp
```

### VLAN 建立

```
configure terminal
vlan 100
  name DATA
exit
```

### 介面設定（L3）

```
configure terminal
interface Ethernet1/1
  no switchport
  ip address 10.0.0.1/24
  no shutdown
exit
```

### vPC 設定

```
configure terminal
feature vpc
vpc domain 10
  peer-keepalive destination 10.0.0.2
exit
interface port-channel 1
  vpc 1
exit
```

### Port-Channel

```
configure terminal
interface Ethernet1/1-2
  channel-group 1 mode active
exit
```
