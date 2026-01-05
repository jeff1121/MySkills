#!/bin/bash
# WordPress 部署腳本
# 使用方式: ./deploy.sh [apply|delete|generate]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
TEMPLATE_FILE="${SCRIPT_DIR}/wordpress.yml.tpl"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "使用方式: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  apply     部署 WordPress 到 Kubernetes"
    echo "  delete    刪除 WordPress 部署"
    echo "  generate  產生 YAML 檔案 (輸出到 stdout)"
    echo "  status    檢查部署狀態"
    echo ""
    echo "範例:"
    echo "  $0 apply              # 部署"
    echo "  $0 generate > wp.yml  # 產生 YAML 檔案"
    exit 1
}

check_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo -e "${RED}錯誤: 找不到 .env 檔案${NC}"
        echo "請先複製 .env.template 並設定："
        echo "  cp .env.template .env"
        echo "  vi .env"
        exit 1
    fi
}

load_env() {
    check_env
    set -a
    source "$ENV_FILE"
    set +a
}

generate_yaml() {
    envsubst < "$TEMPLATE_FILE"
}

do_apply() {
    echo -e "${GREEN}🚀 開始部署 WordPress...${NC}"
    load_env
    generate_yaml | kubectl apply -f -
    echo ""
    echo -e "${GREEN}✅ 部署完成!${NC}"
    echo ""
    echo "等待 pods 就緒..."
    kubectl wait --for=condition=Ready pods --all -n "${NAMESPACE}" --timeout=300s || true
    echo ""
    do_status
}

do_delete() {
    echo -e "${YELLOW}🗑️  刪除 WordPress 部署...${NC}"
    load_env
    generate_yaml | kubectl delete -f - --ignore-not-found
    echo -e "${GREEN}✅ 刪除完成${NC}"
}

do_generate() {
    load_env
    generate_yaml
}

do_status() {
    load_env
    echo -e "${GREEN}=== Pods ===${NC}"
    kubectl get pods -n "${NAMESPACE}" -o wide
    echo ""
    echo -e "${GREEN}=== Services ===${NC}"
    kubectl get svc -n "${NAMESPACE}"
    echo ""
    echo -e "${GREEN}=== PVC ===${NC}"
    kubectl get pvc -n "${NAMESPACE}"
    echo ""
    
    # 取得 WordPress External IP
    EXTERNAL_IP=$(kubectl get svc wordpress -n "${NAMESPACE}" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [[ -n "$EXTERNAL_IP" ]]; then
        echo -e "${GREEN}🌐 WordPress URL: http://${EXTERNAL_IP}${NC}"
    else
        echo -e "${YELLOW}⏳ External IP 尚未分配，請稍後再試${NC}"
    fi
}

# 主程式
case "${1:-}" in
    apply)
        do_apply
        ;;
    delete)
        do_delete
        ;;
    generate)
        do_generate
        ;;
    status)
        load_env
        do_status
        ;;
    *)
        usage
        ;;
esac
