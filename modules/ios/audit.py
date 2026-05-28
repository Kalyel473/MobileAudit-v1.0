#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modules/ios/audit.py — Módulos de Auditoria iOS
Requer: libimobiledevice + pymobiledevice3 (pip install pymobiledevice3)
O dispositivo deve estar conectado, desbloqueado e você deve ter tocado 'Confiar'
"""

import re
import json
import shutil
import subprocess
from datetime import datetime
from core.utils import (
    print_info, print_success, print_error, print_warning,
    print_module_header, print_result, print_table, run_command, format_bytes
)

# Tenta importar pymobiledevice3 (opcional, mais completo)
try:
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.installation_proxy import InstallationProxyService
    from pymobiledevice3.services.diagnostics import DiagnosticsService
    from pymobiledevice3.services.springboard import SpringBoardServicesService
    from pymobiledevice3.services.mobile_config import MobileConfigService
    HAS_PYMOBILE = True
except ImportError:
    HAS_PYMOBILE = False


class iOSAudit:
    def __init__(self, quiet=False):
        self.quiet = quiet
        self.lockdown = None
        self.udid = None

    # ─── HELPERS ────────────────────────────────────────────────────────────────
    def _idev(self, *args, timeout=30):
        """Executa comando idevice* e retorna saída."""
        cmd = list(args)
        if self.udid:
            # Insere -u UDID como segundo argumento (após o comando)
            cmd = [cmd[0], "-u", self.udid] + cmd[1:]
        return run_command(cmd, timeout=timeout)

    def _ideviceinfo(self, key=None, domain=None):
        args = ["ideviceinfo"]
        if domain:
            args += ["-q", domain]
        if key:
            args += ["-k", key]
        out, code = self._idev(*args)
        return out.strip() if code == 0 else "N/A"

    # ─── CONEXÃO ────────────────────────────────────────────────────────────────
    def connect(self):
        if not shutil.which("ideviceinfo"):
            print_error("libimobiledevice não encontrado.")
            print_warning("Instale: sudo apt install libimobiledevice-utils ideviceinstaller")
            if HAS_PYMOBILE:
                print_info("Tentando via pymobiledevice3...")
            else:
                return False

        # Lista devices conectados
        out, code = run_command(["idevice_id", "-l"])
        if code != 0 or not out.strip():
            # Tenta ideviceinfo direto
            test_out, test_code = run_command(["ideviceinfo", "-k", "DeviceName"])
            if test_code != 0:
                return False
        else:
            devices = [d.strip() for d in out.splitlines() if d.strip()]
            if not devices:
                return False
            self.udid = devices[0]
            if len(devices) > 1:
                print_warning(f"{len(devices)} dispositivos iOS conectados. Usando: {self.udid}")
            else:
                print_success(f"Dispositivo iOS conectado: {self.udid}")

        # Tenta pymobiledevice3
        if HAS_PYMOBILE:
            try:
                self.lockdown = create_using_usbmux(serial=self.udid)
                print_success("Conexão via pymobiledevice3 estabelecida.")
            except Exception as e:
                print_warning(f"pymobiledevice3 indisponível: {e}. Usando idevice CLI.")

        return True

    # ─── DISPATCHER ─────────────────────────────────────────────────────────────
    def run_modules(self, modules):
        results = {"_meta": {"platform": "ios", "timestamp": datetime.now().isoformat()}}
        module_map = {
            "info":     self.module_info,
            "apps":     self.module_apps,
            "battery":  self.module_battery,
            "storage":  self.module_storage,
            "network":  self.module_network,
            "security": self.module_security,
            "profiles": self.module_profiles,
            "backup":   self.module_backup,
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
        print_module_header("Informações do Dispositivo iOS", "📱")

        fields = {
            "DeviceName":           "nome_dispositivo",
            "ProductType":          "modelo_interno",
            "ProductVersion":       "ios_versao",
            "BuildVersion":         "build",
            "UniqueDeviceID":       "udid",
            "SerialNumber":         "serial",
            "HardwareModel":        "hardware_model",
            "CPUArchitecture":      "arquitetura_cpu",
            "DeviceColor":          "cor",
            "ModelNumber":          "numero_modelo",
            "RegionInfo":           "regiao",
            "WiFiAddress":          "mac_wifi",
            "BluetoothAddress":     "mac_bluetooth",
            "PhoneNumber":          "numero_telefone",
            "InternationalMobileEquipmentIdentity": "imei",
            "MobileEquipmentIdentifier": "meid",
            "SIMStatus":            "status_sim",
            "ActivationState":      "estado_ativacao",
            "IntegratedCircuitCardIdentity": "iccid",
            "TimeZone":             "fuso_horario",
            "TimeIntervalSince1970": "hora_unix",
        }

        info = {}
        for idev_key, friendly in fields.items():
            val = self._ideviceinfo(key=idev_key)
            info[friendly] = val

        # Versão legível do modelo
        info["modelo_legivel"] = self._model_to_name(info.get("modelo_interno", ""))

        # Uptime via diagnóstico
        if HAS_PYMOBILE and self.lockdown:
            try:
                diag = DiagnosticsService(self.lockdown)
                diag_info = diag.info()
                info["uptime_s"] = diag_info.get("IORegistry", {}).get("IOKitDiagnostics", {})
            except Exception:
                pass

        for k, v in info.items():
            if v and v != "N/A":
                print_result(k.replace("_", " ").capitalize(), str(v))

        return info

    def _model_to_name(self, model_id):
        MODEL_MAP = {
            "iPhone14,2": "iPhone 13 Pro", "iPhone14,3": "iPhone 13 Pro Max",
            "iPhone14,4": "iPhone 13 mini", "iPhone14,5": "iPhone 13",
            "iPhone15,2": "iPhone 14 Pro", "iPhone15,3": "iPhone 14 Pro Max",
            "iPhone14,7": "iPhone 14", "iPhone14,8": "iPhone 14 Plus",
            "iPhone16,1": "iPhone 15 Pro", "iPhone16,2": "iPhone 15 Pro Max",
            "iPhone15,4": "iPhone 15", "iPhone15,5": "iPhone 15 Plus",
            "iPhone17,1": "iPhone 16 Pro", "iPhone17,2": "iPhone 16 Pro Max",
            "iPhone17,3": "iPhone 16", "iPhone17,4": "iPhone 16 Plus",
            "iPad13,1":  "iPad Air (4ª geração)", "iPad13,2": "iPad Air (4ª geração)",
            "iPad14,1":  "iPad mini (6ª geração)", "iPad14,2": "iPad mini (6ª geração)",
        }
        return MODEL_MAP.get(model_id, model_id or "N/A")

    # ─── MÓDULO: APPS ────────────────────────────────────────────────────────────
    def module_apps(self):
        print_module_header("Aplicativos Instalados", "📦")

        apps = []

        # Método 1: ideviceinstaller
        if shutil.which("ideviceinstaller"):
            out, code = self._idev("ideviceinstaller", "-l")
            if code == 0:
                for line in out.splitlines():
                    line = line.strip()
                    if line and not line.startswith("Total"):
                        parts = line.split(",", 2)
                        if len(parts) >= 2:
                            bundle_id = parts[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else "N/A"
                            name = parts[2].strip().strip('"') if len(parts) > 2 else bundle_id
                            apps.append({"nome": name, "bundle_id": bundle_id, "versao": version})

        # Método 2: pymobiledevice3
        if not apps and HAS_PYMOBILE and self.lockdown:
            try:
                proxy = InstallationProxyService(self.lockdown)
                app_list = proxy.get_apps(application_type="User")
                for bundle_id, app_info in app_list.items():
                    apps.append({
                        "nome": app_info.get("CFBundleDisplayName", app_info.get("CFBundleName", bundle_id)),
                        "bundle_id": bundle_id,
                        "versao": app_info.get("CFBundleShortVersionString", "N/A"),
                    })
            except Exception as e:
                print_warning(f"pymobiledevice3 apps: {e}")

        print_result("Total de apps de usuário", len(apps))

        # Detecta apps potencialmente suspeitos
        suspicious_patterns = ["spy", "track", "monitor", "keylog", "intercept", "hack"]
        suspicious = [a for a in apps if any(p in a["nome"].lower() or p in a["bundle_id"].lower() for p in suspicious_patterns)]
        if suspicious:
            print_warning(f"Apps suspeitos: {len(suspicious)}")

        print_table(
            ["Nome", "Bundle ID", "Versão"],
            [[a["nome"], a["bundle_id"], a["versao"]] for a in apps]
        )

        return {
            "total": len(apps),
            "apps_suspeitos": suspicious,
            "apps": apps
        }

    # ─── MÓDULO: BATERIA ─────────────────────────────────────────────────────────
    def module_battery(self):
        print_module_header("Status da Bateria", "🔋")

        battery = {}

        # Via idevicediagnostics
        if shutil.which("idevicediagnostics"):
            out, code = self._idev("idevicediagnostics", "diagnostics", "IORegistry", "--plain")
            if code == 0:
                # Parse plist-like output
                for line in out.splitlines():
                    for key in ["BatteryCurrentCapacity", "BatteryIsCharging",
                                "ExternalChargeCapable", "FullyCharged",
                                "BatteryVoltage", "Temperature",
                                "MaximumFCC", "NominalChargeCapacity"]:
                        if key in line:
                            m = re.search(rf'{key}\s*=\s*([^\n;]+)', line)
                            if m:
                                battery[key] = m.group(1).strip()

        # Via pymobiledevice3
        if HAS_PYMOBILE and self.lockdown:
            try:
                diag = DiagnosticsService(self.lockdown)
                ioreg = diag.ioregistry(plane="IODeviceTree")
                if isinstance(ioreg, dict):
                    batt = ioreg.get("IOPMBattery", {})
                    battery.update({
                        "nivel_%": batt.get("CurrentCapacity", "N/A"),
                        "capacidade_maxima": batt.get("MaxCapacity", "N/A"),
                        "carregando": batt.get("IsCharging", "N/A"),
                        "totalmente_carregado": batt.get("FullyCharged", "N/A"),
                        "temperatura_c": f"{float(batt.get('Temperature', 0)) / 100:.1f}°C" if batt.get("Temperature") else "N/A",
                        "voltagem_mv": batt.get("Voltage", "N/A"),
                        "ciclos_carga": batt.get("CycleCount", "N/A"),
                        "saude_%": f"{(int(batt.get('MaxCapacity', 0)) / max(int(batt.get('DesignCapacity', 1)), 1) * 100):.1f}%" if batt.get("MaxCapacity") and batt.get("DesignCapacity") else "N/A",
                    })
            except Exception as e:
                print_warning(f"pymobiledevice3 battery: {e}")

        # Fallback: ideviceinfo
        if not battery:
            fields = {
                "BatteryCurrentCapacity": "nivel_%",
                "BatteryIsCharging": "carregando",
                "FullyCharged": "totalmente_carregado",
            }
            for key, friendly in fields.items():
                battery[friendly] = self._ideviceinfo(key=key, domain="com.apple.mobile.battery")

        result = battery if battery else {"status": "Dados de bateria não disponíveis"}

        for k, v in result.items():
            print_result(k.replace("_", " ").capitalize(), str(v))
        return result

    # ─── MÓDULO: ARMAZENAMENTO ───────────────────────────────────────────────────
    def module_storage(self):
        print_module_header("Armazenamento", "💾")

        storage = {}

        # ideviceinfo storage domain
        fields = {
            "TotalDiskCapacity": "capacidade_total",
            "TotalDataCapacity": "capacidade_dados",
            "TotalDataAvailable": "espaco_disponivel",
            "TotalSystemCapacity": "capacidade_sistema",
            "TotalSystemAvailable": "sistema_disponivel",
        }
        for key, friendly in fields.items():
            raw = self._ideviceinfo(key=key)
            if raw and raw != "N/A":
                try:
                    storage[friendly] = format_bytes(int(raw))
                except ValueError:
                    storage[friendly] = raw
            else:
                storage[friendly] = "N/A"

        # Calcula uso
        try:
            total = int(self._ideviceinfo(key="TotalDataCapacity") or 0)
            avail = int(self._ideviceinfo(key="TotalDataAvailable") or 0)
            if total > 0:
                used = total - avail
                storage["espaco_usado"] = format_bytes(used)
                storage["porcentagem_uso"] = f"{(used / total * 100):.1f}%"
        except Exception:
            pass

        for k, v in storage.items():
            print_result(k.replace("_", " ").capitalize(), str(v))
        return storage

    # ─── MÓDULO: REDE ────────────────────────────────────────────────────────────
    def module_network(self):
        print_module_header("Informações de Rede", "🌐")

        network = {}

        # MAC WiFi e Bluetooth
        network["mac_wifi"] = self._ideviceinfo(key="WiFiAddress")
        network["mac_bluetooth"] = self._ideviceinfo(key="BluetoothAddress")
        network["imei"] = self._ideviceinfo(key="InternationalMobileEquipmentIdentity")
        network["numero_telefone"] = self._ideviceinfo(key="PhoneNumber")
        network["status_sim"] = self._ideviceinfo(key="SIMStatus")
        network["iccid"] = self._ideviceinfo(key="IntegratedCircuitCardIdentity")

        # Via pymobiledevice3 — diagnósticos de rede
        if HAS_PYMOBILE and self.lockdown:
            try:
                diag = DiagnosticsService(self.lockdown)
                net_info = diag.ioregistry(name="AppleBCMWLAN")
                if isinstance(net_info, dict):
                    network["ssid_atual"] = net_info.get("SSID_STR", "N/A")
                    network["bssid"] = net_info.get("BSSID", "N/A")
                    network["rssi"] = f"{net_info.get('RSSI', 'N/A')} dBm"
                    network["canal_wifi"] = net_info.get("Channel", "N/A")
            except Exception:
                pass

        for k, v in network.items():
            print_result(k.replace("_", " ").capitalize(), str(v))
        return network

    # ─── MÓDULO: SEGURANÇA ───────────────────────────────────────────────────────
    def module_security(self):
        print_module_header("Status de Segurança", "🛡️")

        security = {}

        # Detecção de Jailbreak (indicadores comuns)
        jailbreak_indicators = self._check_jailbreak()
        security["jailbreak_detectado"] = len(jailbreak_indicators) > 0
        security["indicadores_jailbreak"] = jailbreak_indicators

        # Estado de ativação
        security["estado_ativacao"] = self._ideviceinfo(key="ActivationState")

        # Modo de supervisão (MDM)
        supervised = self._ideviceinfo(key="IsSupervised")
        security["supervisionado_mdm"] = supervised.lower() == "true" if supervised else False

        # Código de passe ativo
        passcode = self._ideviceinfo(key="PasswordProtected")
        security["senha_ativa"] = passcode.lower() == "true" if passcode else "N/A"

        # Versão iOS e data do patch de segurança
        security["ios_versao"] = self._ideviceinfo(key="ProductVersion")
        security["numero_build"] = self._ideviceinfo(key="BuildVersion")

        # Verificação de atualização disponível (requer internet)
        security["face_id_touch_id"] = self._check_biometrics()

        # Certificados confiáveis
        if HAS_PYMOBILE and self.lockdown:
            try:
                from pymobiledevice3.services.mobile_config import MobileConfigService
                mc = MobileConfigService(self.lockdown)
                certs = mc.get_profile_list()
                security["perfis_instalados"] = len(certs.get("ProfileList", []))
            except Exception:
                security["perfis_instalados"] = "N/A"

        # Encontrar apps com acesso à câmera/microfone via privacidade
        security["observacoes"] = [
            "iOS não expõe configurações de privacidade de apps via ADB/idevice diretamente.",
            "Para auditoria completa de permissões, acesse: Ajustes > Privacidade e Segurança.",
            "Verifique manualmente: Localização, Câmera, Microfone, Contatos.",
        ]

        print_result("Jailbreak detectado", security["jailbreak_detectado"])
        if jailbreak_indicators:
            print_warning(f"Indicadores: {', '.join(jailbreak_indicators)}")
        print_result("Supervisionado/MDM", security["supervisionado_mdm"])
        print_result("Senha ativa", security["senha_ativa"])
        print_result("iOS Versão", security["ios_versao"])

        return security

    def _check_jailbreak(self):
        """Detecta indicadores de jailbreak via app list e ideviceinfo."""
        indicators = []

        jailbreak_bundle_ids = [
            "com.saurik.Cydia", "com.saurik.cydia",
            "org.coolstar.SileoStore", "net.mtac.filzalite",
            "io.palera.palera1n", "com.opa334.trollstore",
            "com.opa334.trollstoreinstaller", "com.tigisoftware.Filza",
            "com.iMast8.sbmanager", "org.tac.absinthe",
        ]

        # Verifica apps de jailbreak instalados
        if shutil.which("ideviceinstaller"):
            out, _ = self._idev("ideviceinstaller", "-l")
            for bid in jailbreak_bundle_ids:
                if bid.lower() in out.lower():
                    indicators.append(f"App: {bid}")

        # Verifica via pymobiledevice3
        if HAS_PYMOBILE and self.lockdown:
            try:
                proxy = InstallationProxyService(self.lockdown)
                all_apps = proxy.get_apps()
                for bid in jailbreak_bundle_ids:
                    if bid in all_apps:
                        indicators.append(f"App instalado: {bid}")
            except Exception:
                pass

        return indicators

    def _check_biometrics(self):
        """Verifica suporte a Face ID / Touch ID."""
        model = self._ideviceinfo(key="ProductType")
        if not model or model == "N/A":
            return "N/A"
        # iPhones com Face ID: X em diante (iPhone10,3 = iPhone X)
        m = re.match(r'iPhone(\d+),', model)
        if m and int(m.group(1)) >= 10:
            return "Face ID"
        elif m and int(m.group(1)) >= 6:
            return "Touch ID"
        return "N/A"

    # ─── MÓDULO: PERFIS MDM ──────────────────────────────────────────────────────
    def module_profiles(self):
        print_module_header("Perfis de Configuração MDM", "📋")

        profiles = []

        if HAS_PYMOBILE and self.lockdown:
            try:
                mc = MobileConfigService(self.lockdown)
                profile_list = mc.get_profile_list()
                raw_profiles = profile_list.get("ProfileList", [])
                for p in raw_profiles:
                    profiles.append({
                        "nome":         p.get("PayloadDisplayName", "N/A"),
                        "organizacao":  p.get("PayloadOrganization", "N/A"),
                        "descricao":    p.get("PayloadDescription", "N/A"),
                        "uuid":         p.get("PayloadUUID", "N/A"),
                        "versao":       str(p.get("PayloadVersion", "N/A")),
                        "removivel":    str(not p.get("IsManaged", False)),
                    })
            except Exception as e:
                print_warning(f"Perfis via pymobiledevice3: {e}")

        if not profiles:
            print_info("Nenhum perfil detectado ou idevice CLI não suporta listagem de perfis.")
            print_warning("Para ver perfis manualmente: Ajustes > Geral > VPN e Gerenciamento de Dispositivos")
            return {"total": 0, "perfis": [], "nota": "Verificação manual recomendada em Ajustes > Geral > VPN e Gerenciamento de Dispositivos"}

        print_result("Total de perfis instalados", len(profiles))
        if profiles:
            print_table(
                ["Nome", "Organização", "UUID", "Removível"],
                [[p["nome"], p["organizacao"], p["uuid"][:18] + "...", p["removivel"]] for p in profiles]
            )

        return {"total": len(profiles), "perfis": profiles}

    # ─── MÓDULO: BACKUP ──────────────────────────────────────────────────────────
    def module_backup(self):
        print_module_header("Status de Backup", "☁️")

        import os

        backup = {}

        # iCloud Backup via ideviceinfo
        backup["icloud_backup"] = self._ideviceinfo(key="BackupEnabled")
        backup["data_ultimo_backup"] = self._ideviceinfo(key="LastBackupDate")

        # Backups iTunes/Finder locais
        backup_dirs = []
        possible_backup_dirs = []

        # Linux/macOS
        home = os.path.expanduser("~")
        possible_backup_dirs += [
            os.path.join(home, ".var/app/org.libimobiledevice.MobileBackup2"),
            "/var/lib/lockdown",
            os.path.join(home, "Library/Application Support/MobileSync/Backup"),  # macOS
            os.path.join(home, "AppData/Roaming/Apple Computer/MobileSync/Backup"),  # Windows
        ]

        for d in possible_backup_dirs:
            if os.path.exists(d):
                backup_dirs.append(d)

        if backup_dirs:
            backup["diretorios_backup_local"] = backup_dirs
        else:
            backup["diretorios_backup_local"] = "Nenhum backup local encontrado"

        # Informações do idevicebackup2
        if shutil.which("idevicebackup2"):
            status_out, _ = self._idev("idevicebackup2", "list")
            backup["historico_backups"] = status_out[:500] if status_out else "N/A"

        for k, v in backup.items():
            if k != "historico_backups":
                print_result(k.replace("_", " ").capitalize(), str(v))

        return backup
