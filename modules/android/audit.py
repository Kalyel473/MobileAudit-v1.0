#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modules/android/audit.py — Módulos de Auditoria Android via ADB
Requer: adb instalado + USB Debugging ativado no dispositivo
"""

import re
import subprocess
from datetime import datetime
from core.utils import (
    print_info, print_success, print_error, print_warning,
    print_module_header, print_result, print_table, run_command, format_bytes
)


class AndroidAudit:
    def __init__(self, device_serial=None, quiet=False):
        self.serial = device_serial
        self.quiet = quiet
        self._adb_prefix = ["adb"]
        if device_serial:
            self._adb_prefix = ["adb", "-s", device_serial]

    # ─── ADB HELPER ─────────────────────────────────────────────────────────────
    def adb(self, *args, timeout=30):
        cmd = self._adb_prefix + list(args)
        return run_command(cmd, timeout=timeout)

    def adb_shell(self, shell_cmd, timeout=30):
        cmd = self._adb_prefix + ["shell", shell_cmd]
        return run_command(cmd, timeout=timeout)

    # ─── CONEXÃO ────────────────────────────────────────────────────────────────
    def connect(self):
        out, code = run_command(["adb", "devices"])
        if code != 0:
            print_error("ADB não encontrado. Instale: apt install adb")
            return False

        lines = [l.strip() for l in out.splitlines() if l.strip() and "List of devices" not in l]
        if not lines:
            print_error("Nenhum dispositivo Android conectado.")
            return False

        devices = []
        for line in lines:
            parts = line.split("\t")
            if len(parts) == 2:
                serial, status = parts
                devices.append((serial, status))
                if status == "unauthorized":
                    print_warning(f"Dispositivo {serial} não autorizado — confirme no display do celular.")
                elif status == "device":
                    print_success(f"Dispositivo conectado: {serial}")

        authorized = [d for d in devices if d[1] == "device"]
        if not authorized:
            return False

        if self.serial:
            return any(d[0] == self.serial for d in authorized)

        if len(authorized) > 1:
            print_warning(f"{len(authorized)} dispositivos conectados. Use --device SERIAL para especificar.")
        return True

    # ─── DISPATCHER ─────────────────────────────────────────────────────────────
    def run_modules(self, modules):
        results = {"_meta": {"platform": "android", "timestamp": datetime.now().isoformat()}}
        module_map = {
            "info":      self.module_info,
            "apps":      self.module_apps,
            "perms":     self.module_permissions,
            "security":  self.module_security,
            "network":   self.module_network,
            "storage":   self.module_storage,
            "battery":   self.module_battery,
            "processes": self.module_processes,
            "accounts":  self.module_accounts,
            "bluetooth": self.module_bluetooth,
            "backup":    self.module_backup,
        }
        for mod in modules:
            func = module_map.get(mod.lower())
            if func:
                print_info(f"Executando módulo: {mod}")
                try:
                    results[mod] = func()
                except Exception as e:
                    print_error(f"Erro no módulo {mod}: {e}")
                    results[mod] = {"erro": str(e)}
            else:
                print_warning(f"Módulo desconhecido: {mod}")
        return results

    # ─── MÓDULO: INFO ────────────────────────────────────────────────────────────
    def module_info(self):
        print_module_header("Informações do Dispositivo", "📱")

        props = {}
        out, _ = self.adb_shell("getprop")
        for line in out.splitlines():
            m = re.match(r'\[(.+?)\]:\s*\[(.+?)\]', line)
            if m:
                props[m.group(1)] = m.group(2)

        info = {
            "fabricante":       props.get("ro.product.manufacturer", "N/A"),
            "modelo":           props.get("ro.product.model", "N/A"),
            "device":           props.get("ro.product.device", "N/A"),
            "android_version":  props.get("ro.build.version.release", "N/A"),
            "sdk_version":      props.get("ro.build.version.sdk", "N/A"),
            "build_id":         props.get("ro.build.id", "N/A"),
            "build_type":       props.get("ro.build.type", "N/A"),
            "fingerprint":      props.get("ro.build.fingerprint", "N/A"),
            "security_patch":   props.get("ro.build.version.security_patch", "N/A"),
            "baseband":         props.get("gsm.version.baseband", "N/A"),
            "kernel":           self._get_kernel(),
            "serial":           self._get_serial(props),
            "imei":             self._get_imei(),
            "uptime":           self._get_uptime(),
            "timezone":         props.get("persist.sys.timezone", "N/A"),
            "locale":           props.get("persist.sys.locale", props.get("ro.product.locale", "N/A")),
            "arquitetura":      props.get("ro.product.cpu.abi", "N/A"),
            "hardware":         props.get("ro.hardware", "N/A"),
        }

        for k, v in info.items():
            print_result(k.replace("_", " ").capitalize(), v)
        return info

    def _get_kernel(self):
        out, _ = self.adb_shell("uname -r")
        return out.strip() if out else "N/A"

    def _get_serial(self, props):
        serial = props.get("ro.serialno", "")
        if not serial:
            out, _ = self.adb("get-serialno")
            serial = out.strip()
        return serial or "N/A"

    def _get_imei(self):
        out, _ = self.adb_shell("service call iphonesubinfo 1 | toybox cut -d \"'\" -f2 | toybox grep -Eo '[0-9]' | toybox xargs | toybox sed 's/ //g'")
        if out and re.match(r'\d{14,17}', out.strip()):
            return out.strip()
        # Fallback via dumpsys
        out2, _ = self.adb_shell("dumpsys iphonesubinfo")
        m = re.search(r'Device ID = (\d+)', out2)
        return m.group(1) if m else "N/A (permissão necessária)"

    def _get_uptime(self):
        out, _ = self.adb_shell("uptime -p")
        if not out:
            out, _ = self.adb_shell("cat /proc/uptime")
            if out:
                secs = float(out.split()[0])
                h, m = int(secs // 3600), int((secs % 3600) // 60)
                return f"{h}h {m}min"
        return out.strip() if out else "N/A"

    # ─── MÓDULO: APPS ────────────────────────────────────────────────────────────
    def module_apps(self):
        print_module_header("Aplicativos Instalados", "📦")

        def get_pkg_list(flag):
            out, _ = self.adb_shell(f"pm list packages {flag}")
            return sorted([l.replace("package:", "").strip() for l in out.splitlines() if l.startswith("package:")])

        user_apps = get_pkg_list("-3")
        system_apps = get_pkg_list("-s")
        disabled_apps = get_pkg_list("-d")

        print_result("Apps de usuário", len(user_apps))
        print_result("Apps de sistema", len(system_apps))
        print_result("Apps desabilitados", len(disabled_apps))

        # Detecta apps suspeitos (sideload / fontes desconhecidas)
        suspicious_patterns = [
            "hack", "spy", "tracker", "keylog", "monitor", "stalker",
            "crack", "cheat", "sniff", "intercept"
        ]
        suspicious = [a for a in user_apps if any(p in a.lower() for p in suspicious_patterns)]
        if suspicious:
            print_warning(f"Apps potencialmente suspeitos detectados: {len(suspicious)}")
            for s in suspicious:
                print(f"    ⚠ {s}")

        # Versões dos apps de usuário
        app_details = []
        for pkg in user_apps[:100]:  # Limita a 100 para performance
            ver_out, _ = self.adb_shell(f"dumpsys package {pkg} | grep versionName")
            ver = "N/A"
            for line in ver_out.splitlines():
                m = re.search(r'versionName=(.+)', line)
                if m:
                    ver = m.group(1).strip()
                    break
            app_details.append({"pacote": pkg, "versão": ver})

        print_table(["Pacote", "Versão"], [[a["pacote"], a["versão"]] for a in app_details])

        return {
            "total_usuario": len(user_apps),
            "total_sistema": len(system_apps),
            "total_desabilitados": len(disabled_apps),
            "apps_usuario": user_apps,
            "apps_desabilitados": disabled_apps,
            "apps_suspeitos": suspicious,
            "detalhes": app_details,
        }

    # ─── MÓDULO: PERMISSÕES ──────────────────────────────────────────────────────
    def module_permissions(self):
        print_module_header("Permissões Perigosas", "🔐")

        DANGEROUS_PERMS = [
            "android.permission.READ_CONTACTS",
            "android.permission.WRITE_CONTACTS",
            "android.permission.READ_CALL_LOG",
            "android.permission.WRITE_CALL_LOG",
            "android.permission.CALL_PHONE",
            "android.permission.READ_SMS",
            "android.permission.SEND_SMS",
            "android.permission.RECEIVE_SMS",
            "android.permission.RECORD_AUDIO",
            "android.permission.CAMERA",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.ACCESS_COARSE_LOCATION",
            "android.permission.ACCESS_BACKGROUND_LOCATION",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
            "android.permission.READ_PHONE_STATE",
            "android.permission.PROCESS_OUTGOING_CALLS",
            "android.permission.BODY_SENSORS",
            "android.permission.USE_BIOMETRIC",
            "android.permission.GET_ACCOUNTS",
        ]

        out, _ = self.adb_shell("pm list packages -3")
        user_pkgs = [l.replace("package:", "").strip() for l in out.splitlines() if l.startswith("package:")]

        perm_map = []
        for pkg in user_pkgs:
            dump_out, _ = self.adb_shell(f"dumpsys package {pkg}")
            granted = []
            in_grants = False
            for line in dump_out.splitlines():
                if "granted=true" in line:
                    for perm in DANGEROUS_PERMS:
                        if perm in line:
                            short = perm.replace("android.permission.", "")
                            granted.append(short)
            if granted:
                perm_map.append({"app": pkg, "permissões": ", ".join(granted), "total": len(granted)})

        perm_map.sort(key=lambda x: x["total"], reverse=True)

        print_result("Apps com permissões perigosas", len(perm_map))
        print_table(["App", "Permissões", "Total"], [[p["app"], p["permissões"][:60], p["total"]] for p in perm_map[:30]])

        return {"apps_com_permissoes_perigosas": len(perm_map), "detalhes": perm_map}

    # ─── MÓDULO: SEGURANÇA ───────────────────────────────────────────────────────
    def module_security(self):
        print_module_header("Status de Segurança", "🛡️")

        def get_setting(ns, key):
            out, _ = self.adb_shell(f"settings get {ns} {key}")
            return out.strip() if out else "N/A"

        # Criptografia
        enc_out, _ = self.adb_shell("getprop ro.crypto.state")
        encrypted = enc_out.strip().lower() == "encrypted"

        # Tipo de bloqueio de tela
        lock_type_map = {"0": "Nenhum", "1": "Swipe", "2": "Senha/PIN", "3": "PIN", "4": "Padrão", "6": "Biometria"}
        lock_raw = get_setting("secure", "lockscreen.password_type")
        lock_type = lock_type_map.get(lock_raw, f"Tipo {lock_raw}")

        # USB Debugging
        usb_debug = get_setting("global", "adb_enabled") == "1"

        # Fontes desconhecidas (Android < 8)
        unknown_src = get_setting("secure", "install_non_market_apps") == "1"

        # Modo desenvolvedor
        dev_mode = get_setting("global", "development_settings_enabled") == "1"

        # Verificação de apps (Play Protect)
        verify_apps = get_setting("global", "package_verifier_enable") == "1"

        # Root check
        rooted = self._check_root()

        # SELinux
        selinux_out, _ = self.adb_shell("getenforce")
        selinux = selinux_out.strip() if selinux_out else "N/A"

        # Depuração por rede
        wifi_debug = get_setting("global", "adb_wifi_enabled") == "1"

        # Tela sempre ligada carregando
        stay_on = get_setting("global", "stay_on_while_plugged_in")

        # Permissão de acessibilidade
        access_svcs_out, _ = self.adb_shell("settings get secure enabled_accessibility_services")
        access_svcs = [s.strip() for s in access_svcs_out.split(":") if s.strip() and s != "null"] if access_svcs_out and access_svcs_out != "null" else []

        # Administradores de dispositivo ativos
        admin_out, _ = self.adb_shell("dumpsys device_policy")
        admins = []
        for line in admin_out.splitlines():
            if "mAdminList" in line or "ComponentInfo" in line:
                m = re.search(r'ComponentInfo\{(.+?)\}', line)
                if m:
                    admins.append(m.group(1))

        security = {
            "criptografado":         encrypted,
            "tipo_bloqueio_tela":    lock_type,
            "usb_debugging":         usb_debug,
            "fontes_desconhecidas":  unknown_src,
            "modo_desenvolvedor":    dev_mode,
            "verificacao_apps":      verify_apps,
            "rooted":                rooted,
            "selinux":               selinux,
            "debug_wifi_ativo":      wifi_debug,
            "servicos_acessibilidade": access_svcs,
            "admins_dispositivo":    admins,
        }

        print_result("Criptografado", encrypted)
        print_result("Tipo de bloqueio", lock_type)
        print_result("USB Debugging", f"{'⚠ ATIVO' if usb_debug else 'Desativado'}")
        print_result("Fontes desconhecidas", f"{'⚠ ATIVO' if unknown_src else 'Desativado'}")
        print_result("Modo desenvolvedor", f"{'⚠ ATIVO' if dev_mode else 'Desativado'}")
        print_result("Play Protect", f"{'✓ Ativo' if verify_apps else '⚠ Inativo'}")
        print_result("Root/Superusuário", f"{'⚠ DETECTADO' if rooted else 'Não detectado'}")
        print_result("SELinux", selinux)
        print_result("Serviços de acessibilidade", len(access_svcs))
        print_result("Admins de dispositivo", len(admins))

        return security

    def _check_root(self):
        indicators = [
            "which su",
            "ls /system/bin/su",
            "ls /system/xbin/su",
            "ls /sbin/su",
            "ls /data/local/xbin/su",
            "ls /data/local/bin/su",
        ]
        for cmd in indicators:
            out, code = self.adb_shell(cmd)
            if out.strip() and "No such" not in out and code == 0:
                return True

        # Verifica apps de root conhecidos
        root_apps = ["com.topjohnwu.magisk", "com.koushikdutta.superuser",
                     "eu.chainfire.supersu", "com.noshufou.android.su"]
        out, _ = self.adb_shell("pm list packages")
        for app in root_apps:
            if app in out:
                return True
        return False

    # ─── MÓDULO: REDE ────────────────────────────────────────────────────────────
    def module_network(self):
        print_module_header("Informações de Rede", "🌐")

        # WiFi
        wifi_out, _ = self.adb_shell("dumpsys wifi")
        ssid, bssid, ip_wifi, freq, signal = "N/A", "N/A", "N/A", "N/A", "N/A"

        for line in wifi_out.splitlines():
            if "mWifiInfo" in line or "WifiInfo" in line:
                m = re.search(r'SSID: (.+?),', line)
                if m: ssid = m.group(1).strip().strip('"')
                m = re.search(r'BSSID: ([\w:]+)', line)
                if m: bssid = m.group(1)
                m = re.search(r'IP address: ([\d.]+)', line)
                if m: ip_wifi = m.group(1)
                m = re.search(r'Frequency: (\d+)', line)
                if m: freq = f"{m.group(1)} MHz"
                m = re.search(r'RSSI: (-?\d+)', line)
                if m: signal = f"{m.group(1)} dBm"

        # Interfaces de rede
        ip_out, _ = self.adb_shell("ip addr show")
        interfaces = self._parse_ip_addr(ip_out)

        # MAC WiFi
        mac_out, _ = self.adb_shell("cat /sys/class/net/wlan0/address")
        mac_wifi = mac_out.strip() if mac_out else "N/A"

        # DNS
        dns1, _ = self.adb_shell("getprop net.dns1")
        dns2, _ = self.adb_shell("getprop net.dns2")

        # Proxy
        proxy_host, _ = self.adb_shell("settings get global http_proxy")
        proxy = proxy_host.strip() if proxy_host and proxy_host.strip() != "null" else "Nenhum"

        # Dados móveis
        mobile_data, _ = self.adb_shell("settings get global mobile_data")
        airplane_mode, _ = self.adb_shell("settings get global airplane_mode_on")

        # Roaming
        roaming_out, _ = self.adb_shell("getprop gsm.network.type")

        # Operadora
        carrier_out, _ = self.adb_shell("getprop gsm.operator.alpha")

        # Conexões de rede ativas
        netstat_out, _ = self.adb_shell("cat /proc/net/tcp")
        active_conns = self._parse_tcp_connections(netstat_out)

        network = {
            "wifi": {
                "ssid": ssid,
                "bssid": bssid,
                "ip": ip_wifi,
                "mac": mac_wifi,
                "frequencia": freq,
                "sinal": signal,
            },
            "dns_primario":     dns1.strip() if dns1 else "N/A",
            "dns_secundario":   dns2.strip() if dns2 else "N/A",
            "proxy":            proxy,
            "dados_moveis":     mobile_data.strip() == "1" if mobile_data else False,
            "modo_aviao":       airplane_mode.strip() == "1" if airplane_mode else False,
            "operadora":        carrier_out.strip() if carrier_out else "N/A",
            "interfaces":       interfaces,
            "conexoes_tcp_ativas": len(active_conns),
        }

        print_result("SSID", ssid)
        print_result("IP WiFi", ip_wifi)
        print_result("MAC WiFi", mac_wifi)
        print_result("DNS Primário", dns1.strip() if dns1 else "N/A")
        print_result("Proxy", proxy)
        print_result("Modo avião", airplane_mode.strip() == "1")
        print_result("Operadora", carrier_out.strip() if carrier_out else "N/A")
        print_result("Conexões TCP ativas", len(active_conns))

        return network

    def _parse_ip_addr(self, output):
        interfaces = []
        current = None
        for line in output.splitlines():
            m = re.match(r'^\d+: (\w+):', line)
            if m:
                current = {"nome": m.group(1), "ips": []}
                interfaces.append(current)
            elif current and "inet " in line:
                m2 = re.search(r'inet ([\d.]+/\d+)', line)
                if m2:
                    current["ips"].append(m2.group(1))
        return interfaces

    def _parse_tcp_connections(self, output):
        conns = []
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4 and parts[3] == "01":  # estado ESTABLISHED
                conns.append(parts)
        return conns

    # ─── MÓDULO: ARMAZENAMENTO ───────────────────────────────────────────────────
    def module_storage(self):
        print_module_header("Armazenamento", "💾")

        df_out, _ = self.adb_shell("df -h")
        partitions = []
        for line in df_out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                partitions.append({
                    "sistema_arquivos": parts[0],
                    "tamanho": parts[1],
                    "usado": parts[2],
                    "disponivel": parts[3],
                    "uso_%": parts[4] if len(parts) > 4 else "N/A",
                })

        # Armazenamento interno detalhado via StatFs
        storage_out, _ = self.adb_shell("dumpsys diskstats")
        internal_total, internal_free = "N/A", "N/A"
        for line in storage_out.splitlines():
            if "Data-Free" in line:
                m = re.search(r'Data-Free: (\d+)K', line)
                if m:
                    internal_free = format_bytes(int(m.group(1)) * 1024)
            if "Data-Total" in line or "App" in line:
                m = re.search(r'(\d+)K', line)
                if m:
                    internal_total = format_bytes(int(m.group(1)) * 1024)

        # SD Card
        sdcard_out, _ = self.adb_shell("df /sdcard")
        sdcard = "N/A"
        for line in sdcard_out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                sdcard = f"{parts[1]} total, {parts[3]} disponível"

        # Apps por tamanho
        storage = {
            "particoes": partitions,
            "armazenamento_interno": internal_total,
            "espaco_livre_interno": internal_free,
            "sdcard": sdcard,
        }

        print_table(
            ["Partição", "Tamanho", "Usado", "Disponível", "Uso%"],
            [[p["sistema_arquivos"], p["tamanho"], p["usado"], p["disponivel"], p["uso_%"]] for p in partitions]
        )

        return storage

    # ─── MÓDULO: BATERIA ─────────────────────────────────────────────────────────
    def module_battery(self):
        print_module_header("Status da Bateria", "🔋")

        out, _ = self.adb_shell("dumpsys battery")
        battery = {}
        for line in out.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                battery[key.strip()] = val.strip()

        result = {
            "nivel_%":          battery.get("level", "N/A"),
            "status":           {
                "1": "Desconhecido", "2": "Carregando",
                "3": "Descarregando", "4": "Sem carga", "5": "Cheio"
            }.get(battery.get("status", ""), battery.get("status", "N/A")),
            "saude":            {
                "1": "Desconhecido", "2": "Bom", "3": "Superaquecido",
                "4": "Morto", "5": "Sobretensão", "6": "Falha",
                "7": "Frio"
            }.get(battery.get("health", ""), battery.get("health", "N/A")),
            "plugado":          battery.get("AC powered", "N/A"),
            "carregamento_usb": battery.get("USB powered", "N/A"),
            "temperatura_c":    f"{int(battery.get('temperature', 0)) / 10:.1f}°C" if battery.get("temperature", "").isdigit() else "N/A",
            "voltagem_mv":      battery.get("voltage", "N/A"),
            "tecnologia":       battery.get("technology", "N/A"),
        }

        for k, v in result.items():
            print_result(k.replace("_", " ").capitalize(), str(v))
        return result

    # ─── MÓDULO: PROCESSOS ───────────────────────────────────────────────────────
    def module_processes(self):
        print_module_header("Processos em Execução", "⚙️")

        out, _ = self.adb_shell("ps -A")
        processes = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 9:
                processes.append({
                    "pid":    parts[1],
                    "ppid":   parts[2],
                    "user":   parts[0],
                    "estado": parts[7],
                    "nome":   parts[-1],
                })

        # Serviços Android ativos
        svc_out, _ = self.adb_shell("service list")
        services = []
        for line in svc_out.splitlines():
            m = re.match(r'\s*\d+\s+(\w[\w.]+):', line)
            if m:
                services.append(m.group(1))

        print_result("Total de processos", len(processes))
        print_result("Serviços registrados", len(services))

        # Processos mais relevantes (não-sistema)
        user_procs = [p for p in processes if "." in p["nome"] and not p["nome"].startswith("/")] [:30]
        print_table(["PID", "User", "Estado", "Nome"], [[p["pid"], p["user"], p["estado"], p["nome"]] for p in user_procs])

        return {
            "total_processos": len(processes),
            "total_servicos": len(services),
            "processos": processes[:100],
            "servicos": services[:50],
        }

    # ─── MÓDULO: CONTAS ──────────────────────────────────────────────────────────
    def module_accounts(self):
        print_module_header("Contas Sincronizadas", "👤")

        out, _ = self.adb_shell("dumpsys account")
        accounts = []
        for line in out.splitlines():
            m = re.search(r'Account \{name=(.+?), type=(.+?)\}', line)
            if m:
                accounts.append({"nome": m.group(1), "tipo": m.group(2)})

        print_result("Total de contas", len(accounts))
        print_table(["Nome da Conta", "Tipo"], [[a["nome"], a["tipo"]] for a in accounts])
        return {"total": len(accounts), "contas": accounts}

    # ─── MÓDULO: BLUETOOTH ───────────────────────────────────────────────────────
    def module_bluetooth(self):
        print_module_header("Bluetooth", "🔵")

        out, _ = self.adb_shell("dumpsys bluetooth_manager")
        devices = []
        bt_enabled = False
        bt_name = "N/A"
        bt_addr = "N/A"

        for line in out.splitlines():
            if "enabled: true" in line.lower() or "mState=STATE_ON" in line:
                bt_enabled = True
            if "mName" in line:
                m = re.search(r'mName=(.+)', line)
                if m: bt_name = m.group(1).strip()
            if "mAddress" in line:
                m = re.search(r'mAddress=([\w:]+)', line)
                if m: bt_addr = m.group(1).strip()
            # Dispositivos pareados
            m = re.search(r'name: (.+), address: ([\w:]+)', line)
            if m:
                devices.append({"nome": m.group(1), "mac": m.group(2)})

        result = {
            "ativo":              bt_enabled,
            "nome_dispositivo":   bt_name,
            "mac_bluetooth":      bt_addr,
            "dispositivos_pareados": len(devices),
            "pareados":           devices,
        }

        print_result("Bluetooth ativo", bt_enabled)
        print_result("Nome do device", bt_name)
        print_result("Endereço MAC BT", bt_addr)
        print_result("Dispositivos pareados", len(devices))
        if devices:
            print_table(["Nome", "MAC"], [[d["nome"], d["mac"]] for d in devices])

        return result

    # ─── MÓDULO: BACKUP ──────────────────────────────────────────────────────────
    def module_backup(self):
        print_module_header("Configurações de Backup", "☁️")

        auto_restore = self.adb_shell("settings get secure backup_auto_restore")[0].strip()
        backup_enabled = self.adb_shell("settings get global backup_enabled")[0].strip()
        backup_transport = self.adb_shell("settings get secure backup_transport")[0].strip()

        # Google Account de backup
        backup_account = "N/A"
        out, _ = self.adb_shell("dumpsys backup")
        for line in out.splitlines():
            if "Current transport" in line or "backupAccount" in line:
                backup_account = line.strip()
                break

        result = {
            "backup_habilitado":  backup_enabled == "1",
            "restauracao_auto":   auto_restore == "1",
            "transporte_backup":  backup_transport if backup_transport and backup_transport != "null" else "N/A",
            "conta_backup":       backup_account,
        }

        for k, v in result.items():
            print_result(k.replace("_", " ").capitalize(), v)
        return result
