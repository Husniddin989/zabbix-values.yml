#!/bin/bash

# =============================================================================
# SYSTEM MONITOR - Tizim resurslarini kuzatish va Telegram orqali xabar yuborish
# Muallif: Husniddin
# Versiya: 1.0
# =============================================================================

# Konfiguratsiya fayli joylashuvi
CONFIG_FILE="/etc/memory-monitor/config.conf"
DEFAULT_LOG_FILE="/var/log/memory_monitor.log"
DEFAULT_THRESHOLD=80
DEFAULT_INTERVAL=60
DEFAULT_LOG_LEVEL="INFO"

# Skript haqida ma'lumot chiqarish
show_info() {
    echo "==================================================="
    echo "SYSTEM MONITOR - Tizim resurslarini kuzatish dasturi"
    echo "Versiya: 1.0"
    echo "==================================================="
    echo "Bu dastur serveringizning RAM, CPU va disk resurslarini"
    echo "kuzatib boradi va belgilangan chegaradan oshganda"
    echo "Telegram orqali xabar yuboradi."
    echo "==================================================="
}

# Agar parametr berilgan bo'lsa
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_info
    echo "Foydalanish: $0 [--config /yo'l/config.conf]"
    echo "  --config    Konfiguratsiya fayli yo'lini ko'rsatish"
    echo "  --help      Ushbu ma'lumotni ko'rsatish"
    exit 0
fi

# Parametrlarni tekshirish
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --config)
            CONFIG_FILE="$2"
            shift
            shift
            ;;
        *)
            echo "Noma'lum parametr: $1"
            echo "Yordam uchun: $0 --help"
            exit 1
            ;;
    esac
done

# Agar konfiguratsiya fayli mavjud bo'lmasa, uni yaratib olish
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_DIR=$(dirname "$CONFIG_FILE")
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        echo "Konfiguratsiya katalogi yaratildi: $CONFIG_DIR"
    fi
    
    cat > "$CONFIG_FILE" << EOF
# Memory Monitor konfiguratsiya fayli
# Telegram bot sozlamalari
BOT_TOKEN="7307193506:AAFPT6sTT-ObsST-iwztmq-PkF8h7dSM0bo"
CHAT_ID="-4244542922"

# Monitoring sozlamalari
THRESHOLD=80               # RAM foizi (qachon xabar yuborish kerak)
CHECK_INTERVAL=60          # Tekshirish oralig'i (soniyalarda)
LOG_FILE="/var/log/memory_monitor.log"
LOG_LEVEL="INFO"           # DEBUG, INFO, WARNING, ERROR

# Xabar sozlamalari
ALERT_MESSAGE_TITLE="🛑 SYSTEM MONITOR ALERT"
INCLUDE_TOP_PROCESSES=true
TOP_PROCESSES_COUNT=10

# CPU monitoring (true/false)
MONITOR_CPU=true
CPU_THRESHOLD=90

# Disk monitoring (true/false)
MONITOR_DISK=true
DISK_THRESHOLD=90
DISK_PATH="/"
EOF
    echo "Standart konfiguratsiya fayli yaratildi: $CONFIG_FILE"
    echo "Iltimos, uni o'z ehtiyojlaringizga qarab sozlang."
fi

# Konfiguratsiya faylini yuklash
source "$CONFIG_FILE"

# Standart qiymatlarni aniqlash
BOT_TOKEN="${BOT_TOKEN:-}"
CHAT_ID="${CHAT_ID:-}"
LOG_FILE="${LOG_FILE:-$DEFAULT_LOG_FILE}"
THRESHOLD="${THRESHOLD:-$DEFAULT_THRESHOLD}"
CHECK_INTERVAL="${CHECK_INTERVAL:-$DEFAULT_INTERVAL}"
LOG_LEVEL="${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}"
ALERT_MESSAGE_TITLE="${ALERT_MESSAGE_TITLE:-🛑 SYSTEM MONITOR ALERT}"
INCLUDE_TOP_PROCESSES="${INCLUDE_TOP_PROCESSES:-true}"
TOP_PROCESSES_COUNT="${TOP_PROCESSES_COUNT:-10}"
MONITOR_CPU="${MONITOR_CPU:-false}"
CPU_THRESHOLD="${CPU_THRESHOLD:-90}"
MONITOR_DISK="${MONITOR_DISK:-false}"
DISK_THRESHOLD="${DISK_THRESHOLD:-90}"
DISK_PATH="${DISK_PATH:-/}"

# Log faylini yaratib olish (agar mavjud bo'lmasa)
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
fi

# Konfiguratsiyani tekshirish
if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "XATO: BOT_TOKEN va CHAT_ID konfiguratsiya faylida ko'rsatilishi kerak."
    echo "Iltimos, $CONFIG_FILE faylini tahrirlang."
    exit 1
fi

# Log darajasi funksiyalari
LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARNING=2
LOG_LEVEL_ERROR=3

get_log_level_num() {
    case "$1" in
        "DEBUG") echo $LOG_LEVEL_DEBUG ;;
        "INFO") echo $LOG_LEVEL_INFO ;;
        "WARNING") echo $LOG_LEVEL_WARNING ;;
        "ERROR") echo $LOG_LEVEL_ERROR ;;
        *) echo $LOG_LEVEL_INFO ;;
    esac
}

CURRENT_LOG_LEVEL=$(get_log_level_num "$LOG_LEVEL")

# Log yozish funksiyasi
log_message() {
    local level="$1"
    local message="$2"
    local level_num=$(get_log_level_num "$level")
    
    if [ $level_num -ge $CURRENT_LOG_LEVEL ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - [$level] - $message" >> "$LOG_FILE"
        
        # Debug rejimida console-ga ham yozish
        if [ "$level" = "DEBUG" ] || [ "$level" = "ERROR" ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - [$level] - $message"
        fi
    fi
}

# Log faylini yaratib olish (agar mavjud bo'lmasa)
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    log_message "INFO" "Log fayli yaratildi: $LOG_FILE"
fi

log_message "INFO" "Memory monitoring service boshlandi"
log_message "INFO" "Konfiguratsiya fayli: $CONFIG_FILE"
log_message "DEBUG" "Monitoring sozlamalari: RAM $THRESHOLD%, interval $CHECK_INTERVAL sek"

# System ma'lumotlarini olish funksiyasi
get_system_info() {
    local hostname=$(hostname)
    local server_ip=$(hostname -I | awk '{print $1}')
    local kernel=$(uname -r)
    local uptime=$(uptime -p)
    local os_info=$(cat /etc/os-release | grep "PRETTY_NAME" | cut -d= -f2 | tr -d '"')
    local total_memory=$(free -h | awk '/^Mem:/ {print $2}')
    local total_disk=$(df -h "$DISK_PATH" | awk 'NR==2 {print $2}')
    
    echo "Hostname: $hostname"
    echo "IP: $server_ip"
    echo "OS: $os_info"
    echo "Kernel: $kernel"
    echo "Uptime: $uptime"
    echo "Total RAM: $total_memory"
    echo "Total Disk ($DISK_PATH): $total_disk"
}

# CPU foydalanishini tekshirish
check_cpu_usage() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
    local cpu_usage_int=${cpu_usage%.*}
    
    if [ "$MONITOR_CPU" = "true" ] && [ "$cpu_usage_int" -ge "$CPU_THRESHOLD" ]; then
        log_message "WARNING" "Yuqori CPU ishlatilishi: ${cpu_usage_int}%"
        return 0
    fi
    return 1
}

# Disk foydalanishini tekshirish
check_disk_usage() {
    local disk_usage=$(df -h "$DISK_PATH" | awk 'NR==2 {print $5}' | tr -d '%')
    
    if [ "$MONITOR_DISK" = "true" ] && [ "$disk_usage" -ge "$DISK_THRESHOLD" ]; then
        log_message "WARNING" "Yuqori disk ishlatilishi ($DISK_PATH): ${disk_usage}%"
        return 0
    fi
    return 1
}

# Xabar yuborish funksiyasi
send_telegram_alert() {
    local alert_type="$1"
    local usage_value="$2"
    local DATE=$(date '+%Y-%m-%d %H:%M:%S')
    local SERVER_IP=$(hostname -I | awk '{print $1}')
    local HOSTNAME=$(hostname)
    
    # Xabar matni tayyorlash
    local MESSAGE="$ALERT_MESSAGE_TITLE - *$alert_type*
📅 Sana: $DATE
🖥️ Hostname: \`$HOSTNAME\`
🌐 Server IP: \`$SERVER_IP\`
💥 $alert_type foydalanish: *${usage_value}%*"
    
    # Top jarayonlarni qo'shish (agar yoqilgan bo'lsa)
    if [ "$INCLUDE_TOP_PROCESSES" = "true" ]; then
        local processes_count=$((TOP_PROCESSES_COUNT + 1))  # +1 for header
        local TOP_PROCESSES=""
        
        case "$alert_type" in
            "RAM")
                TOP_PROCESSES=$(ps -eo pid,ppid,comm,%mem,%cpu --sort=-%mem | head -n $processes_count | awk '{printf "%s %s %s %s%% %s%%\n", $1, $2, $3, $4, $5}')
                ;;
            "CPU")
                TOP_PROCESSES=$(ps -eo pid,ppid,comm,%cpu,%mem --sort=-%cpu | head -n $processes_count | awk '{printf "%s %s %s %s%% %s%%\n", $1, $2, $3, $4, $5}')
                ;;
            "Disk")
                TOP_PROCESSES=$(du -h "$DISK_PATH"/* 2>/dev/null | sort -rh | head -n $TOP_PROCESSES_COUNT)
                ;;
        esac
        
        MESSAGE+="
🔍 Top jarayonlar:
\`\`\`
$TOP_PROCESSES
\`\`\`"
    fi
    
    # System ma'lumotlarini qo'shish
    local SYS_INFO=$(get_system_info)
    MESSAGE+="
📊 Tizim ma'lumotlari:
\`\`\`
$SYS_INFO
\`\`\`"
    
    echo "----------------------------------------" >> "$LOG_FILE"
    echo "$MESSAGE" >> "$LOG_FILE"
    
    # Telegram API orqali xabar yuborish
    local RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d chat_id="$CHAT_ID" \
        -d parse_mode="Markdown" \
        --data-urlencode "text=$MESSAGE")
    
    # API javobini tekshirish
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        log_message "INFO" "$alert_type alert xabari Telegramga muvaffaqiyatli yuborildi"
        return 0
    else
        log_message "ERROR" "Telegramga xabar yuborishda xatolik: $RESPONSE"
        return 1
    fi
}

# Asosiy monitoring halqasi
last_ram_alert_time=0
last_cpu_alert_time=0
last_disk_alert_time=0
alert_interval=$((CHECK_INTERVAL * 10))  # xabarlar orasidagi minimum vaqt (10 interval)

log_message "INFO" "Monitoring boshlandi. Interval: $CHECK_INTERVAL soniya"

while true; do
    current_time=$(date +%s)
    
    # RAM ishlatilishini tekshirish
    MEM_USAGE=$(free | awk '/Mem:/ { printf("%.0f"), $3/$2 * 100 }')
    if [ "$MEM_USAGE" -ge "$THRESHOLD" ]; then
        time_since_last_alert=$((current_time - last_ram_alert_time))
        
        if [ $time_since_last_alert -ge $alert_interval ]; then
            log_message "WARNING" "Yuqori RAM ishlatilishi: ${MEM_USAGE}%"
            send_telegram_alert "RAM" "$MEM_USAGE"
            last_ram_alert_time=$current_time
        else
            log_message "DEBUG" "RAM alert cheklandi (so'nggi xabardan $time_since_last_alert soniya o'tdi)"
        fi
    fi
    
    # CPU ishlatilishini tekshirish
    if [ "$MONITOR_CPU" = "true" ]; then
        CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
        CPU_USAGE_INT=${CPU_USAGE%.*}
        
        if [ "$CPU_USAGE_INT" -ge "$CPU_THRESHOLD" ]; then
            time_since_last_alert=$((current_time - last_cpu_alert_time))
            
            if [ $time_since_last_alert -ge $alert_interval ]; then
                log_message "WARNING" "Yuqori CPU ishlatilishi: ${CPU_USAGE_INT}%"
                send_telegram_alert "CPU" "$CPU_USAGE_INT"
                last_cpu_alert_time=$current_time
            else
                log_message "DEBUG" "CPU alert cheklandi (so'nggi xabardan $time_since_last_alert soniya o'tdi)"
            fi
        fi
    fi
    
    # Disk ishlatilishini tekshirish
    if [ "$MONITOR_DISK" = "true" ]; then
        DISK_USAGE=$(df -h "$DISK_PATH" | awk 'NR==2 {print $5}' | tr -d '%')
        
        if [ "$DISK_USAGE" -ge "$DISK_THRESHOLD" ]; then
            time_since_last_alert=$((current_time - last_disk_alert_time))
            
            if [ $time_since_last_alert -ge $alert_interval ]; then
                log_message "WARNING" "Yuqori disk ishlatilishi ($DISK_PATH): ${DISK_USAGE}%"
                send_telegram_alert "Disk" "$DISK_USAGE"
                last_disk_alert_time=$current_time
            else
                log_message "DEBUG" "Disk alert cheklandi (so'nggi xabardan $time_since_last_alert soniya o'tdi)"
            fi
        fi
    fi
    
    # Status faylini yangilash
    STATUS_FILE="/tmp/memory-monitor-status.tmp"
    echo "So'nggi tekshirish: $(date)" > "$STATUS_FILE"
    echo "RAM: ${MEM_USAGE}%" >> "$STATUS_FILE"
    [ "$MONITOR_CPU" = "true" ] && echo "CPU: ${CPU_USAGE_INT}%" >> "$STATUS_FILE"
    [ "$MONITOR_DISK" = "true" ] && echo "Disk ($DISK_PATH): ${DISK_USAGE}%" >> "$STATUS_FILE"
    
    # Belgilangan interval bo'yicha kutish
    sleep "$CHECK_INTERVAL"
done
