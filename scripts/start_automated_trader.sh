#!/bin/bash
# 启动全自动化交易系统

set -e

# 脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "🤖 启动全自动化AI交易系统"
echo "=================================================="
echo "项目目录: $PROJECT_DIR"
echo ""

# 切换到项目目录
cd "$PROJECT_DIR"

# 检查Python环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: 未找到虚拟环境 (venv)"
    echo "请先运行: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活Python虚拟环境..."
source venv/bin/activate

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到 .env 文件"
    echo "请从 .env.example 复制并配置您的API密钥"
    echo "cp .env.example .env"
    echo ""
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 创建日志目录
mkdir -p logs
mkdir -p data

echo ""
echo "✅ 环境检查完成"
echo ""
echo "=================================================="
echo "🚀 启动交易系统..."
echo "=================================================="
echo ""
echo "提示:"
echo "  - 使用 Ctrl+C 优雅关闭系统"
echo "  - 日志保存在 logs/ 目录"
echo "  - 数据库保存在 data/ 目录"
echo ""
echo "=================================================="
echo ""

# 启动交易系统
python -m src.automated_trader

echo ""
echo "=================================================="
echo "✅ 交易系统已关闭"
echo "=================================================="
