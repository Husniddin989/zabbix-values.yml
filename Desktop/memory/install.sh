#!/bin/bash

# =============================================================================
# SYSTEM MONITOR - O'rnatish skripti
# Muallif: Husniddin
# Versiya: 1.0
# =============================================================================

set -e

# Ranglar
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Root tekshirish
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}Bu skriptni ishga tushirish uchun root huquqiga ega bo'lishingiz kerak.${NC}" 1>&2
   echo -e "${YELLOW}Maslahat: 'sudo ./install.sh' buyrug'ini ishlatib ko'ring${NC}" 1>&2
   exit 1
fi

echo -e "${BLUE}===== SYSTEM MONITOR o'rnatish uchun yordamchi skript =====${NC}"
echo -e "${YELLOW}Bu skript sizga system-monitor xizmatini o'rnatishda yordam beradi${NC}\n"

# O'rnatish joyini tanlash
INSTALL_DIR="/opt/memory-monitor"
CONFIG_DIR="/etc/memory-monitor"
SYSTEMD_DIR="/etc/systemd/system"

mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

# Telegram Bot sozlamalari
echo -e "${BLUE}Telegram sozlamalari${NC}"
echo -e "${YELLOW}Telegram Bot yaratish uchun @BotFather ga murojaat qiling${NC}"

read -p "Telegram Bot Token [7307193506:AAFPT6sTT-ObsST-iwztmq-PkF8h7dSM0bo]: " BOT_TOKEN
BOT_TOKEN=${BOT_TOKEN:-"7307193506:AAFPT6sTT-ObsST-iwztmq-PkF8h7dSM0bo"}

read -p "Telegram Chat ID [-4244542922]: " CHAT_ID
CHAT_ID=${CHAT_ID:-"-4244542922"}

# Monitoring sozlamalari
echo -e "\n${BLUE}Monitoring sozlamalari${NC}"

read -p "RAM foizi (chegarasi) [80]: " RAM_THRESHOLD
RAM_THRESHOLD=${RAM_THRESHOLD:-80}

read -p "Tekshirish oralig'i (soniyalarda) [60]: " CHECK_INTERVAL
CHECK_INTERVAL=${CHECK_INTERVAL:-60}

read -p "CPU monitoringini yoqish? (true/false) [true]: " MONITOR_CPU
MONITOR_CPU=${MONITOR_CPU:-true}

if [ "$MONITOR_CPU" = "true" ]; then
    read -p "CPU foizi (chegarasi) [90]: " CPU_THRESHOLD
    CPU_THRESHOLD=${CPU_THRESHOLD:-90}
else
    CPU_THRESHOLD=90
fi

read -p "Disk monitoringini yoqish? (true/false) [true]: " MONITOR_DISK
MONITOR_DISK=${MONITOR_DISK:-true}

if [ "$MONITOR_DISK" = "true" ]; then
    read -p "Disk foizi (chegarasi) [90]: " DISK_THRESHOLD
    DISK_THRESHOLD=${DISK_THRESHOLD:-90}
    
    read -p "Disk yo'li [/]: " DISK_PATH
    DISK_PATH=${DISK_PATH:-"/"}
else
    DISK_THRESHOLD=90
    DISK_PATH="/"
fi

read -p "Log fayli [/var/log/memory_monitor.log]: " LOG_FILE
LOG_FILE=${LOG_FILE:-"/var/log/memory_monitor.log"}

read -p "Log darajasi (DEBUG/INFO/WARNING/ERROR) [INFO]: " LOG_LEVEL
LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Konfiguratsiya faylini yaratish
echo -e "\n${GREEN}Konfiguratsiya faylini yaratish...${NC}"

cat > "$CONFIG_DIR/config.conf" << EOF
# Memory Monitor konfiguratsiya fayli
# Telegram bot sozlamalari
BOT_TOKEN="$BOT_TOKEN"
CHAT_ID="$CHAT_ID"

# Monitoring sozlamalari
THRESHOLD=$RAM_THRESHOLD
CHECK_INTERVAL=$CHECK_INTERVAL
LOG_FILE="$LOG_FILE"
LOG_LEVEL="$LOG_LEVEL"

# Xabar sozlamalari
ALERT_MESSAGE_TITLE="🛑 SYSTEM MONITOR ALERT"
INCLUDE_TOP_PROCESSES=true
TOP_PROCESSES_COUNT=10

# CPU monitoring (true/false)
MONITOR_CPU=$MONITOR_CPU
CPU_THRESHOLD=$CPU_THRESHOLD

# Disk monitoring (true/false)
MONITOR_DISK=$MONITOR_DISK
DISK_THRESHOLD=$DISK_THRESHOLD
DISK_PATH="$DISK_PATH"
EOF

# Asosiy skriptni o'rnatish
echo -e "${GREEN}Monitoring skriptini o'rnatish...${NC}"

# Skript faylini nusxalash
cp "$(dirname "$0")/memory-monitor.sh" "$INSTALL_DIR/memory-monitor.sh"
chmod +x "$INSTALL_DIR/memory-monitor.sh"

# Systemd service faylini yaratish
echo -e "${GREEN}Systemd service faylini yaratish...${NC}"

cat > "$SYSTEMD_DIR/memory-monitor.service" << EOF
[Unit]
Description=System Memory, CPU and Disk Monitoring Service
After=network.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/memory-monitor.sh
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=memory-monitor

[Install]
WantedBy=multi-user.target
EOF

# Xizmatni yoqish va ishga tushirish
echo -e "${GREEN}Xizmatni yoqish va ishga tushirish...${NC}"
systemctl daemon-reload
systemctl enable memory-monitor.service
systemctl start memory-monitor.service

# Xizmat holatini tekshirish
echo -e "${BLUE}Xizmat holati:${NC}"
systemctl status memory-monitor.service

echo -e "\n${GREEN}O'rnatish muvaffaqiyatli yakunlandi!${NC}"
echo -e "${YELLOW}Konfiguratsiya fayli: $CONFIG_DIR/config.conf${NC}"
echo -e "${YELLOW}Log fayli: $LOG_FILE${NC}"
echo -e "\n${BLUE}Qo'shimcha buyruqlar:${NC}"
echo -e "  Xizmatni qayta ishga tushirish: ${YELLOW}sudo systemctl restart memory-monitor.service${NC}"
echo -e "  Xizmatni to'xtatish: ${YELLOW}sudo systemctl stop memory-monitor.service${NC}"
echo -e "  Xizmat holatini tekshirish: ${YELLOW}sudo systemctl status memory-monitor.service${NC}"
echo -e "  Loglarni ko'rish: ${YELLOW}sudo journalctl -u memory-monitor.service${NC}"
echo -e "  Konfiguratsiyani tahrirlash: ${YELLOW}sudo nano $CONFIG_DIR/config.conf${NC}"
