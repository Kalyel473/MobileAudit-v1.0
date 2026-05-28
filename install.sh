#!/bin/bash
# ============================================================
#  MobileAudit v1.0 — Script de Instalação (Linux/Ubuntu)
# ============================================================

set -e

RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
CYAN='\033[96m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[*]${RESET} $1"; }
success() { echo -e "${GREEN}[✓]${RESET} $1"; }
warning() { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[✗]${RESET} $1"; }

echo -e "${CYAN}${BOLD}"
echo "  ███╗   ███╗ ██████╗ ██████╗ ██╗██╗     ███████╗ █████╗ ██╗   ██╗██████╗ ██╗████████╗"
echo "  ████╗ ████║██╔═══██╗██╔══██╗██║██║     ██╔════╝██╔══██╗██║   ██║██╔══██╗██║╚══██╔══╝"
echo "  ██╔████╔██║██║   ██║██████╔╝██║██║     █████╗  ███████║██║   ██║██║  ██║██║   ██║   "
echo "  ██║╚██╔╝██║██║   ██║██╔══██╗██║██║     ██╔══╝  ██╔══██║██║   ██║██║  ██║██║   ██║   "
echo "  ██║ ╚═╝ ██║╚██████╔╝██████╔╝██║███████╗███████╗██║  ██║╚██████╔╝██████╔╝██║   ██║   "
echo "  ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝  "
echo -e "${RESET}"
echo -e "${BOLD}  Instalador v1.0 — Android & iOS Audit Tool${RESET}"
echo -e "  ─────────────────────────────────────────────────────\n"

# ─── Verifica Python ────────────────────────────────────────
info "Verificando Python 3..."
if ! command -v python3 &>/dev/null; then
    error "Python 3 não encontrado. Instale com: sudo apt install python3"
    exit 1
fi
PYTHON_VER=$(python3 --version 2>&1)
success "Python encontrado: $PYTHON_VER"

# ─── Verifica pip ───────────────────────────────────────────
info "Verificando pip..."
if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
    info "pip não encontrado. Instalando..."
    sudo apt-get install -y python3-pip
fi
success "pip disponível"

# ─── Instala dependências do sistema ────────────────────────
info "Instalando dependências do sistema (requer sudo)..."

echo -e "\n${YELLOW}  Instalar ferramentas Android (ADB)? [S/n]${RESET} \c"
read -r resp
if [[ "$resp" != "n" && "$resp" != "N" ]]; then
    sudo apt-get install -y android-tools-adb 2>/dev/null || \
    sudo apt-get install -y adb 2>/dev/null || \
    warning "ADB não pôde ser instalado via apt. Baixe o Android SDK Platform Tools."
    success "ADB instalado/verificado"
fi

echo -e "\n${YELLOW}  Instalar ferramentas iOS (libimobiledevice)? [S/n]${RESET} \c"
read -r resp
if [[ "$resp" != "n" && "$resp" != "N" ]]; then
    sudo apt-get install -y \
        libimobiledevice-utils \
        ideviceinstaller \
        libplist-utils \
        usbmuxd 2>/dev/null || \
    warning "Algumas ferramentas iOS podem não estar disponíveis."

    # Habilita usbmuxd para iOS
    sudo systemctl enable usbmuxd 2>/dev/null || true
    sudo systemctl start usbmuxd 2>/dev/null || true
    success "libimobiledevice instalado/verificado"
fi

# ─── Instala dependências Python ────────────────────────────
info "Instalando dependências Python..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

python3 -m pip install --upgrade pip --quiet
python3 -m pip install -r requirements.txt --quiet && \
    success "Pacotes Python instalados" || \
    warning "Alguns pacotes Python falharam. Verifique manualmente."

# pymobiledevice3 (pode precisar de build tools)
echo -e "\n${YELLOW}  Instalar pymobiledevice3 (suporte iOS avançado)? [S/n]${RESET} \c"
read -r resp
if [[ "$resp" != "n" && "$resp" != "N" ]]; then
    python3 -m pip install pymobiledevice3 --quiet && \
        success "pymobiledevice3 instalado" || \
        warning "pymobiledevice3 falhou. A ferramenta usará idevice CLI como fallback."
fi

# ─── Cria diretório de relatórios ───────────────────────────
mkdir -p "$SCRIPT_DIR/reports"
success "Diretório reports/ criado"

# ─── Torna executável ────────────────────────────────────────
chmod +x "$SCRIPT_DIR/mobileaudit.py"
success "mobileaudit.py marcado como executável"

# ─── Cria alias (opcional) ──────────────────────────────────
echo -e "\n${YELLOW}  Criar alias 'mobileaudit' no ~/.bashrc? [S/n]${RESET} \c"
read -r resp
if [[ "$resp" != "n" && "$resp" != "N" ]]; then
    ALIAS_CMD="alias mobileaudit='python3 $SCRIPT_DIR/mobileaudit.py'"
    if ! grep -q "alias mobileaudit=" ~/.bashrc 2>/dev/null; then
        echo "" >> ~/.bashrc
        echo "# MobileAudit" >> ~/.bashrc
        echo "$ALIAS_CMD" >> ~/.bashrc
        success "Alias adicionado ao ~/.bashrc. Execute: source ~/.bashrc"
    else
        warning "Alias já existe em ~/.bashrc"
    fi
fi

# ─── Regras udev para ADB (Linux) ───────────────────────────
echo -e "\n${YELLOW}  Configurar regras udev para ADB (acesso USB sem sudo)? [S/n]${RESET} \c"
read -r resp
if [[ "$resp" != "n" && "$resp" != "N" ]]; then
    UDEV_RULES='/etc/udev/rules.d/51-android.rules'
    if [ ! -f "$UDEV_RULES" ]; then
        sudo bash -c 'cat > /etc/udev/rules.d/51-android.rules << "EOF"
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="22b8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0bb4", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="12d1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="1004", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="05c6", MODE="0666", GROUP="plugdev"
EOF'
        sudo chmod a+r "$UDEV_RULES"
        sudo udevadm control --reload-rules 2>/dev/null || true
        success "Regras udev configuradas"
    else
        warning "Regras udev já existem"
    fi
fi

# ─── Resumo ─────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  ✓ Instalação concluída!${RESET}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${RESET}"
echo
echo -e "  ${BOLD}Próximos passos:${RESET}"
echo -e "  ${CYAN}1.${RESET} Verifique dependências:"
echo -e "       python3 mobileaudit.py --check-deps"
echo
echo -e "  ${CYAN}2.${RESET} Auditoria Android (conecte via USB com USB Debug ativo):"
echo -e "       python3 mobileaudit.py --android --all"
echo
echo -e "  ${CYAN}3.${RESET} Auditoria iOS (conecte, desbloqueie e toque 'Confiar'):"
echo -e "       python3 mobileaudit.py --ios --all"
echo
echo -e "  ${CYAN}4.${RESET} Relatórios ficam em: ${BOLD}./reports/${RESET}"
echo
echo -e "  ${YELLOW}⚠  Use apenas em seus próprios dispositivos!${RESET}"
echo
