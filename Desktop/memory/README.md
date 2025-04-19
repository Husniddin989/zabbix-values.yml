# SYSTEM MONITOR - FOYDALANISH QO'LLANMASI

## Mundarija
1. [Kirish](#1-kirish)
2. [O'rnatish](#2-ornatish)
3. [Konfiguratsiya](#3-konfiguratsiya)
4. [Xizmatni boshqarish](#4-xizmatni-boshqarish)
5. [Telegram xabarlari](#5-telegram-xabarlari)
6. [Loglar bilan ishlash](#6-loglar-bilan-ishlash)
7. [Muammolarni bartaraf etish](#7-muammolarni-bartaraf-etish)
8. [Tez-tez so'raladigan savollar](#8-tez-tez-soraladigan-savollar)

## 1. Kirish

System Monitor - bu serveringizning RAM, CPU va disk resurslarini kuzatib boruvchi va belgilangan chegaradan oshganda Telegram orqali xabar yuboruvchi dastur. Bu dastur serverlaringizni proaktiv tarzda nazorat qilish va muammolar yuzaga kelishidan oldin ularni aniqlash imkonini beradi.

### Asosiy imkoniyatlar:

- RAM foydalanishini kuzatish
- CPU foydalanishini kuzatish
- Disk foydalanishini kuzatish
- Telegram orqali xabar yuborish
- Eng ko'p resurs ishlatayotgan jarayonlar haqida ma'lumot
- Moslashuvchan konfiguratsiya
- Systemd xizmati sifatida ishlash
- Batafsil loglar

## 2. O'rnatish

System Monitor-ni o'rnatish uchun quyidagi qadamlarni bajaring:

### 2.1. Fayllarni yuklab olish

Ushbu repozitoriyani yuklab oling yoki fayllarni serveringizga ko'chiring:

```bash
git clone https://github.com/username/system-monitor.git
cd system-monitor
```

Yoki fayllarni to'g'ridan-to'g'ri yuklab oling va ularni serveringizga ko'chiring.

### 2.2. O'rnatish skriptini ishga tushirish

O'rnatish skriptini root huquqlari bilan ishga tushiring:

```bash
sudo chmod +x install.sh
sudo ./install.sh
```

O'rnatish jarayonida sizdan quyidagi ma'lumotlarni kiritish so'raladi:

- Telegram Bot Token
- Telegram Chat ID
- RAM foizi chegarasi (standart: 80%)
- Tekshirish oralig'i (standart: 60 soniya)
- CPU monitoringini yoqish/o'chirish
- CPU foizi chegarasi (standart: 90%)
- Disk monitoringini yoqish/o'chirish
- Disk foizi chegarasi (standart: 90%)
- Disk yo'li (standart: /)
- Log fayli joylashuvi
- Log darajasi (DEBUG, INFO, WARNING, ERROR)

O'rnatish muvaffaqiyatli yakunlangandan so'ng, xizmat avtomatik ravishda ishga tushadi.

### 2.3. Telegram Bot yaratish

Agar sizda Telegram bot mavjud bo'lmasa, quyidagi qadamlarni bajaring:

1. Telegram-da @BotFather ga murojaat qiling
2. `/newbot` buyrug'ini yuboring
3. Bot uchun nom kiriting
4. Bot uchun foydalanuvchi nomi kiriting (oxiri "bot" bilan tugashi kerak)
5. BotFather sizga API token beradi, uni saqlang
6. Botni guruhga qo'shing yoki shaxsiy xabar yuboring
7. Chat ID-ni olish uchun https://api.telegram.org/bot<BOT_TOKEN>/getUpdates ga murojaat qiling

## 3. Konfiguratsiya

System Monitor konfiguratsiya fayli `/etc/memory-monitor/config.conf` joylashgan. Uni tahrirlash uchun:

```bash
sudo nano /etc/memory-monitor/config.conf
```

### 3.1. Konfiguratsiya parametrlari

| Parametr | Tavsif | Standart qiymat |
|----------|--------|-----------------|
| BOT_TOKEN | Telegram Bot API tokeni | - |
| CHAT_ID | Telegram Chat ID | - |
| THRESHOLD | RAM foizi chegarasi | 80 |
| CHECK_INTERVAL | Tekshirish oralig'i (soniyalarda) | 60 |
| LOG_FILE | Log fayli joylashuvi | /var/log/memory_monitor.log |
| LOG_LEVEL | Log darajasi (DEBUG, INFO, WARNING, ERROR) | INFO |
| ALERT_MESSAGE_TITLE | Xabar sarlavhasi | 🛑 SYSTEM MONITOR ALERT |
| INCLUDE_TOP_PROCESSES | Eng ko'p resurs ishlatayotgan jarayonlarni ko'rsatish | true |
| TOP_PROCESSES_COUNT | Ko'rsatiladigan jarayonlar soni | 10 |
| MONITOR_CPU | CPU monitoringini yoqish/o'chirish | true |
| CPU_THRESHOLD | CPU foizi chegarasi | 90 |
| MONITOR_DISK | Disk monitoringini yoqish/o'chirish | true |
| DISK_THRESHOLD | Disk foizi chegarasi | 90 |
| DISK_PATH | Disk yo'li | / |

### 3.2. Konfiguratsiyani yangilash

Konfiguratsiyani o'zgartirgandan so'ng, xizmatni qayta ishga tushirish kerak:

```bash
sudo systemctl restart memory-monitor.service
```

## 4. Xizmatni boshqarish

System Monitor systemd xizmati sifatida ishlaydi. Uni boshqarish uchun quyidagi buyruqlardan foydalanishingiz mumkin:

### 4.1. Xizmat holatini tekshirish

```bash
sudo systemctl status memory-monitor.service
```

### 4.2. Xizmatni to'xtatish

```bash
sudo systemctl stop memory-monitor.service
```

### 4.3. Xizmatni ishga tushirish

```bash
sudo systemctl start memory-monitor.service
```

### 4.4. Xizmatni qayta ishga tushirish

```bash
sudo systemctl restart memory-monitor.service
```

### 4.5. Xizmatni o'chirish

```bash
sudo systemctl disable memory-monitor.service
```

### 4.6. Xizmatni yoqish

```bash
sudo systemctl enable memory-monitor.service
```

## 5. Telegram xabarlari

System Monitor belgilangan chegaradan oshganda Telegram orqali xabar yuboradi. Xabar quyidagi ma'lumotlarni o'z ichiga oladi:

- Xabar turi (RAM, CPU yoki Disk)
- Sana va vaqt
- Server nomi (hostname)
- Server IP manzili
- Resurs foydalanish foizi
- Eng ko'p resurs ishlatayotgan jarayonlar ro'yxati
- Tizim ma'lumotlari (OS, kernel, uptime, va boshqalar)

### 5.1. Xabar chastotasi

Bir xil turdagi xabarlar orasidagi minimum vaqt `CHECK_INTERVAL * 10` soniya. Bu serverdan juda ko'p xabar kelishining oldini oladi.

## 6. Loglar bilan ishlash

System Monitor barcha hodisalarni log fayliga yozib boradi. Standart log fayli `/var/log/memory_monitor.log` joylashgan.

### 6.1. Loglarni ko'rish

```bash
sudo tail -f /var/log/memory_monitor.log
```

### 6.2. Systemd loglarini ko'rish

```bash
sudo journalctl -u memory-monitor.service
```

### 6.3. Log darajalari

System Monitor quyidagi log darajalarini qo'llab-quvvatlaydi:

- DEBUG: Barcha ma'lumotlar, shu jumladan debug ma'lumotlari
- INFO: Standart operatsiyalar haqida ma'lumot
- WARNING: Ogohlantirish xabarlari (masalan, yuqori resurs foydalanishi)
- ERROR: Xatolik xabarlari

Log darajasini konfiguratsiya faylida o'zgartirishingiz mumkin.

## 7. Muammolarni bartaraf etish

### 7.1. Xizmat ishga tushmayapti

Agar xizmat ishga tushmasa, quyidagi qadamlarni bajaring:

1. Xizmat holatini tekshiring:
   ```bash
   sudo systemctl status memory-monitor.service
   ```

2. Loglarni tekshiring:
   ```bash
   sudo journalctl -u memory-monitor.service
   ```

3. Skript faylini tekshiring:
   ```bash
   sudo cat /opt/memory-monitor/memory-monitor.sh
   ```

4. Konfiguratsiya faylini tekshiring:
   ```bash
   sudo cat /etc/memory-monitor/config.conf
   ```

5. Skript faylining bajarilish huquqlarini tekshiring:
   ```bash
   sudo chmod +x /opt/memory-monitor/memory-monitor.sh
   ```

### 7.2. Telegram xabarlari kelmayapti

Agar Telegram xabarlari kelmasa, quyidagi qadamlarni bajaring:

1. BOT_TOKEN va CHAT_ID to'g'ri ekanligini tekshiring
2. Botni guruhga qo'shganingizni tekshiring
3. Botga kamida bir marta xabar yuborganingizni tekshiring
4. Loglarni tekshiring:
   ```bash
   sudo tail -f /var/log/memory_monitor.log
   ```

5. Internet ulanishini tekshiring:
   ```bash
   ping api.telegram.org
   ```

### 7.3. Xizmat juda ko'p resurs ishlatyapti

Agar xizmat juda ko'p resurs ishlatsa, tekshirish oralig'ini oshiring:

```bash
sudo nano /etc/memory-monitor/config.conf
# CHECK_INTERVAL qiymatini oshiring, masalan 300 (5 daqiqa)
sudo systemctl restart memory-monitor.service
```

## 8. Tez-tez so'raladigan savollar

### 8.1. Bir nechta serverlarni kuzatish mumkinmi?

Ha, har bir server uchun alohida System Monitor o'rnatishingiz va ularni bir xil Telegram botga ulashingiz mumkin. Xabarlarda server nomi va IP manzili ko'rsatiladi.

### 8.2. Boshqa resurslarni kuzatish mumkinmi?

Hozirda System Monitor RAM, CPU va disk resurslarini kuzatadi. Kelajakda boshqa resurslarni kuzatish imkoniyati qo'shilishi mumkin.

### 8.3. Xabar formatini o'zgartirish mumkinmi?

Ha, buning uchun `/opt/memory-monitor/memory-monitor.sh` faylini tahrirlashingiz kerak. `send_telegram_alert` funksiyasini topib, xabar formatini o'zgartirishingiz mumkin.

### 8.4. Xizmatni o'chirib qo'yish mumkinmi?

Ha, xizmatni vaqtincha to'xtatish uchun:

```bash
sudo systemctl stop memory-monitor.service
```

Xizmatni butunlay o'chirish uchun:

```bash
sudo systemctl disable memory-monitor.service
sudo systemctl stop memory-monitor.service
```

### 8.5. Konfiguratsiyani qayta o'rnatmasdan o'zgartirish mumkinmi?

Ha, `/etc/memory-monitor/config.conf` faylini tahrirlashingiz va xizmatni qayta ishga tushirishingiz mumkin:

```bash
sudo nano /etc/memory-monitor/config.conf
sudo systemctl restart memory-monitor.service
```
