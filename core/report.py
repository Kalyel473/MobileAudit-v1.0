#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/report.py — Gerador de Relatórios (JSON, HTML, TXT)
"""

import os
import json
from datetime import datetime
from core.utils import ensure_reports_dir, sanitize_text


class ReportGenerator:
    def __init__(self, results: dict):
        self.results = results
        self.timestamp = datetime.now()
        self.ts_str = self.timestamp.strftime("%Y%m%d_%H%M%S")

    # ─── JSON ────────────────────────────────────────────────────────────────────
    def save_json(self, filepath=None):
        if not filepath:
            filepath = os.path.join(ensure_reports_dir(), f"mobileaudit_{self.ts_str}.json")
        payload = {
            "tool": "MobileAudit v1.0",
            "generated_at": self.timestamp.isoformat(),
            "results": self.results
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        return filepath

    # ─── TXT ─────────────────────────────────────────────────────────────────────
    def save_txt(self, filepath=None):
        if not filepath:
            filepath = os.path.join(ensure_reports_dir(), f"mobileaudit_{self.ts_str}.txt")
        lines = []
        lines.append("=" * 70)
        lines.append("  MobileAudit v1.0 — Relatório de Auditoria")
        lines.append(f"  Gerado em: {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("=" * 70)

        for module, data in self.results.items():
            lines.append(f"\n{'─' * 70}")
            lines.append(f"  MÓDULO: {module.upper()}")
            lines.append(f"{'─' * 70}")
            if isinstance(data, dict):
                self._dict_to_txt(data, lines, indent=2)
            elif isinstance(data, list):
                for item in data:
                    lines.append(f"  • {item}")
            else:
                lines.append(f"  {data}")

        lines.append("\n" + "=" * 70)
        lines.append("  Fim do Relatório")
        lines.append("=" * 70)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath

    def _dict_to_txt(self, d, lines, indent=0):
        spaces = " " * indent
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{spaces}{key}:")
                self._dict_to_txt(value, lines, indent + 2)
            elif isinstance(value, list):
                lines.append(f"{spaces}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            lines.append(f"{spaces}  {k}: {v}")
                        lines.append("")
                    else:
                        lines.append(f"{spaces}  • {item}")
            else:
                lines.append(f"{spaces}{key}: {value}")

    # ─── HTML ────────────────────────────────────────────────────────────────────
    def save_html(self, filepath=None):
        if not filepath:
            filepath = os.path.join(ensure_reports_dir(), f"mobileaudit_{self.ts_str}.html")

        # Informações de cabeçalho
        platform = self.results.get("_meta", {}).get("platform", "Desconhecido")
        device_name = self.results.get("info", {}).get("model", "Dispositivo")

        sections_html = self._build_sections_html()

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MobileAudit — Relatório {self.ts_str}</title>
<style>
  :root {{
    --bg: #0d1117; --surface: #161b22; --surface2: #21262d;
    --border: #30363d; --text: #c9d1d9; --text-muted: #8b949e;
    --accent: #58a6ff; --success: #3fb950; --warning: #d29922;
    --danger: #f85149; --purple: #bc8cff;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }}
  header {{ background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); border-bottom: 1px solid var(--border); padding: 24px 40px; }}
  .logo {{ font-size: 28px; font-weight: 700; color: var(--accent); letter-spacing: -0.5px; }}
  .logo span {{ color: var(--success); }}
  .meta {{ color: var(--text-muted); font-size: 13px; margin-top: 6px; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; margin-left: 8px; }}
  .badge-android {{ background: #3fb95022; color: var(--success); border: 1px solid #3fb95044; }}
  .badge-ios {{ background: #58a6ff22; color: var(--accent); border: 1px solid #58a6ff44; }}
  .warning-bar {{ background: #d2992222; border-left: 3px solid var(--warning); padding: 10px 40px; font-size: 12px; color: var(--warning); }}
  main {{ max-width: 1200px; margin: 0 auto; padding: 30px 40px; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 30px; }}
  .summary-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }}
  .summary-card .label {{ font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; }}
  .summary-card .value {{ font-size: 20px; font-weight: 700; color: var(--accent); margin-top: 4px; }}
  .summary-card .sub {{ font-size: 12px; color: var(--text-muted); margin-top: 2px; }}
  .module {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 20px; overflow: hidden; }}
  .module-header {{ background: var(--surface2); padding: 14px 20px; display: flex; align-items: center; gap: 10px; cursor: pointer; }}
  .module-icon {{ font-size: 18px; }}
  .module-title {{ font-size: 15px; font-weight: 600; color: var(--text); }}
  .module-count {{ margin-left: auto; background: var(--border); border-radius: 20px; padding: 2px 10px; font-size: 12px; color: var(--text-muted); }}
  .module-body {{ padding: 16px 20px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 8px 12px; background: var(--surface2); color: var(--text-muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; color: var(--text); word-break: break-all; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #ffffff08; }}
  .kv-row {{ display: flex; padding: 8px 0; border-bottom: 1px solid #21262d; align-items: flex-start; gap: 16px; }}
  .kv-row:last-child {{ border-bottom: none; }}
  .kv-key {{ min-width: 200px; color: var(--text-muted); font-size: 13px; }}
  .kv-val {{ color: var(--text); font-weight: 500; word-break: break-all; }}
  .tag {{ display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin: 1px; }}
  .tag-danger {{ background: #f8514922; color: var(--danger); border: 1px solid #f8514944; }}
  .tag-warning {{ background: #d2992222; color: var(--warning); border: 1px solid #d2992244; }}
  .tag-ok {{ background: #3fb95022; color: var(--success); border: 1px solid #3fb95044; }}
  .tag-info {{ background: #58a6ff22; color: var(--accent); border: 1px solid #58a6ff44; }}
  .tag-purple {{ background: #bc8cff22; color: var(--purple); border: 1px solid #bc8cff44; }}
  pre {{ background: #010409; border: 1px solid var(--border); border-radius: 6px; padding: 12px; font-size: 12px; overflow-x: auto; color: #7ee787; }}
  footer {{ text-align: center; padding: 20px; color: var(--text-muted); font-size: 12px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<header>
  <div class="logo">Mobile<span>Audit</span> <span style="font-size:14px;font-weight:400">v1.0</span>
    <span class="badge badge-{platform.lower()}">{platform}</span>
  </div>
  <div class="meta">
    📱 Dispositivo: <strong>{sanitize_text(str(device_name))}</strong> &nbsp;|&nbsp;
    🕐 Gerado em: {self.timestamp.strftime('%d/%m/%Y às %H:%M:%S')} &nbsp;|&nbsp;
    📂 Módulos: {len([k for k in self.results if not k.startswith('_')])}
  </div>
</header>
<div class="warning-bar">
  ⚠️ Este relatório contém informações sensíveis do dispositivo. Armazene e compartilhe com responsabilidade. 
  Uso conforme LGPD · Marco Civil da Internet · Lei 12.737/2012.
</div>
<main>
{sections_html}
</main>
<footer>MobileAudit v1.0 — Ferramenta de auditoria pessoal de dispositivos móveis</footer>
</body>
</html>"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return filepath

    def _build_sections_html(self):
        module_icons = {
            "info": "📱", "apps": "📦", "perms": "🔐", "security": "🛡️",
            "network": "🌐", "storage": "💾", "battery": "🔋", "processes": "⚙️",
            "accounts": "👤", "bluetooth": "🔵", "backup": "☁️", "profiles": "📋",
        }
        sections = []
        for module, data in self.results.items():
            if module.startswith("_"):
                continue
            icon = module_icons.get(module, "🔍")
            title = {
                "info": "Informações do Dispositivo", "apps": "Aplicativos Instalados",
                "perms": "Permissões Concedidas", "security": "Status de Segurança",
                "network": "Informações de Rede", "storage": "Armazenamento",
                "battery": "Bateria", "processes": "Processos em Execução",
                "accounts": "Contas Sincronizadas", "bluetooth": "Bluetooth",
                "backup": "Backup", "profiles": "Perfis de Configuração",
            }.get(module, module.capitalize())

            body_html = self._render_data_html(data)
            count = self._count_items(data)
            count_badge = f'<span class="module-count">{count} itens</span>' if count else ""

            sections.append(f"""
<div class="module">
  <div class="module-header">
    <span class="module-icon">{icon}</span>
    <span class="module-title">{title}</span>
    {count_badge}
  </div>
  <div class="module-body">{body_html}</div>
</div>""")

        return "\n".join(sections)

    def _count_items(self, data):
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            lists = [v for v in data.values() if isinstance(v, list)]
            if lists:
                return sum(len(l) for l in lists)
        return None

    def _render_data_html(self, data):
        if data is None:
            return '<p style="color:var(--text-muted)">Nenhum dado disponível.</p>'

        if isinstance(data, str):
            return f'<pre>{sanitize_text(data)}</pre>'

        if isinstance(data, list):
            if not data:
                return '<p style="color:var(--text-muted)">Nenhum item encontrado.</p>'
            if isinstance(data[0], dict):
                return self._list_of_dicts_html(data)
            else:
                items = "".join(f'<tr><td>{sanitize_text(str(item))}</td></tr>' for item in data)
                return f'<table><tbody>{items}</tbody></table>'

        if isinstance(data, dict):
            parts = []
            for key, value in data.items():
                if isinstance(value, list) and value:
                    if isinstance(value[0], dict):
                        parts.append(f'<p style="font-weight:600;margin:12px 0 6px;color:var(--accent)">{key}</p>')
                        parts.append(self._list_of_dicts_html(value))
                    else:
                        items = "".join(
                            f'<span class="tag tag-info">{sanitize_text(str(v))}</span>'
                            for v in value[:30]
                        )
                        extra = f' <span style="color:var(--text-muted)">+{len(value)-30}</span>' if len(value) > 30 else ''
                        parts.append(f'<div class="kv-row"><span class="kv-key">{key}</span><span class="kv-val">{items}{extra}</span></div>')
                elif isinstance(value, dict):
                    parts.append(f'<p style="font-weight:600;margin:12px 0 6px;color:var(--accent)">{key}</p>')
                    parts.append(self._render_data_html(value))
                else:
                    styled_val = self._style_value(key, value)
                    parts.append(f'<div class="kv-row"><span class="kv-key">{sanitize_text(key)}</span><span class="kv-val">{styled_val}</span></div>')
            return "".join(parts)

        return f'<span>{sanitize_text(str(data))}</span>'

    def _list_of_dicts_html(self, items):
        if not items:
            return ""
        headers = list(items[0].keys())
        th = "".join(f"<th>{h}</th>" for h in headers)
        rows = ""
        for item in items:
            td = "".join(f"<td>{sanitize_text(str(item.get(h, '')))}</td>" for h in headers)
            rows += f"<tr>{td}</tr>"
        return f'<table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>'

    def _style_value(self, key, value):
        key_lower = key.lower()
        val_str = sanitize_text(str(value))

        # Valores booleanos de segurança
        security_keys = ["encrypted", "criptografado", "desbloqueado", "rooted", "jailbreak", "jailbroken"]
        bad_keys = ["usb_debug", "usb_debugging", "fontes_desconhecidas", "unknown_sources", "developer_mode"]

        if isinstance(value, bool):
            if key_lower in security_keys:
                cls = "tag-ok" if value else "tag-danger"
                txt = "Sim" if value else "Não"
                return f'<span class="tag {cls}">{txt}</span>'
            if key_lower in bad_keys:
                cls = "tag-warning" if value else "tag-ok"
                txt = "Ativado" if value else "Desativado"
                return f'<span class="tag {cls}">{txt}</span>'
            cls = "tag-ok" if value else "tag-info"
            return f'<span class="tag {cls}">{"Sim" if value else "Não"}</span>'

        if any(k in key_lower for k in ["version", "versão", "android", "ios"]):
            return f'<span class="tag tag-purple">{val_str}</span>'

        if any(k in key_lower for k in ["ip", "mac", "ssid"]):
            return f'<code style="color:var(--success)">{val_str}</code>'

        if "%" in val_str:
            pct = ''.join(filter(lambda x: x.isdigit(), val_str.split("%")[0]))
            if pct.isdigit():
                p = int(pct)
                cls = "tag-danger" if p < 20 else ("tag-warning" if p < 50 else "tag-ok")
                return f'<span class="tag {cls}">{val_str}</span>'

        return val_str

    # ─── AUTO SAVE ───────────────────────────────────────────────────────────────
    def save_auto(self):
        """Salva JSON + HTML automaticamente."""
        reports_dir = ensure_reports_dir()
        json_path = os.path.join(reports_dir, f"mobileaudit_{self.ts_str}.json")
        html_path = os.path.join(reports_dir, f"mobileaudit_{self.ts_str}.html")
        self.save_json(json_path)
        self.save_html(html_path)
        return html_path
