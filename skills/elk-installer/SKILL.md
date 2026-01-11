---
name: elk-installer
description: 安裝 Linux 伺服器上安裝與設定 Elastic Stack（Elasticsearch、Logstash、Kibana），包含 OS 更新、套件庫設定、組態、服務啟動、測試與結果回報。當使用者提供正式環境的 SSH 存取並希望自動化安裝 ELK/Elastic Stack（RHEL 9+、Oracle Linux 9+、SLES 15+、Debian 12+、Photon OS 5+）時使用。
---

# ELK 安裝器

## 概覽
透過隨附的 Python SSH 安裝腳本在遠端 Linux 主機安裝、設定並驗證 Elasticsearch、Logstash 與 Kibana。指令一律在代理端機器上執行，不要在本機安裝。

## 支援平台
- SUSE Linux Enterprise Server 15+
- Red Hat Enterprise Linux 9+
- Photon OS 5+
- Oracle Linux 9+
- Debian Linux 12+

## 必要輸入
在進行任何變更前先收集 SSH 連線資訊：

- HostAddr: address or IP
- HostPort: SSH port
- HostUser: login user
- HostPass: login password

提示：若未提供設定選項，先詢問並告知預設值：
- Elastic 主版本（預設 8）
- 節點模式（單節點或多節點）
- Elasticsearch 與 Kibana 綁定位址
- Elasticsearch HTTP 連接埠（預設 9200）
- Kibana 連接埠（預設 5601）
- Logstash Beats 連接埠（預設 5044）
- JVM heap size（預設 2g）
- 是否開放 Elasticsearch、Kibana、Logstash 的防火牆連接埠（預設 9200、5601、5044）
- 多節點的 seed hosts 與 initial masters

提示範例：

```
請提供 SSH 連線資訊：
HostAddr:
HostPort:
HostUser:
HostPass:
```

## 工作流程
### 1. 在代理端機器安裝前置需求
- 安裝 SSH 安裝器所需的 Python 相依套件：
  - `python3 -m pip install -r scripts/requirements.txt`

### 2. 執行 SSH 安裝器（建議）
- 執行 `python3 scripts/main.py` 進入互動式提示，或直接帶入旗標。
- 套用變更前先確認設定摘要。
- 目標主機需具備 root 權限或免密 sudo。
- 多節點情境下，每台節點各跑一次，並使用相同的 seed host 與 initial master 值。

指令範例：
```
python3 scripts/main.py \
  --host 10.0.0.10 \
  --user root \
  --open-firewall
```

### 3. 回報結果
- 擷取腳本輸出摘要並回報：
  - Elasticsearch URL
  - Kibana URL
  - 產生的 elastic 密碼
- 提醒使用者妥善保存密碼。
- 若在 Photon OS 上略過防火牆規則，需明確說明。

### 4. 備援流程（僅在腳本受阻時使用）
- 改用 OS 專屬參考文件進行手動步驟：
  - `references/os-rhel9-oracle9.md`
  - `references/os-sles15.md`
  - `references/os-debian12.md`
  - `references/os-photon5.md`
- 使用 `references/elastic-config.md` 取得組態範本。

## 疑難排解（快速）
- SSH 失敗：確認網路、帳密與 sudo 權限。
- Elasticsearch 無法啟動：檢查 `journalctl -u elasticsearch` 與組態語法。
- Kibana 無法連線：確認帳密、CA 與 `elasticsearch.hosts`。
- Logstash pipeline 錯誤：執行組態測試並查看 `/var/log/logstash/logstash-plain.log`。

## 腳本
- `scripts/main.py` - SSH 安裝 CLI 進入點
- `scripts/installer.py` - 遠端安裝流程編排
- `scripts/commands.py` - OS 專屬指令與組態範本
- `scripts/ssh_client.py` - SSH 客戶端包裝器
- `scripts/requirements.txt` - Python 相依套件

## 參考文件
- `references/os-rhel9-oracle9.md`
- `references/os-sles15.md`
- `references/os-debian12.md`
- `references/os-photon5.md`
- `references/elastic-config.md`
