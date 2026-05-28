#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MobileAudit v1.0 — Ferramenta de Auditoria para Android & iOS
Uso pessoal e autorizado. Respeite a privacidade.
"""

import argparse
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import banner, print_info, print_error, print_success, print_warning, check_dependencies
from core.report import ReportGenerator


def main():
    banner()

    parser = argparse.ArgumentParser(
        prog="mobileaudit",
        description="MobileAudit v1.0 — Auditoria completa de dispositivos Android e iOS",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Exemplos de uso:
  python mobileaudit.py --android --all
  python mobileaudit.py --android --modules info apps security network
  python mobileaudit.py --ios --all
  python mobileaudit.py --ios --modules info battery storage
  python mobileaudit.py --android --all --output relatorio.html
  python mobileaudit.py --check-deps

Módulos Android disponíveis:
  info       Informações do dispositivo (modelo, IMEI, Android version)
  apps       Aplicativos instalados (sistema + usuário)
  perms      Permissões perigosas concedidas aos apps
  security   Status de segurança (criptografia, bloqueio, USB debug)
  network    Informações de rede (WiFi, IP, MAC, DNS, proxy)
  storage    Armazenamento interno e externo
  battery    Saúde e status da bateria
  processes  Processos e serviços em execução
  accounts   Contas sincronizadas
  bluetooth  Dispositivos Bluetooth pareados
  backup     Configurações de backup

Módulos iOS disponíveis:
  info       Informações do dispositivo (modelo, UDID, iOS version)
  apps       Aplicativos instalados
  battery    Status e saúde da bateria
  storage    Uso de armazenamento
  network    Informações de rede
  security   Segurança (jailbreak, senhas, certificados)
  profiles   Perfis de configuração MDM instalados
  backup     Status e histórico de backups
        """,
    )

    # Plataforma
    platform_group = parser.add_mutually_exclusive_group(required=True)
    platform_group.add_argument("--android", action="store_true", help="Auditar dispositivo Android via ADB")
    platform_group.add_argument("--ios", action="store_true", help="Auditar dispositivo iOS via libimobiledevice")
    platform_group.add_argument("--check-deps", action="store_true", help="Verificar dependências necessárias")

    # Módulos
    parser.add_argument(
        "--all", action="store_true", help="Executar todos os módulos de auditoria"
    )
    parser.add_argument(
        "--modules", nargs="+", metavar="MODULE",
        help="Módulos específicos a executar (separados por espaço)"
    )

    # Saída
    parser.add_argument("--output", metavar="FILE", help="Salvar relatório em arquivo (JSON, HTML ou TXT por extensão)")
    parser.add_argument("--json", action="store_true", help="Forçar saída em JSON")
    parser.add_argument("--html", action="store_true", help="Forçar saída em HTML")
    parser.add_argument("--quiet", "-q", action="store_true", help="Modo silencioso (apenas resultados)")
    parser.add_argument("--device", metavar="SERIAL", help="Serial ADB específico (Android multi-device)")

    args = parser.parse_args()

    # Verificação de dependências
    if args.check_deps:
        check_dependencies()
        sys.exit(0)

    if not args.all and not args.modules:
        parser.error("Especifique --all ou --modules [modulo1 modulo2 ...]")

    results = {}

    # ─── ANDROID ────────────────────────────────────────────────────────────────
    if args.android:
        from modules.android.audit import AndroidAudit

        print_info("Inicializando auditoria Android via ADB...")
        auditor = AndroidAudit(device_serial=args.device, quiet=args.quiet)

        if not auditor.connect():
            print_error("Não foi possível conectar ao dispositivo Android.")
            print_warning("Verifique se: USB Debugging está ativado e o cabo USB está conectado.")
            sys.exit(1)

        android_modules = [
            "info", "apps", "perms", "security",
            "network", "storage", "battery",
            "processes", "accounts", "bluetooth", "backup"
        ]

        selected = android_modules if args.all else args.modules
        results = auditor.run_modules(selected)

    # ─── IOS ────────────────────────────────────────────────────────────────────
    elif args.ios:
        from modules.ios.audit import iOSAudit

        print_info("Inicializando auditoria iOS via libimobiledevice...")
        auditor = iOSAudit(quiet=args.quiet)

        if not auditor.connect():
            print_error("Não foi possível conectar ao dispositivo iOS.")
            print_warning("Verifique se: o device está conectado, desbloqueado e você tocou em 'Confiar'.")
            sys.exit(1)

        ios_modules = [
            "info", "apps", "battery", "storage",
            "network", "security", "profiles", "backup"
        ]

        selected = ios_modules if args.all else args.modules
        results = auditor.run_modules(selected)

    # ─── RELATÓRIO ──────────────────────────────────────────────────────────────
    if results:
        report = ReportGenerator(results)

        # Determina formato de saída
        output_file = args.output
        if output_file:
            ext = os.path.splitext(output_file)[1].lower()
            if ext == ".json" or args.json:
                report.save_json(output_file)
            elif ext == ".html" or args.html:
                report.save_html(output_file)
            else:
                report.save_txt(output_file)
            print_success(f"Relatório salvo em: {output_file}")
        else:
            # Salva automaticamente em reports/
            auto_file = report.save_auto()
            print_success(f"Relatório salvo automaticamente em: {auto_file}")


if __name__ == "__main__":
    main()
