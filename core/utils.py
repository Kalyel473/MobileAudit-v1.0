#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/utils.py — Utilitários, banner e verificação de dependências
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

# ─── CORES ANSI ─────────────────────────────────────────────────────────────────
class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"

    # Desabilita cores se não for terminal
    @classmethod
    def disable(cls):
        for attr in ["RESET","BOLD","RED","GREEN","YELLOW","BLUE","MAGENTA","CYAN","WHITE","GRAY"]:
            setattr(cls, attr, "")

if not sys.stdout.isatty():
    Colors.disable()

C = Colors


# ─── BANNER ─────────────────────────────────────────────────────────────────────
def banner():
    logo = f"""
{C.CYAN}{C.BOLD}
 ███╗   ███╗ ██████╗ ██████╗ ██╗██╗     ███████╗ █████╗ ██╗   ██╗██████╗ ██╗████████╗
 ████╗ ████║██╔═══██╗██╔══██╗██║██║     ██╔════╝██╔══██╗██║   ██║██╔══██╗██║╚══██╔══╝
 ██╔████╔██║██║   ██║██████╔╝██║██║     █████╗  ███████║██║   ██║██║  ██║██║   ██║
 ██║╚██╔╝██║██║   ██║██╔══██╗██║██║     ██╔══╝  ██╔══██║██║   ██║██║  ██║██║   ██║
 ██║ ╚═╝ ██║╚██████╔╝██████╔╝██║███████╗███████╗██║  ██║╚██████╔╝██████╔╝██║   ██║
 ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝
{C.RESET}
{C.GRAY}  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  {C.GREEN}MobileAudit v1.0{C.GRAY}  |  Auditoria Completa Android & iOS            ║
  ║  {C.YELLOW}⚠ USO AUTORIZADO APENAS EM DISPOSITIVOS PRÓPRIOS OU COM PERMISSÃO{C.GRAY}  ║
  ║  {C.CYAN}Compatível com: LGPD · Marco Civil da Internet · Lei 12.737/2012{C.GRAY}   ║
  ╚══════════════════════════════════════════════════════════════════════════╝{C.RESET}
    """
    print(logo)
    print(f"{C.GRAY}  Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Python {sys.version.split()[0]}{C.RESET}\n")


# ─── FUNÇÕES DE PRINT ───────────────────────────────────────────────────────────
def print_info(msg):
    print(f"{C.BLUE}[*]{C.RESET} {msg}")

def print_success(msg):
    print(f"{C.GREEN}[✓]{C.RESET} {msg}")

def print_error(msg):
    print(f"{C.RED}[✗]{C.RESET} {msg}")

def print_warning(msg):
    print(f"{C.YELLOW}[!]{C.RESET} {msg}")

def print_module_header(name, icon="🔍"):
    width = 60
    title = f"  {icon}  {name}  "
    pad = (width - len(title)) // 2
    print(f"\n{C.CYAN}{C.BOLD}{'─' * width}{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}{' ' * pad}{title}{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}{'─' * width}{C.RESET}")

def print_result(key, value, indent=2):
    spaces = " " * indent
    if value is None or value == "":
        value = f"{C.GRAY}N/A{C.RESET}"
    elif isinstance(value, bool):
        value = f"{C.GREEN}Sim{C.RESET}" if value else f"{C.RED}Não{C.RESET}"
    print(f"{spaces}{C.BOLD}{key}:{C.RESET} {value}")

def print_table(headers, rows, indent=2):
    """Imprime tabela simples no terminal."""
    spaces = " " * indent
    if not rows:
        print(f"{spaces}{C.GRAY}(nenhum resultado){C.RESET}")
        return

    # Calcula largura das colunas
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Header
    header_line = "  ".join(f"{C.BOLD}{h:<{col_widths[i]}}{C.RESET}" for i, h in enumerate(headers))
    separator = "  ".join("─" * w for w in col_widths)
    print(f"{spaces}{header_line}")
    print(f"{spaces}{C.GRAY}{separator}{C.RESET}")

    # Linhas
    for row in rows[:50]:  # Limita a 50 linhas no terminal
        line = "  ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row) if i < len(col_widths))
        print(f"{spaces}{line}")

    if len(rows) > 50:
        print(f"{spaces}{C.GRAY}... e mais {len(rows) - 50} itens (ver relatório completo){C.RESET}")


# ─── VERIFICAÇÃO DE DEPENDÊNCIAS ────────────────────────────────────────────────
def check_dependencies():
    print_module_header("Verificação de Dependências", "🔧")

    deps = {
        "Android (ADB)": {
            "adb": ("adb version", "Android Debug Bridge — instale via 'apt install adb' ou Android SDK"),
        },
        "iOS (libimobiledevice)": {
            "ideviceinfo":       ("ideviceinfo --version", "apt install libimobiledevice-utils"),
            "ideviceinstaller":  ("ideviceinstaller --version", "apt install ideviceinstaller"),
            "idevicediagnostics":("idevicediagnostics --version", "apt install libimobiledevice-utils"),
            "idevicebackup2":    ("idevicebackup2 --version", "apt install libimobiledevice-utils"),
            "idevicesyslog":     ("idevicesyslog --version", "apt install libimobiledevice-utils"),
        },
        "Python (pip)": {
            "pymobiledevice3":  (None, "pip install pymobiledevice3"),
            "rich":             (None, "pip install rich"),
            "tabulate":         (None, "pip install tabulate"),
        },
    }

    all_ok = True
    for category, tools in deps.items():
        print(f"\n{C.YELLOW}{C.BOLD}  {category}{C.RESET}")
        for tool, (cmd, install_hint) in tools.items():
            if cmd is None:
                # Verifica import Python
                try:
                    __import__(tool)
                    print_success(f"  {tool} (Python package)")
                except ImportError:
                    print_error(f"  {tool} — AUSENTE → {C.GRAY}{install_hint}{C.RESET}")
                    all_ok = False
            else:
                found = shutil.which(tool.split()[0])
                if found:
                    try:
                        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
                        version_line = (result.stdout or result.stderr).split("\n")[0].strip()
                        print_success(f"  {tool} — {C.GRAY}{version_line[:60]}{C.RESET}")
                    except Exception:
                        print_success(f"  {tool} — encontrado em {found}")
                else:
                    print_error(f"  {tool} — AUSENTE → {C.GRAY}{install_hint}{C.RESET}")
                    all_ok = False

    print()
    if all_ok:
        print_success("Todas as dependências estão instaladas!")
    else:
        print_warning("Algumas dependências estão faltando. Instale-as antes de prosseguir.")

    return all_ok


# ─── UTILITÁRIOS GERAIS ──────────────────────────────────────────────────────────
def run_command(cmd, timeout=30):
    """Executa comando e retorna stdout."""
    try:
        result = subprocess.run(
            cmd, shell=isinstance(cmd, str),
            capture_output=True, text=True,
            timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except FileNotFoundError:
        return "", -127
    except Exception as e:
        return str(e), -1


def format_bytes(size_bytes):
    """Formata bytes em unidade legível."""
    if size_bytes is None:
        return "N/A"
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def sanitize_text(text):
    """Remove caracteres problemáticos para relatórios."""
    if not text:
        return ""
    return text.encode("utf-8", errors="replace").decode("utf-8").strip()


def ensure_reports_dir():
    """Garante que o diretório reports/ existe."""
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir
