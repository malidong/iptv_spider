#!/usr/bin/env bash
# IPTV Spider - UV 项目启动脚本（Bash 版本）
# 用途: 自动初始化环境并运行项目

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数: 打印彩色信息
print_info() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

show_help() {
    echo "Usage: ./setup.sh [command] [arguments]"
    echo ""
    echo "Available commands:"
    echo "  run              Run IPTV Spider (default)"
    echo "  help             Show project help"
    echo "  test             Run unit tests"
    echo "  shell            Start Python shell"
    echo "  dev              Install dev dependencies and start shell"
    echo "  list             List installed packages"
    echo "  lint             Run code checks"
    echo "  clean            Delete virtual environment"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh"
    echo "  ./setup.sh help"
    echo "  ./setup.sh run --filter \"CCTV\" --output_dir \"./output\""
    echo "  ./setup.sh test"
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "   IPTV Spider - UV Project Setup"
    echo "=========================================="
    echo ""

    # 检查 UV 是否安装
    print_info "Checking UV installation..."
    if ! command -v uv &> /dev/null; then
        print_error "UV not installed"
        echo "Please install UV: pip install uv"
        exit 1
    fi
    print_success "UV is installed"
    uv --version | sed 's/^/     /'
    echo ""

    # 同步依赖
    print_info "Syncing project dependencies..."
    if ! uv sync --quiet; then
        print_error "Failed to sync dependencies"
        exit 1
    fi
    print_success "Dependencies synced successfully"
    echo ""

    # 获取命令参数
    local cmd="${1:-run}"
    shift || true

    # 执行命令
    case "$cmd" in
        run)
            print_info "Running IPTV Spider..."
            uv run iptv-spider "$@"
            ;;
        help)
            print_info "Showing help information..."
            uv run iptv-spider --help
            ;;
        test)
            print_info "Running test suite..."
            uv run python -m pytest tests/ -v "$@"
            ;;
        shell)
            print_info "Starting Python shell..."
            uv run python
            ;;
        dev)
            print_info "Installing dev dependencies..."
            uv sync --extra dev --quiet
            print_info "Starting Python shell..."
            uv run python
            ;;
        clean)
            print_warning "Cleaning virtual environment..."
            if [ -d ".venv" ]; then
                rm -rf .venv
                print_success "Virtual environment removed"
            else
                echo -e "  ${BLUE}[i]${NC} Virtual environment not found"
            fi
            ;;
        list)
            print_info "Listing installed packages..."
            uv pip list "$@"
            ;;
        lint)
            print_info "Running code checks..."
            uv run flake8 src/iptv_spider/ "$@"
            ;;
        *)
            show_help
            ;;
    esac
}

# 使脚本可执行
chmod +x "$0" 2>/dev/null

# 运行主函数
main "$@"
