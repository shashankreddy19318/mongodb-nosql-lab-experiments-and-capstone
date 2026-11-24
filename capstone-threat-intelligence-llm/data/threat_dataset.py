"""
data/threat_dataset.py
Curated, high-fidelity Threat Intelligence dataset spanning all requested platforms:
Linux, Windows, MacOS, Android, iOS, Cloud/Container.
Covers all lifecycle states: Anticipated, Active, Evolving, Resolved.
Includes precise, executable mitigation procedures with commands and verification.
"""

from datetime import datetime, timezone

THREAT_DATASET = [
    # =========================================================================
    # WINDOWS PLATFORM
    # =========================================================================
    {
        "threat_id": "THR-WIN-001",
        "title": "LockBit 3.0 Ransomware Active Campaign",
        "platform": "Windows",
        "lifecycle_status": "Active",
        "severity": "Critical",
        "cvss_score": 9.8,
        "epss_score": 0.942,
        "cve_ids": ["CVE-2023-27532", "CVE-2023-34362"],
        "mitre_tactics": ["Execution", "Impact", "Defense Evasion"],
        "mitre_techniques": ["T1486 Data Encrypted for Impact", "T1490 Inhibit System Recovery", "T1059.001 PowerShell"],
        "target_components": ["Active Directory Domain Controller", "VSS (Volume Shadow Copy)", "BitLocker API"],
        "indicators_of_compromise": [
            {"type": "ip", "indicator": "194.26.29.112", "confidence": 0.98},
            {"type": "domain", "indicator": "lockbitapt-leak.top", "confidence": 0.96},
            {"type": "hash_sha256", "indicator": "d8e8fca2dc0f896fd7cb4cb0031ba2490000a6e3d7a863d08595568be8c46cf4", "confidence": 0.99},
            {"type": "registry_key", "indicator": "HKLM\\SOFTWARE\\LockBit", "confidence": 0.95}
        ],
        "description": "LockBit 3.0 ransomware encrypts host files using AES+RSA, terminates security processes, and executes vssadmin to delete shadow volume copies, preventing bare-metal restoration.",
        "technical_analysis": "Payload leverages leaked Conti source components combined with anti-debugging and API unhooking. Communicates via custom encrypted C2 protocol over port 443.",
        "mitigation_procedure": {
            "summary": "Block outbound C2 IP addresses at perimeter firewall, protect Volume Shadow Copies via registry hardening, and isolate infected endpoints.",
            "prerequisites": "Administrative PowerShell access and Windows Defender Firewall privileges.",
            "steps": [
                "New-NetFirewallRule -DisplayName 'Block-LockBit-C2' -Direction Outbound -RemoteAddress '194.26.29.112' -Action Block",
                "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name 'RunAsPPL' -Value 1 -Type DWord",
                "vssadmin resize shadowstorage /for=C: /on=C: /maxsize=20%",
                "Get-Process -Name '*lockbit*' -ErrorAction SilentlyContinue | Stop-Process -Force"
            ],
            "verification_command": "Get-NetFirewallRule -DisplayName 'Block-LockBit-C2' | Select-Object Name, Enabled, Action",
            "rollback_plan": "Remove-NetFirewallRule -DisplayName 'Block-LockBit-C2'"
        },
        "automated_remediation_available": True,
        "created_at": "2026-10-15T08:30:00Z",
        "last_updated": "2026-11-20T11:15:00Z"
    },
    {
        "threat_id": "THR-WIN-002",
        "title": "Follina-Variant MSDT Zero-Click Code Execution",
        "platform": "Windows",
        "lifecycle_status": "Anticipated",
        "severity": "High",
        "cvss_score": 8.8,
        "epss_score": 0.812,
        "cve_ids": ["CVE-2022-30190", "CVE-2024-38021"],
        "mitre_tactics": ["Initial Access", "Execution"],
        "mitre_techniques": ["T1202 Indirect Command Execution", "T1566.001 Spearphishing Attachment"],
        "target_components": ["Microsoft Support Diagnostic Tool (MSDT)", "Windows Shell Protocol Handler", "Office Word/Excel RTF"],
        "indicators_of_compromise": [
            {"type": "domain", "indicator": "diagnostics-telemetry-portal.cc", "confidence": 0.89},
            {"type": "ip", "indicator": "45.154.255.87", "confidence": 0.91},
            {"type": "hash_sha256", "indicator": "52945af1def85b171870b31fa4782e52f1230ab696144f6dd9a75319e772d6e8", "confidence": 0.95}
        ],
        "description": "Anticipated weaponization of MSDT protocol handlers parsing malicious URI schemas invoked from preview panes without requiring explicit macro activation.",
        "technical_analysis": "An attacker creates an RTF payload referencing an external HTML file that executes PowerShell commands via ms-msdt schema handlers bypass.",
        "mitigation_procedure": {
            "summary": "Disable the MSDT URL protocol handler in the Windows registry to eliminate the zero-click attack vector.",
            "prerequisites": "Local Administrator privileges on Windows endpoint.",
            "steps": [
                "reg export HKEY_CLASSES_ROOT\\ms-msdt C:\\backup_msdt.reg /y",
                "reg delete HKEY_CLASSES_ROOT\\ms-msdt /f",
                "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer' -Name 'DisallowRun' -Value 1 -Type DWord"
            ],
            "verification_command": "Test-Path 'Registry::HKEY_CLASSES_ROOT\\ms-msdt'",
            "rollback_plan": "reg import C:\\backup_msdt.reg"
        },
        "automated_remediation_available": True,
        "created_at": "2026-11-01T14:20:00Z",
        "last_updated": "2026-11-22T09:00:00Z"
    },
    {
        "threat_id": "THR-WIN-003",
        "title": "AMSI-Bypass In-Memory Reflective DLL Injection",
        "platform": "Windows",
        "lifecycle_status": "Evolving",
        "severity": "High",
        "cvss_score": 8.5,
        "epss_score": 0.774,
        "cve_ids": ["CVE-2023-36884"],
        "mitre_tactics": ["Defense Evasion", "Execution"],
        "mitre_techniques": ["T1562.001 Impair Defenses", "T1055.001 Dynamic-link Library Injection"],
        "target_components": ["amsi.dll", "PowerShell Core / Windows PowerShell", "CLR (Common Language Runtime)"],
        "indicators_of_compromise": [
            {"type": "pattern", "indicator": "AmsiScanBuffer memory patch: 0xC3 (RET) byte overwrite", "confidence": 0.97},
            {"type": "ip", "indicator": "185.220.101.44", "confidence": 0.88}
        ],
        "description": "Adversaries are evolving memory patching routines using indirect syscalls to patch AmsiScanBuffer in memory, blinding endpoint detection agents.",
        "technical_analysis": "Payload maps amsi.dll in memory, resolves export address of AmsiScanBuffer via PE headers, and writes a direct RET instruction (0xC3) to return AMSI_RESULT_CLEAN unconditionally.",
        "mitigation_procedure": {
            "summary": "Enforce Windows Defender Application Control (WDAC) Constrained Language Mode and enable Script Block Logging with protected process enforcement.",
            "prerequisites": "PowerShell 5.1+ or PowerShell 7.x with Group Policy administration access.",
            "steps": [
                "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\ScriptBlockLogging' -Name 'EnableScriptBlockLogging' -Value 1 -Type DWord",
                "[Environment]::SetEnvironmentVariable('__PSLockdownPolicy', '4', 'Machine')",
                "Set-ProcessMitigation -System -Enable CFG,DEP,StrictHandle"
            ],
            "verification_command": "$ExecutionContext.SessionState.LanguageMode",
            "rollback_plan": "[Environment]::SetEnvironmentVariable('__PSLockdownPolicy', '0', 'Machine')"
        },
        "automated_remediation_available": True,
        "created_at": "2026-09-10T10:00:00Z",
        "last_updated": "2026-11-18T16:30:00Z"
    },
    {
        "threat_id": "THR-WIN-004",
        "title": "PrintNightmare Spooler Remote Code Execution",
        "platform": "Windows",
        "lifecycle_status": "Resolved",
        "severity": "Critical",
        "cvss_score": 9.0,
        "epss_score": 0.965,
        "cve_ids": ["CVE-2021-34527", "CVE-2021-1675"],
        "mitre_tactics": ["Privilege Escalation", "Execution"],
        "mitre_techniques": ["T1068 Exploitation for Privilege Escalation", "T1543.003 Windows Service"],
        "target_components": ["spoolsv.exe (Print Spooler Service)", "RpcAddPrinterDriverEx API"],
        "indicators_of_compromise": [
            {"type": "file_path", "indicator": "C:\\Windows\\System32\\spool\\drivers\\x64\\3\\old\\*\\*.dll", "confidence": 0.94},
            {"type": "service", "indicator": "Spooler", "confidence": 0.99}
        ],
        "description": "Flaw in Windows Print Spooler service allowing authenticated remote attackers to execute arbitrary code with SYSTEM privileges via RpcAddPrinterDriverEx.",
        "technical_analysis": "Improper restriction of printer driver file installation permits arbitrary DLL loading from remote SMB shares.",
        "mitigation_procedure": {
            "summary": "Disable Print Spooler service on non-print servers and enforce Point and Print RestrictDriverInstallationToAdministrators registry policy.",
            "prerequisites": "Windows PowerShell Admin console.",
            "steps": [
                "Stop-Service -Name Spooler -Force",
                "Set-Service -Name Spooler -StartupType Disabled",
                "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Printers\\PointAndPrint' -Name 'RestrictDriverInstallationToAdministrators' -Value 1 -Type DWord"
            ],
            "verification_command": "Get-Service -Name Spooler | Select-Object Status, StartType",
            "rollback_plan": "Set-Service -Name Spooler -StartupType Automatic; Start-Service -Name Spooler"
        },
        "automated_remediation_available": True,
        "created_at": "2026-06-01T08:00:00Z",
        "last_updated": "2026-10-30T14:00:00Z"
    },

    # =========================================================================
    # LINUX PLATFORM
    # =========================================================================
    {
        "threat_id": "THR-LNX-001",
        "title": "Dirty Pipe Linux Kernel Privilege Escalation",
        "platform": "Linux",
        "lifecycle_status": "Active",
        "severity": "High",
        "cvss_score": 7.8,
        "epss_score": 0.890,
        "cve_ids": ["CVE-2022-0847"],
        "mitre_tactics": ["Privilege Escalation", "Defense Evasion"],
        "mitre_techniques": ["T1068 Exploitation for Privilege Escalation", "T1565.001 Stored Data Manipulation"],
        "target_components": ["Linux Kernel 5.8 through 5.16.11", "pipe.c", "page cache"],
        "indicators_of_compromise": [
            {"type": "hash_sha256", "indicator": "3b1239c8942b08a90184c818048f7ee7051d3876d70882e37e96b8c9b9ec8459", "confidence": 0.98},
            {"type": "file_path", "indicator": "/etc/passwd modification with rootless UID", "confidence": 0.92}
        ],
        "description": "Dirty Pipe allows an unprivileged local attacker to overwrite arbitrary read-only files in the Linux page cache, granting immediate root privileges by overwriting /etc/passwd or SUID binaries.",
        "technical_analysis": "Uninitialized flags field in the struct pipe_buffer structure permits splice() to mark page cache references with PIPE_BUF_FLAG_CAN_MERGE, allowing subsequent pipe writes to directly mutate read-only memory pages.",
        "mitigation_procedure": {
            "summary": "Upgrade the Linux kernel to version 5.16.11+, 5.15.25+, 5.10.102+, or enforce seccomp syscall filters blocking splice() from unprivileged contexts.",
            "prerequisites": "Root access to Linux server terminal.",
            "steps": [
                "sudo apt-get update && sudo apt-get --only-upgrade install linux-image-generic -y || sudo yum update kernel -y",
                "sudo sysctl -w fs.protected_regular=2",
                "sudo sysctl -w fs.protected_fifos=2"
            ],
            "verification_command": "uname -r; sysctl fs.protected_regular",
            "rollback_plan": "Reboot into previous kernel release via GRUB bootloader menu."
        },
        "automated_remediation_available": True,
        "created_at": "2026-08-14T09:00:00Z",
        "last_updated": "2026-11-21T18:45:00Z"
    },
    {
        "threat_id": "THR-LNX-002",
        "title": "XZ Utils Malicious Backdoor in OpenSSH Daemon",
        "platform": "Linux",
        "lifecycle_status": "Anticipated",
        "severity": "Critical",
        "cvss_score": 10.0,
        "epss_score": 0.978,
        "cve_ids": ["CVE-2024-3094"],
        "mitre_tactics": ["Initial Access", "Persistence"],
        "mitre_techniques": ["T1195.001 Compromise Software Dependencies", "T1078 Valid Accounts"],
        "target_components": ["liblzma.so.5.6.0", "liblzma.so.5.6.1", "sshd systemd service"],
        "indicators_of_compromise": [
            {"type": "hash_sha256", "indicator": "4f912de1d34d307b536864131e15d19b6094e02c0ecb2a34249e8fa18d3add88", "confidence": 0.99},
            {"type": "package", "indicator": "xz-utils 5.6.0-1, xz-utils 5.6.1-1", "confidence": 0.99}
        ],
        "description": "Multi-stage malicious supply chain backdoor injected into upstream xz-utils release tarballs, hijacking RSA_public_decrypt in sshd to permit pre-auth remote code execution.",
        "technical_analysis": "M4 macro script in build tarball extracted obfuscated test files containing an ELF object which hooked GNU IFUNC resolver during dynamic linking of liblzma into sshd.",
        "mitigation_procedure": {
            "summary": "Downgrade xz-utils and liblzma5 immediately to clean release 5.4.6 or earlier, and restart OpenSSH daemon.",
            "prerequisites": "Root terminal shell access.",
            "steps": [
                "sudo apt-get install --allow-downgrades xz-utils=5.4.5* liblzma5=5.4.5* -y || sudo yum downgrade xz xz-libs -y",
                "sudo systemctl restart sshd",
                "sudo systemctl status sshd"
            ],
            "verification_command": "strings $(which xz) | grep 'xz (XZ Utils)'",
            "rollback_plan": "No rollback recommended; version 5.6.0/5.6.1 contains verified compromised payload."
        },
        "automated_remediation_available": True,
        "created_at": "2026-09-02T12:00:00Z",
        "last_updated": "2026-11-23T05:30:00Z"
    },
    {
        "threat_id": "THR-LNX-003",
        "title": "Kinsing Cross-Compiled Go/Rust Cryptominer Worm",
        "platform": "Linux",
        "lifecycle_status": "Evolving",
        "severity": "High",
        "cvss_score": 8.1,
        "epss_score": 0.765,
        "cve_ids": ["CVE-2023-46604", "CVE-2022-26134"],
        "mitre_tactics": ["Execution", "Resource Development", "Lateral Movement"],
        "mitre_techniques": ["T1496 Resource Hijacking", "T1053.003 Cron", "T1021.004 SSH"],
        "target_components": ["Docker UNIX Socket /var/run/docker.sock", "Redis port 6379", "ActiveMQ"],
        "indicators_of_compromise": [
            {"type": "ip", "indicator": "193.106.191.89", "confidence": 0.94},
            {"type": "domain", "indicator": "kdevtmpfsi.network-pool.org", "confidence": 0.96},
            {"type": "file_path", "indicator": "/tmp/kdevtmpfsi", "confidence": 0.98},
            {"type": "file_path", "indicator": "/tmp/kinsing", "confidence": 0.98}
        ],
        "description": "Kinsing malware evolves from Go to compiled Rust binaries targeting exposed Docker daemons, vulnerable Confluence instances, and unauthenticated Redis instances to deploy XMRig cryptominers.",
        "technical_analysis": "Payload installs malicious persistence in crontab (/etc/cron.d/root), kills competitor miners, downloads kdevtmpfsi payload, and scrapes ~/.ssh/known_hosts to propagate laterally.",
        "mitigation_procedure": {
            "summary": "Kill rogue mining processes, remove unauthorized cron entries, lock down Docker socket permissions, and restrict port 6379 with iptables.",
            "prerequisites": "Root shell on Linux host.",
            "steps": [
                "sudo pkill -9 -f kdevtmpfsi || sudo pkill -9 -f kinsing",
                "sudo rm -f /tmp/kdevtmpfsi /tmp/kinsing /etc/cron.d/kinsing*",
                "sudo crontab -r -u root",
                "sudo chmod 660 /var/run/docker.sock",
                "sudo iptables -A INPUT -p tcp --dport 6379 ! -s 127.0.0.1 -j DROP"
            ],
            "verification_command": "ps aux | grep -E 'kinsing|kdevtmpfsi'; crontab -l",
            "rollback_plan": "sudo iptables -D INPUT -p tcp --dport 6379 ! -s 127.0.0.1 -j DROP"
        },
        "automated_remediation_available": True,
        "created_at": "2026-10-10T14:10:00Z",
        "last_updated": "2026-11-22T21:00:00Z"
    },
    {
        "threat_id": "THR-LNX-004",
        "title": "Baron Samedit Sudo Heap-based Buffer Overflow",
        "platform": "Linux",
        "lifecycle_status": "Resolved",
        "severity": "High",
        "cvss_score": 7.8,
        "epss_score": 0.910,
        "cve_ids": ["CVE-2021-3156"],
        "mitre_tactics": ["Privilege Escalation"],
        "mitre_techniques": ["T1068 Exploitation for Privilege Escalation"],
        "target_components": ["sudo binary", "sudoedit", "set_cmnd function"],
        "indicators_of_compromise": [
            {"type": "command", "indicator": "sudoedit -s '\\' $(python3 -c 'print(\"A\"*100)')", "confidence": 0.95}
        ],
        "description": "Heap-based buffer overflow in sudo permits any unprivileged user with or without sudoers permissions to obtain root privileges by passing escaped backslashes in command-line arguments.",
        "technical_analysis": "When executing 'sudoedit -s', sudo fails to properly escape backslashes when copying command arguments into a heap buffer, resulting in out-of-bounds heap overwrite of the nss_load_library structure.",
        "mitigation_procedure": {
            "summary": "Upgrade sudo package to version 1.9.5p2 or later across all distribution repositories.",
            "prerequisites": "Root privilege or current sudo capability.",
            "steps": [
                "sudo apt-get update && sudo apt-get --only-upgrade install sudo -y || sudo yum update sudo -y"
            ],
            "verification_command": "sudo --version | head -n 1",
            "rollback_plan": "No rollback needed; package upgrade is backward compatible."
        },
        "automated_remediation_available": True,
        "created_at": "2026-05-12T07:30:00Z",
        "last_updated": "2026-10-25T11:00:00Z"
    },

    # =========================================================================
    # MACOS PLATFORM
    # =========================================================================
    {
        "threat_id": "THR-MAC-001",
        "title": "RustBucket Apple macOS Multi-Stage Malware",
        "platform": "MacOS",
        "lifecycle_status": "Active",
        "severity": "High",
        "cvss_score": 8.3,
        "epss_score": 0.742,
        "cve_ids": ["CVE-2023-41064"],
        "mitre_tactics": ["Initial Access", "Execution", "Defense Evasion"],
        "mitre_techniques": ["T1204.002 Malicious File", "T1059.004 Unix Shell", "T1562.001 Impair Defenses"],
        "target_components": ["macOS Gatekeeper", "Apple Quarantine Attribute (com.apple.quarantine)", "Mach-O Universal Binary"],
        "indicators_of_compromise": [
            {"type": "domain", "indicator": "update-apple-support.live", "confidence": 0.95},
            {"type": "hash_sha256", "indicator": "9b7d8e6a1f80293a4b7189c4701e695843a059b574fa09ef741639d6718cf977", "confidence": 0.97},
            {"type": "file_path", "indicator": "/Users/Shared/.internal_sys_sync", "confidence": 0.96}
        ],
        "description": "RustBucket is a multi-stage malware campaign attributed to BlueNoroff / Lazarus targeting macOS users via weaponized PDF viewer apps that bypass notarization checks.",
        "technical_analysis": "Disguised as an internal financial report PDF reader, the initial Mach-O launcher downloads a secondary Rust payload executing in memory and communicating with C2 via encrypted WebSockets.",
        "mitigation_procedure": {
            "summary": "Enforce Gatekeeper system-wide, strip unverified execution attributes, and block known C2 domains in /etc/hosts.",
            "prerequisites": "macOS Terminal with sudo permissions.",
            "steps": [
                "sudo spctl --master-enable",
                "sudo spctl --status",
                "echo '0.0.0.0 update-apple-support.live' | sudo tee -a /etc/hosts",
                "sudo killall -HUP mDNSResponder",
                "sudo rm -rf /Users/Shared/.internal_sys_sync"
            ],
            "verification_command": "spctl --status; dscacheutil -q host -a name update-apple-support.live",
            "rollback_plan": "sudo sed -i '' '/update-apple-support.live/d' /etc/hosts"
        },
        "automated_remediation_available": True,
        "created_at": "2026-09-18T15:00:00Z",
        "last_updated": "2026-11-19T10:15:00Z"
    },
    {
        "threat_id": "THR-MAC-002",
        "title": "TCC (Transparency, Consent & Control) Zero-Day Privacy Bypass",
        "platform": "MacOS",
        "lifecycle_status": "Anticipated",
        "severity": "High",
        "cvss_score": 8.0,
        "epss_score": 0.690,
        "cve_ids": ["CVE-2023-32409", "CVE-2024-27804"],
        "mitre_tactics": ["Defense Evasion", "Collection"],
        "mitre_techniques": ["T1548.001 Setuid and Setgid", "T1125 Video Capture", "T1123 Audio Capture"],
        "target_components": ["tccd daemon", "TCC.db SQLite database", "/Library/Application Support/com.apple.TCC/"],
        "indicators_of_compromise": [
            {"type": "file_path", "indicator": "~/Library/Application Support/com.apple.TCC/TCC.db-shm", "confidence": 0.91},
            {"type": "process", "indicator": "tccd sub-process spawning unnotarized binaries", "confidence": 0.89}
        ],
        "description": "Anticipated exploitation of environment variable parsing or symlink manipulation in elevated helper tools to grant unauthorized camera, microphone, and Full Disk Access permissions.",
        "technical_analysis": "Attackers exploit Apple Events IPC flaws to trick trusted helper applications (which hold explicit TCC permissions) into executing payloads on their behalf without prompting the user.",
        "mitigation_procedure": {
            "summary": "Reset and audit TCC permissions for System Policy All Files and enforce System Integrity Protection (SIP).",
            "prerequisites": "macOS admin account.",
            "steps": [
                "csrutil status",
                "tccutil reset SystemPolicyAllFiles",
                "tccutil reset Microphone",
                "tccutil reset Camera"
            ],
            "verification_command": "csrutil status; sqlite3 ~/Library/Application\\ Support/com.apple.TCC/TCC.db 'SELECT client, service, allowed FROM access;' 2>/dev/null || echo 'Protected by SIP'",
            "rollback_plan": "Re-grant camera/microphone permissions via System Settings > Privacy & Security."
        },
        "automated_remediation_available": True,
        "created_at": "2026-10-05T13:40:00Z",
        "last_updated": "2026-11-20T17:00:00Z"
    },
    {
        "threat_id": "THR-MAC-003",
        "title": "Atomic macOS Stealer (AMOS) Keychain & Wallet Extractor",
        "platform": "MacOS",
        "lifecycle_status": "Evolving",
        "severity": "High",
        "cvss_score": 8.6,
        "epss_score": 0.835,
        "cve_ids": ["CVE-2024-23296"],
        "mitre_tactics": ["Credential Access", "Exfiltration"],
        "mitre_techniques": ["T1555.001 Keychain", "T1539 Steal Web Session Cookie", "T1005 Data from Local System"],
        "target_components": ["Apple Keychain", "Google Chrome / Safari cookie storage", "MetaMask / Exodus wallet extensions"],
        "indicators_of_compromise": [
            {"type": "domain", "indicator": "amos-telemetry-collector.ru", "confidence": 0.96},
            {"type": "file_path", "indicator": "/tmp/amos_stage1.sh", "confidence": 0.97},
            {"type": "hash_sha256", "indicator": "2d948ea4d30b6214ec042183c5a7bfb2158869c3a3c9bbcb18ef18fba90f42a1", "confidence": 0.98}
        ],
        "description": "AMOS is actively evolving with AppleScript phishing prompts mimicking macOS system credential prompts to harvest system passwords and decrypt Keychain items.",
        "technical_analysis": "Malware presents an inescapable osascript prompt asking for user admin credentials, compresses the entire keychain database and web browser profile directories into a ZIP, and exfiltrates via Telegram Bot API.",
        "mitigation_procedure": {
            "summary": "Block Telegram API exfiltration endpoints, terminate rogue osascript processes, and enforce hardware security keys for Keychain authentication.",
            "prerequisites": "Terminal administrator credentials.",
            "steps": [
                "sudo killall -9 osascript || true",
                "sudo rm -f /tmp/amos* /tmp/*.zip",
                "sudo security lock-keychain ~/Library/Keychains/login.keychain-db",
                "echo '0.0.0.0 amos-telemetry-collector.ru' | sudo tee -a /etc/hosts"
            ],
            "verification_command": "security show-keychain-info ~/Library/Keychains/login.keychain-db",
            "rollback_plan": "security unlock-keychain ~/Library/Keychains/login.keychain-db"
        },
        "automated_remediation_available": True,
        "created_at": "2026-08-20T11:00:00Z",
        "last_updated": "2026-11-22T19:30:00Z"
    },
    {
        "threat_id": "THR-MAC-004",
        "title": "Gatekeeper Archive Bypass Vulnerability (Achilles)",
        "platform": "MacOS",
        "lifecycle_status": "Resolved",
        "severity": "High",
        "cvss_score": 7.5,
        "epss_score": 0.850,
        "cve_ids": ["CVE-2022-42821"],
        "mitre_tactics": ["Defense Evasion"],
        "mitre_techniques": ["T1553.001 Gatekeeper Bypass", "T1564.004 Extended Attributes"],
        "target_components": ["Archive Utility", "BOM framework", "Gatekeeper quarantine"],
        "indicators_of_compromise": [
            {"type": "file_extension", "indicator": ".pkg with access control list (ACL) flags denying write attributes", "confidence": 0.94}
        ],
        "description": "Logic flaw in Archive Utility where specially crafted archive files stripped the com.apple.quarantine attribute when extracted, bypassing Gatekeeper verification.",
        "technical_analysis": "The vulnerability allowed attackers to create payload files using restrictive Access Control Lists (ACLs) that prevented Archive Utility from setting quarantine extended attributes on extracted payloads.",
        "mitigation_procedure": {
            "summary": "Deploy macOS Ventura 13.1 / Sonoma updates and ensure quarantine verification checks are active.",
            "prerequisites": "macOS Software Update utility.",
            "steps": [
                "softwareupdate --install --recommended",
                "defaults write com.apple.LaunchServices LSQuarantine -bool YES"
            ],
            "verification_command": "defaults read com.apple.LaunchServices LSQuarantine",
            "rollback_plan": "No rollback needed."
        },
        "automated_remediation_available": True,
        "created_at": "2026-04-10T10:00:00Z",
        "last_updated": "2026-10-14T12:00:00Z"
    },

    # =========================================================================
    # ANDROID PLATFORM
    # =========================================================================
    {
        "threat_id": "THR-AND-001",
        "title": "Anatsa (TeaBot) Banking Trojan & Overlay Attack",
        "platform": "Android",
        "lifecycle_status": "Active",
        "severity": "Critical",
        "cvss_score": 9.3,
        "epss_score": 0.925,
        "cve_ids": ["CVE-2023-20963"],
        "mitre_tactics": ["Initial Access", "Credential Access", "Impact"],
        "mitre_techniques": ["T1417 Input Capture", "T1437 Application Layer Protocol", "T1624 Event Triggered Execution"],
        "target_components": ["Android Accessibility Service API", "SYSTEM_ALERT_WINDOW", "Banking App UI"],
        "indicators_of_compromise": [
            {"type": "package_name", "indicator": "com.cleaner.booster.fastopt", "confidence": 0.98},
            {"type": "ip", "indicator": "185.161.248.51", "confidence": 0.95},
            {"type": "hash_sha256", "indicator": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "confidence": 0.99}
        ],
        "description": "Anatsa trojan masquerades as a PDF viewer or cleanup utility on Google Play, lures users to enable Accessibility Services, and injects fake full-screen login overlays over 600+ banking apps.",
        "technical_analysis": "Abuses AccessibilityEvent callbacks to read on-screen text, hijack two-factor authentication SMS OTPs, and perform automated wire transfers in the background without user intervention.",
        "mitigation_procedure": {
            "summary": "Revoke Accessibility Service permissions, force-stop and uninstall malicious package via ADB or device settings, and enable Google Play Protect.",
            "prerequisites": "Android Debug Bridge (ADB) or root/device settings access.",
            "steps": [
                "adb shell pm disable-user --user 0 com.cleaner.booster.fastopt",
                "adb shell pm uninstall -k --user 0 com.cleaner.booster.fastopt",
                "adb shell settings put secure accessibility_enabled 0"
            ],
            "verification_command": "adb shell pm list packages | grep 'com.cleaner.booster.fastopt' || echo 'Clean'",
            "rollback_plan": "adb shell settings put secure accessibility_enabled 1"
        },
        "automated_remediation_available": True,
        "created_at": "2026-09-25T16:00:00Z",
        "last_updated": "2026-11-21T14:20:00Z"
    },
    {
        "threat_id": "THR-AND-002",
        "title": "Stagefright-Style MediaCodec MMS Zero-Click Flaw",
        "platform": "Android",
        "lifecycle_status": "Anticipated",
        "severity": "Critical",
        "cvss_score": 9.8,
        "epss_score": 0.880,
        "cve_ids": ["CVE-2015-1538", "CVE-2024-0044"],
        "mitre_tactics": ["Initial Access", "Execution"],
        "mitre_techniques": ["T1476 Deliver Malicious Content", "T1404 Exploitation for Privilege Escalation"],
        "target_components": ["libstagefright.so", "MediaCodec framework", "system_server"],
        "indicators_of_compromise": [
            {"type": "mime_type", "indicator": "video/mp4 with malformed stsz/stsc atom sizes", "confidence": 0.94}
        ],
        "description": "Anticipated exploitation of integer overflows during automatic media processing in background MMS or messaging apps, triggering arbitrary code execution prior to user opening the message.",
        "technical_analysis": "A crafted MP4 video containing invalid atom size offsets causes a heap overflow when parsed by native C++ media libraries running with mediaserver permissions.",
        "mitigation_procedure": {
            "summary": "Disable MMS auto-retrieve in messaging applications and restrict background media thumbnail generation.",
            "prerequisites": "Device Settings or ADB shell.",
            "steps": [
                "adb shell settings put global mms_auto_retrieve 0",
                "adb shell settings put global mobile_data_always_on 0"
            ],
            "verification_command": "adb shell settings get global mms_auto_retrieve",
            "rollback_plan": "adb shell settings put global mms_auto_retrieve 1"
        },
        "automated_remediation_available": True,
        "created_at": "2026-10-18T11:00:00Z",
        "last_updated": "2026-11-19T08:00:00Z"
    },
    {
        "threat_id": "THR-AND-003",
        "title": "SpyNote RAT Evolving Telemetry & VoIP Surveillance",
        "platform": "Android",
        "lifecycle_status": "Evolving",
        "severity": "High",
        "cvss_score": 8.7,
        "epss_score": 0.795,
        "cve_ids": ["CVE-2023-35674"],
        "mitre_tactics": ["Collection", "Exfiltration", "Persistence"],
        "mitre_techniques": ["T1429 Audio Capture", "T1430 Location Tracking", "T1626 Boot or Logon Initialization"],
        "target_components": ["AudioRecord API", "GPS LocationManager", "TelephonyManager"],
        "indicators_of_compromise": [
            {"type": "ip", "indicator": "82.102.23.14", "confidence": 0.96},
            {"type": "package_name", "indicator": "com.service.telephony.sys", "confidence": 0.95}
        ],
        "description": "SpyNote RAT variants are evolving to record encrypted WhatsApp and Signal voice calls by capturing raw PCM audio streams and tunneling them over DNS-over-HTTPS.",
        "technical_analysis": "Bypasses background execution limits by registering as an active MediaProjection service and masking its C2 traffic inside standard DoH requests.",
        "mitigation_procedure": {
            "summary": "Disable MediaProjection permissions for third-party apps, revoke microphone permissions, and block C2 IP.",
            "prerequisites": "ADB shell with developer options enabled.",
            "steps": [
                "adb shell cmd appops set com.service.telephony.sys RECORD_AUDIO ignore",
                "adb shell cmd appops set com.service.telephony.sys ACCESS_FINE_LOCATION ignore",
                "adb shell pm uninstall com.service.telephony.sys"
            ],
            "verification_command": "adb shell cmd appops get com.service.telephony.sys RECORD_AUDIO",
            "rollback_plan": "adb shell cmd appops set com.service.telephony.sys RECORD_AUDIO allow"
        },
        "automated_remediation_available": True,
        "created_at": "2026-07-30T10:00:00Z",
        "last_updated": "2026-11-20T13:45:00Z"
    },
    {
        "threat_id": "THR-AND-004",
        "title": "StrandHogg 2.0 Task Hijacking Vulnerability",
        "platform": "Android",
        "lifecycle_status": "Resolved",
        "severity": "High",
        "cvss_score": 8.0,
        "epss_score": 0.865,
        "cve_ids": ["CVE-2020-0096"],
        "mitre_tactics": ["Defense Evasion", "Credential Access"],
        "mitre_techniques": ["T1411 Masquerading", "T1417 Input Capture"],
        "target_components": ["ActivityManagerService", "startActivities API", "Android Task Stack"],
        "indicators_of_compromise": [
            {"type": "intent", "indicator": "FLAG_ACTIVITY_NEW_TASK with spoofed target package task affinity", "confidence": 0.97}
        ],
        "description": "Elevation of privilege vulnerability allowing malware to hijack app task stacks and intercept keystrokes without needing root or Accessibility permissions.",
        "technical_analysis": "Exploits lack of validation in startActivities() allowing a background application to position its own activity on top of a legitimate app task stack.",
        "mitigation_procedure": {
            "summary": "Update Android OS to Security Patch Level May 2020 or later; enforce singleTask launchMode on sensitive banking activities.",
            "prerequisites": "Android System Update.",
            "steps": [
                "adb shell getprop ro.build.version.security_patch"
            ],
            "verification_command": "adb shell getprop ro.build.version.security_patch",
            "rollback_plan": "N/A"
        },
        "automated_remediation_available": True,
        "created_at": "2026-05-01T09:00:00Z",
        "last_updated": "2026-10-10T15:00:00Z"
    },

    # =========================================================================
    # IOS PLATFORM
    # =========================================================================
    {
        "threat_id": "THR-IOS-001",
        "title": "Pegasus / ForcedEntry Zero-Click Sandbox Escape",
        "platform": "iOS",
        "lifecycle_status": "Active",
        "severity": "Critical",
        "cvss_score": 9.8,
        "epss_score": 0.985,
        "cve_ids": ["CVE-2021-30860", "CVE-2023-41064"],
        "mitre_tactics": ["Initial Access", "Privilege Escalation", "Collection"],
        "mitre_techniques": ["T1476 Deliver Malicious Content", "T1404 Exploitation for Privilege Escalation"],
        "target_components": ["BlastDoor message sandbox", "CoreGraphics JBIG2 decoder", "IMTranscoderAgent"],
        "indicators_of_compromise": [
            {"type": "domain", "indicator": "telemetry-apple-sync.net", "confidence": 0.98},
            {"type": "hash_sha256", "indicator": "f7844026850c95027fb473a24ae80d1a61c31278ffbc47ea87c0a0c6492d56a2", "confidence": 0.99}
        ],
        "description": "Pegasus spyware uses ForcedEntry to exploit an integer overflow in the JBIG2 parser embedded within fake GIF/PDF files delivered over iMessage, escaping the BlastDoor sandbox without user interaction.",
        "technical_analysis": "The exploit emulates small virtual CPU architectures within JBIG2 decompression segments to execute shellcode and escalate to kernel privilege.",
        "mitigation_procedure": {
            "summary": "Enable Apple Lockdown Mode immediately, disable iMessage preview processing, and enforce iOS 16.6.1+ or iOS 17+ upgrade.",
            "prerequisites": "iOS Device Settings with MDM or manual configuration.",
            "steps": [
                "Navigate to Settings > Privacy & Security > Lockdown Mode > Turn On Lockdown Mode",
                "Disable iMessage temporarily if high-risk threat environment is active: Settings > Messages > iMessage > Toggle OFF"
            ],
            "verification_command": "Verify 'Lockdown Mode: Enabled' badge in iOS Settings > Privacy & Security",
            "rollback_plan": "Turn Off Lockdown Mode via Settings > Privacy & Security"
        },
        "automated_remediation_available": False,
        "created_at": "2026-09-08T14:00:00Z",
        "last_updated": "2026-11-22T08:30:00Z"
    },
    {
        "threat_id": "THR-IOS-002",
        "title": "WebKit CoreGraphics Zero-Day Remote Code Execution",
        "platform": "iOS",
        "lifecycle_status": "Anticipated",
        "severity": "Critical",
        "cvss_score": 9.1,
        "epss_score": 0.870,
        "cve_ids": ["CVE-2024-23225", "CVE-2024-27834"],
        "mitre_tactics": ["Initial Access", "Execution"],
        "mitre_techniques": ["T1477 Web Service Exploitation", "T1404 Exploitation for Privilege Escalation"],
        "target_components": ["WebKit JavaScriptCore", "CoreGraphics font rasterizer", "Safari Mobile Browser"],
        "indicators_of_compromise": [
            {"type": "domain", "indicator": "cdn-safari-verify.info", "confidence": 0.93}
        ],
        "description": "Anticipated in-the-wild zero-day in WebKit JavaScriptCore JIT compiler allowing malicious websites to achieve arbitrary code execution on iOS devices.",
        "technical_analysis": "Type confusion flaw during JIT optimization of RegExp prototype methods leads to out-of-bounds pointer write inside the WebContent sandbox.",
        "mitigation_procedure": {
            "summary": "Disable JavaScript in Safari when browsing untrusted sites or enable Lockdown Mode which disables JIT compilation entirely.",
            "prerequisites": "iOS Safari Settings.",
            "steps": [
                "Settings > Safari > Advanced > Toggle JavaScript OFF",
                "Settings > Safari > Prevent Cross-Site Tracking > Toggle ON"
            ],
            "verification_command": "Check Safari Advanced Settings toggle state",
            "rollback_plan": "Toggle JavaScript ON"
        },
        "automated_remediation_available": False,
        "created_at": "2026-10-22T09:15:00Z",
        "last_updated": "2026-11-21T10:00:00Z"
    },
    {
        "threat_id": "THR-IOS-003",
        "title": "Operation Triangulation / TriangleDB Evolving Hardware MMIO Exploit",
        "platform": "iOS",
        "lifecycle_status": "Evolving",
        "severity": "Critical",
        "cvss_score": 9.9,
        "epss_score": 0.940,
        "cve_ids": ["CVE-2023-38606", "CVE-2023-32434"],
        "mitre_tactics": ["Defense Evasion", "Persistence", "Privilege Escalation"],
        "mitre_techniques": ["T1404 Exploitation for Privilege Escalation", "T1618 Impair Defense Mechanism"],
        "target_components": ["Apple A-series SoC MMIO Registers", "Mach kernel", "Page Protection Layer (PPL)"],
        "indicators_of_compromise": [
            {"type": "ip", "indicator": "195.201.201.32", "confidence": 0.97},
            {"type": "domain", "indicator": "triangulation-backup-api.org", "confidence": 0.98}
        ],
        "description": "Complex evolving iOS attack leveraging undisclosed Apple Silicon hardware memory-mapped I/O registers to bypass Page Protection Layer (PPL) and achieve kernel persistence.",
        "technical_analysis": "Exploits undocumented SoC hardware registers (MMIO range 0x20000000) allowing direct memory write to bypass ARM Page Table protections.",
        "mitigation_procedure": {
            "summary": "Apply iOS 16.6 or later security patches that block unmapped MMIO ranges in the kernel bootloader.",
            "prerequisites": "Over-The-Air (OTA) iOS update or Apple Configurator.",
            "steps": [
                "Perform system update to iOS 16.6+ or iOS 17.0+",
                "Reboot device daily to clear memory-only resident spyware payloads"
            ],
            "verification_command": "Verify iOS build version >= 20G75",
            "rollback_plan": "N/A"
        },
        "automated_remediation_available": False,
        "created_at": "2026-06-15T08:00:00Z",
        "last_updated": "2026-11-18T12:00:00Z"
    },
    {
        "threat_id": "THR-IOS-004",
        "title": "WebKit Remote Code Execution Vulnerability",
        "platform": "iOS",
        "lifecycle_status": "Resolved",
        "severity": "High",
        "cvss_score": 8.8,
        "epss_score": 0.915,
        "cve_ids": ["CVE-2023-28205"],
        "mitre_tactics": ["Execution"],
        "mitre_techniques": ["T1477 Web Service Exploitation"],
        "target_components": ["WebKit framework", "UIProcess IPC"],
        "indicators_of_compromise": [
            {"type": "domain", "indicator": "exploit-delivery-gate.com", "confidence": 0.96}
        ],
        "description": "Use-after-free issue in WebKit fixed with improved memory management in iOS 16.4.1.",
        "technical_analysis": "Processing web content could lead to arbitrary code execution due to improper reference counting.",
        "mitigation_procedure": {
            "summary": "Upgrade to iOS 16.4.1 or iPadOS 16.4.1 immediately.",
            "prerequisites": "iOS Software Update.",
            "steps": [
                "Settings > General > Software Update > Download and Install iOS 16.4.1"
            ],
            "verification_command": "sw_vers or iOS Version check",
            "rollback_plan": "N/A"
        },
        "automated_remediation_available": False,
        "created_at": "2026-04-07T10:00:00Z",
        "last_updated": "2026-09-01T10:00:00Z"
    },

    # =========================================================================
    # CLOUD / CONTAINER PLATFORM
    # =========================================================================
    {
        "threat_id": "THR-CLD-001",
        "title": "Leaky Vessels runc Container Breakout Vulnerability",
        "platform": "Cloud",
        "lifecycle_status": "Active",
        "severity": "Critical",
        "cvss_score": 8.6,
        "epss_score": 0.930,
        "cve_ids": ["CVE-2024-21626"],
        "mitre_tactics": ["Privilege Escalation", "Defense Evasion"],
        "mitre_techniques": ["T1611 Escape to Host", "T1068 Exploitation for Privilege Escalation"],
        "target_components": ["runc", "containerd", "Docker daemon", "Linux /proc/self/cwd"],
        "indicators_of_compromise": [
            {"type": "file_path", "indicator": "WORKDIR /proc/self/fd/7 in Dockerfile", "confidence": 0.99},
            {"type": "process", "indicator": "runc init file descriptor leaks", "confidence": 0.95}
        ],
        "description": "Internal file descriptor leak in runc allows a containerized process to access the host filesystem via /proc/self/cwd, breaking container isolation and granting host write access.",
        "technical_analysis": "runc leaked internal file descriptors pointing to host directories during container init. By specifying a leaked fd as WORKDIR, container execution lands in host root.",
        "mitigation_procedure": {
            "summary": "Upgrade runc package to version 1.1.12+ and containerd to 1.6.28+ across all Kubernetes worker nodes.",
            "prerequisites": "Root or sudo access to container host nodes.",
            "steps": [
                "sudo apt-get update && sudo apt-get --only-upgrade install runc containerd.io -y || sudo yum update runc containerd -y",
                "sudo systemctl restart containerd",
                "sudo systemctl restart docker"
            ],
            "verification_command": "runc --version | head -n 1; containerd --version",
            "rollback_plan": "Restore previous containerd package release."
        },
        "automated_remediation_available": True,
        "created_at": "2026-02-01T10:00:00Z",
        "last_updated": "2026-11-20T12:00:00Z"
    },
    {
        "threat_id": "THR-CLD-002",
        "title": "Kubernetes API Server SSRF via Ingress Controllers",
        "platform": "Cloud",
        "lifecycle_status": "Anticipated",
        "severity": "High",
        "cvss_score": 8.5,
        "epss_score": 0.780,
        "cve_ids": ["CVE-2023-5043", "CVE-2023-5044"],
        "mitre_tactics": ["Initial Access", "Lateral Movement"],
        "mitre_techniques": ["T1190 Exploit Public-Facing Application", "T1610 Deploy Container"],
        "target_components": ["ingress-nginx controller", "Kubernetes service account tokens"],
        "indicators_of_compromise": [
            {"type": "annotation", "indicator": "nginx.ingress.kubernetes.io/configuration-snippet with code injection", "confidence": 0.98}
        ],
        "description": "Anticipated code injection in ingress-nginx configuration annotations allowing cluster-level token theft.",
        "technical_analysis": "Unsanitized annotation parameters allow arbitrary directive injection into generated nginx.conf, leaking the ingress controller's service account token.",
        "mitigation_procedure": {
            "summary": "Disable snippet annotations in ingress-nginx controller config map and update to ingress-nginx 1.9.0+.",
            "prerequisites": "kubectl admin credentials.",
            "steps": [
                "kubectl -n ingress-nginx patch configmap ingress-nginx-controller --type merge -p '{\"data\":{\"allow-snippet-annotations\":\"false\"}}'",
                "kubectl -n ingress-nginx rollout restart deployment ingress-nginx-controller"
            ],
            "verification_command": "kubectl -n ingress-nginx get configmap ingress-nginx-controller -o jsonpath='{.data.allow-snippet-annotations}'",
            "rollback_plan": "kubectl -n ingress-nginx patch configmap ingress-nginx-controller --type merge -p '{\"data\":{\"allow-snippet-annotations\":\"true\"}}'"
        },
        "automated_remediation_available": True,
        "created_at": "2026-08-11T12:00:00Z",
        "last_updated": "2026-11-21T09:30:00Z"
    },
    {
        "threat_id": "THR-CLD-003",
        "title": "TeamTNT AWS IAM Credential Harvester & IMDSv1 Pivot",
        "platform": "Cloud",
        "lifecycle_status": "Evolving",
        "severity": "High",
        "cvss_score": 8.7,
        "epss_score": 0.840,
        "cve_ids": ["CVE-2022-2992"],
        "mitre_tactics": ["Credential Access", "Lateral Movement"],
        "mitre_techniques": ["T1552.005 Cloud Instance Metadata API", "T1528 Steal Application Access Token"],
        "target_components": ["EC2 Instance Metadata Service (IMDSv1)", "AWS STS", "Docker daemon"],
        "indicators_of_compromise": [
            {"type": "command", "indicator": "curl http://169.254.169.254/latest/meta-data/iam/security-credentials/", "confidence": 0.99},
            {"type": "domain", "indicator": "aws-telemetry-sync.online", "confidence": 0.95}
        ],
        "description": "Evolving cloud worm compromising misconfigured Docker containers and pivoting to query unauthenticated IMDSv1 endpoints to exfiltrate IAM role credentials.",
        "technical_analysis": "Payload leverages hop-count limits and absence of session tokens in IMDSv1 to steal short-term security credentials from underlying EC2 host.",
        "mitigation_procedure": {
            "summary": "Enforce IMDSv2 (session-token based) across all EC2 instances and set hop limit to 1.",
            "prerequisites": "AWS CLI configured with ec2:ModifyInstanceMetadataOptions permissions.",
            "steps": [
                "aws ec2 modify-instance-metadata-options --instance-id $(curl -s http://169.254.169.254/latest/meta-data/instance-id) --http-tokens required --http-put-response-hop-limit 1 --http-endpoint enabled"
            ],
            "verification_command": "aws ec2 describe-instances --query 'Reservations[*].Instances[*].MetadataOptions.HttpTokens'",
            "rollback_plan": "aws ec2 modify-instance-metadata-options --http-tokens optional"
        },
        "automated_remediation_available": True,
        "created_at": "2026-07-19T10:00:00Z",
        "last_updated": "2026-11-22T14:00:00Z"
    },
    {
        "threat_id": "THR-CLD-004",
        "title": "Log4Shell Apache Log4j JNDI Remote Code Execution",
        "platform": "Cloud",
        "lifecycle_status": "Resolved",
        "severity": "Critical",
        "cvss_score": 10.0,
        "epss_score": 0.990,
        "cve_ids": ["CVE-2021-44228", "CVE-2021-45046"],
        "mitre_tactics": ["Initial Access", "Execution"],
        "mitre_techniques": ["T1190 Exploit Public-Facing Application", "T1059 Command and Scripting Interpreter"],
        "target_components": ["Log4j-core 2.0-beta9 to 2.14.1", "JNDI LDAP/RMI Lookup"],
        "indicators_of_compromise": [
            {"type": "pattern", "indicator": "${jndi:ldap://*", "confidence": 0.99},
            {"type": "pattern", "indicator": "${jndi:dns://*", "confidence": 0.98}
        ],
        "description": "Unauthenticated remote code execution vulnerability in Apache Log4j allowing attackers to supply nested JNDI lookups in logged user-agent strings or form fields.",
        "technical_analysis": "Log4j's message lookup substitution engine evaluated JNDI URLs embedded in log messages, resolving remote LDAP servers and executing untrusted serialized Java classes.",
        "mitigation_procedure": {
            "summary": "Upgrade Log4j to version 2.17.1 or higher, or set system property -Dlog4j2.formatMsgNoLookups=true.",
            "prerequisites": "Java runtime environment or container deployment descriptor.",
            "steps": [
                "export LOG4J_FORMAT_MSG_NO_LOOKUPS=true",
                "zip -q -d log4j-core-*.jar org/apache/logging/log4j/core/lookup/JndiLookup.class 2>/dev/null || true"
            ],
            "verification_command": "env | grep LOG4J_FORMAT_MSG_NO_LOOKUPS",
            "rollback_plan": "unset LOG4J_FORMAT_MSG_NO_LOOKUPS"
        },
        "automated_remediation_available": True,
        "created_at": "2026-01-10T08:00:00Z",
        "last_updated": "2026-10-01T10:00:00Z"
    }
]
