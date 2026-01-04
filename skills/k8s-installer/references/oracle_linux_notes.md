# Oracle Linux 特定注意事項

## 與 RHEL/CentOS 的差異

Oracle Linux 基於 RHEL，大部分指令相容，但有以下注意事項：

## SELinux

Oracle Linux 預設啟用 SELinux，可能影響 K8S 運作：

```bash
# 檢查狀態
getenforce

# 暫時關閉（測試用）
setenforce 0

# 永久設定為 permissive（建議）
sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config
```

## Firewall

Oracle Linux 使用 firewalld：

```bash
# 開放必要 port（Control Plane）
firewall-cmd --permanent --add-port=6443/tcp
firewall-cmd --permanent --add-port=2379-2380/tcp
firewall-cmd --permanent --add-port=10250/tcp
firewall-cmd --permanent --add-port=10259/tcp
firewall-cmd --permanent --add-port=10257/tcp

# 開放必要 port（Worker）
firewall-cmd --permanent --add-port=10250/tcp
firewall-cmd --permanent --add-port=30000-32767/tcp

# 套用變更
firewall-cmd --reload
```

## 套件管理

Oracle Linux 9 使用 dnf：

```bash
# 安裝套件
dnf install -y containerd

# 啟用 EPEL（某些套件需要）
dnf install -y oracle-epel-release-el9
```

## UEK vs RHCK

Oracle Linux 提供兩種核心：
- **UEK (Unbreakable Enterprise Kernel)**：Oracle 優化版本
- **RHCK (Red Hat Compatible Kernel)**：與 RHEL 相容

建議使用 **RHCK** 以確保 K8S 相容性：

```bash
# 檢查目前核心
uname -r

# 切換至 RHCK
grubby --set-default /boot/vmlinuz-<rhck-version>
reboot
```

## containerd 注意事項

Oracle Linux 的 containerd 套件位於 ol9_addons repo：

```bash
# 確認 repo 啟用
dnf config-manager --enable ol9_addons

# 安裝
dnf install -y containerd
```

## 網路設定

Oracle Linux 9 使用 NetworkManager：

```bash
# 確認網路介面
nmcli device status

# 設定靜態 IP（如需要）
nmcli con mod "System eth0" ipv4.addresses 192.168.1.100/24
nmcli con mod "System eth0" ipv4.gateway 192.168.1.1
nmcli con mod "System eth0" ipv4.dns "8.8.8.8"
nmcli con mod "System eth0" ipv4.method manual
nmcli con up "System eth0"
```

## 參考資源

- [Oracle Linux 9 Documentation](https://docs.oracle.com/en/operating-systems/oracle-linux/9/)
- [Running Kubernetes on Oracle Linux](https://docs.oracle.com/en/operating-systems/oracle-linux/kubernetes/)
