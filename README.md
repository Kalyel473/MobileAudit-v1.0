# 📱 MobileAudit v1.0

> **Ferramenta de auditoria completa para dispositivos Android e iOS**  
> CLI profissional · Relatórios HTML/JSON · Sem dependências pesadas

---

## ⚠️ Aviso Legal

Esta ferramenta foi desenvolvida para **uso pessoal e autorizado**. Utilize apenas em:
- Seus próprios dispositivos
- Dispositivos de terceiros com **autorização explícita por escrito**
- Ambientes de teste/laboratório de sua propriedade

O uso indevido pode violar:
- **LGPD** (Lei 13.709/2018) — proteção de dados pessoais
- **Marco Civil da Internet** (Lei 12.965/2014) — inviolabilidade de comunicações
- **Lei Carolina Dieckmann** (Lei 12.737/2012) — crimes cibernéticos

---

## 🚀 Instalação

### Requisitos do Sistema

| Componente | Versão Mínima | Instalação |
|---|---|---|
| Python | 3.8+ | `sudo apt install python3` |
| ADB (Android) | qualquer | `sudo apt install adb` |
| libimobiledevice (iOS) | qualquer | `sudo apt install libimobiledevice-utils` |
| ideviceinstaller (iOS) | qualquer | `sudo apt install ideviceinstaller` |

### Instalação Automática (Linux/Ubuntu)

```bash
git clone https://github.com/seu-usuario/MobileAudit.git
cd MobileAudit
chmod +x install.sh
./install.sh
```

### Instalação Manual

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/MobileAudit.git
cd MobileAudit

# 2. Instale dependências Python
pip install -r requirements.txt

# 3. Instale ferramentas de sistema

# Android
sudo apt install android-tools-adb

# iOS
sudo apt install libimobiledevice-utils ideviceinstaller usbmuxd
sudo systemctl enable --now usbmuxd

# iOS avançado (recomendado)
pip install pymobiledevice3
```

### Verificar instalação

```bash
python3 mobileaudit.py --check-deps
```

---

## 📋 Módulos Disponíveis

### Android (via ADB)

| Módulo | Descrição | Dados Coletados |
|---|---|---|
| `info` | Informações do dispositivo | Modelo, IMEI, Android version, kernel, serial, arquitetura |
| `apps` | Aplicativos instalados | Apps de usuário/sistema/desabilitados, versões, suspeitos |
| `perms` | Permissões perigosas | Câmera, microfone, localização, SMS, contatos por app |
| `security` | Status de segurança | Criptografia, tipo de bloqueio, root, SELinux, USB debug |
| `network` | Informações de rede | SSID, IP, MAC, DNS, proxy, operadora, conexões TCP |
| `storage` | Armazenamento | Partições, espaço livre, SD card |
| `battery` | Bateria | Nível, saúde, temperatura, voltagem, tecnologia |
| `processes` | Processos | Processos em execução, serviços Android |
| `accounts` | Contas sincronizadas | Google, Exchange, outras contas |
| `bluetooth` | Bluetooth | Status, dispositivos pareados, MAC BT |
| `backup` | Backup | Status iCloud/Google, configurações |

### iOS (via libimobiledevice + pymobiledevice3)

| Módulo | Descrição | Dados Coletados |
|---|---|---|
| `info` | Informações do dispositivo | Modelo, UDID, iOS version, IMEI, serial, MAC |
| `apps` | Aplicativos instalados | Bundle IDs, versões, apps suspeitos |
| `battery` | Bateria | Nível, ciclos de carga, saúde, temperatura |
| `storage` | Armazenamento | Capacidade total/livre/usada |
| `network` | Informações de rede | MAC WiFi/BT, IMEI, operadora, SIM |
| `security` | Segurança | Jailbreak, MDM, senha ativa, Face/Touch ID |
| `profiles` | Perfis MDM | Perfis de configuração instalados, organizações |
| `backup` | Backup | Status iCloud, backups locais |

---

## 💻 Uso

### Auditoria Completa

```bash
# Android — todos os módulos
python3 mobileaudit.py --android --all

# iOS — todos os módulos
python3 mobileaudit.py --ios --all
```

### Módulos Específicos

```bash
# Android — apenas segurança e rede
python3 mobileaudit.py --android --modules security network

# iOS — info + apps + bateria
python3 mobileaudit.py --ios --modules info apps battery

# Android — permissões e apps
python3 mobileaudit.py --android --modules apps perms
```

### Salvar Relatórios

```bash
# HTML (melhor visualização)
python3 mobileaudit.py --android --all --output relatorio.html

# JSON (processamento programático)
python3 mobileaudit.py --android --all --output dados.json

# TXT (simples)
python3 mobileaudit.py --ios --all --output auditoria.txt

# Salva automaticamente em reports/ (HTML + JSON)
python3 mobileaudit.py --android --all
```

### Multi-dispositivo Android

```bash
# Listar dispositivos conectados
adb devices

# Especificar dispositivo
python3 mobileaudit.py --android --all --device SERIAL_DO_DEVICE
```

---

## 📱 Preparação dos Dispositivos

### Android — Habilitar USB Debugging

1. **Configurações** → **Sobre o telefone**
2. Toque **7x** em **Número da versão** (ativa modo desenvolvedor)
3. Volte em **Configurações** → **Opções do desenvolvedor**
4. Ative **Depuração USB**
5. Conecte o cabo USB e confirme "**Permitir depuração USB**" no celular
6. Verifique: `adb devices` — deve aparecer `device` (não `unauthorized`)

### iOS — Autorizar Conexão

1. Conecte o iPhone/iPad via cabo USB
2. **Desbloqueie** a tela do dispositivo
3. Quando aparecer "**Confiar neste Computador?**" → toque **Confiar**
4. Digite sua senha se solicitado
5. Verifique: `ideviceinfo -k DeviceName` — deve retornar o nome do device

---

## 📂 Estrutura do Projeto

```
MobileAudit/
├── mobileaudit.py          # Ponto de entrada principal
├── requirements.txt        # Dependências Python
├── install.sh              # Script de instalação
├── README.md               # Esta documentação
│
├── core/
│   ├── utils.py            # Banner, cores, helpers, verificação de deps
│   └── report.py           # Gerador de relatórios (JSON/HTML/TXT)
│
├── modules/
│   ├── android/
│   │   └── audit.py        # 11 módulos Android via ADB
│   └── ios/
│       └── audit.py        # 8 módulos iOS via libimobiledevice
│
└── reports/                # Relatórios gerados (auto-criado)
    ├── mobileaudit_20250528_143022.html
    └── mobileaudit_20250528_143022.json
```

---

## 📊 Exemplo de Relatório HTML

O relatório HTML gerado inclui:
- **Header** com nome do dispositivo, plataforma e timestamp
- **Aviso legal** integrado
- **Seções por módulo** com ícones e contagem de itens
- **Tabelas** com todos os dados coletados
- **Destaque visual** para status (🔴 risco / 🟡 atenção / 🟢 ok)
- **Tema escuro** profissional (dark mode)

---

## 🔒 Privacidade e Segurança dos Relatórios

Os relatórios contêm informações sensíveis como IMEI, UDID, MACs e contas. Recomendações:

- Armazene em local seguro e criptografado
- Não compartilhe por e-mail/mensagem sem criptografia
- Exclua após o uso
- Para conformidade LGPD: aplique controles de acesso adequados

---

## 🛠️ Troubleshooting

### Android: "unauthorized" no `adb devices`
- Desconecte e reconecte o cabo USB
- Revogue autorizações ADB em **Opções do Desenvolvedor** → **Revogar autorizações**
- Confirme o popup no display do celular

### iOS: "ideviceinfo: ERROR: Could not connect to lockdownd"
- Certifique-se que o device está **desbloqueado**
- Execute: `sudo systemctl restart usbmuxd`
- Toque **Confiar** no popup do device

### pymobiledevice3: "SSL error" ou "Could not connect"
- Execute como `sudo` na primeira vez (para acesso usbmuxd)
- Ou adicione seu usuário ao grupo plugdev: `sudo usermod -aG plugdev $USER`

---

## 🧰 Dependências

### Python (pip)
- `rich` — interface CLI rica (opcional, melhora output)
- `pymobiledevice3` — suporte iOS avançado (opcional)
- `tabulate` — formatação de tabelas

### Sistema (apt)
- `adb` — Android Debug Bridge
- `libimobiledevice-utils` — ferramentas iOS
- `ideviceinstaller` — listagem de apps iOS
- `usbmuxd` — daemon de comunicação USB iOS

---

## 📜 Licença

MIT License — uso livre para fins pessoais, educacionais e profissionais autorizados.

---

*MobileAudit v1.0 — Desenvolvido para auditoria pessoal e conformidade com LGPD*
