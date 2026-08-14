import csv
import os
import math
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pytz
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== កំណត់ព័ត៌មាន Bot, ទីតាំង & Group ====================
BOT_TOKEN = "8910936837:AAGDMi2K8UQ_ZaX3K6XogrLcZRvNOg2-8Ss"
CAMBODIA_TZ = pytz.timezone('Asia/Phnom_Penh')
CSV_FILE = "attendance.csv"

# 🎯 ទីតាំងនៅប៉ោយប៉ែត (MH68+J6X, Krong Poi Pet)
TARGET_LAT = 13.66160
TARGET_LON = 102.56560
ALLOWED_RADIUS_METERS = 100.0  # ចម្ងាយអនុញ្ញាត ១០០ ម៉ែត្រ

# 👥 Group Chat ID របស់គ្រុប "Roeun and Y"
GROUP_CHAT_ID = -1004358845143

# រូបមន្តគណនាចម្ងាយ GPS (Haversine Formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # ម៉ែត្រ
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# បង្កើត CSV Header
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(["Telegram ID", "ឈ្មោះពេញ", "Username", "ប្រភេទ", "កាលបរិច្ឆេទ", "ម៉ោង", "Latitude", "Longitude", "ចម្ងាយ(m)", "ស្ថានភាព"])

# ដំណើរការពេលស្កេន QR Code ឬវាយ /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    action_type = "attendance"
    
    if context.args:
        if context.args[0] == "checkin":
            action_type = "checkin"
        elif context.args[0] == "checkout":
            action_type = "checkout"

    context.user_data['action_type'] = action_type

    if action_type == "checkin":
        btn_text = "🟢 ចុចទីនេះដើម្បីបញ្ជាក់វត្តមាន «ចូលធ្វើការ»"
        welcome_text = f"👋 សួស្តី {user_name}!\n\nសូមចុចប៊ូតុងខាងក្រោម ដើម្បីកត់ត្រាវត្តមាន <b>«ចូលធ្វើការ»</b>៖"
    elif action_type == "checkout":
        btn_text = "🔴 ចុចទីនេះដើម្បីបញ្ជាក់វត្តមាន «ចេញទៅផ្ទះ»"
        welcome_text = f"👋 សួស្តី {user_name}!\n\nសូមចុចប៊ូតុងខាងក្រោម ដើម្បីកត់ត្រាវត្តមាន <b>«ចេញទៅផ្ទះ»</b>៖"
    else:
        btn_text = "📍 ចុចទីនេះដើម្បីបញ្ជាក់វត្តមាន & ទីតាំង"
        welcome_text = f"👋 សួស្តី {user_name}!\n\nសូមចុចប៊ូតុងខាងក្រោម ដើម្បីកត់ត្រាវត្តមាន៖"

    location_button = KeyboardButton(text=btn_text, request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)

# ដំណើរការពេលទទួលបាន Location
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        location = update.message.location
        action_type = context.user_data.get('action_type', 'checkin')
        
        if action_type == "checkin":
            action_title = "ចូលធ្វើការ (Check-in)"
            icon = "🟢"
        elif action_type == "checkout":
            action_title = "ចេញទៅផ្ទះ (Check-out)"
            icon = "🔴"
        else:
            action_title = "វត្តមានទូទៅ"
            icon = "📍"

        user_lat = location.latitude
        user_lon = location.longitude
        
        # គណនាចម្ងាយពីអ្នកស្កេន ទៅកាន់ទីតាំង
        distance = calculate_distance(user_lat, user_lon, TARGET_LAT, TARGET_LON)
        now = datetime.now(CAMBODIA_TZ)
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%I:%M:%S %p")
        maps_link = f"https://maps.google.com/?q={user_lat},{user_lon}"
        
        # ពិនិត្យមើលចម្ងាយ (រង្វង់ ១០០ ម៉ែត្រ)
        if distance <= ALLOWED_RADIUS_METERS:
            status = "ត្រឹមត្រូវ"
            with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow([user.id, user.full_name, f"@{user.username}" if user.username else "N/A", action_title, date_str, time_str, user_lat, user_lon, f"{distance:.1f}m", status])
            
            # សារផ្ញើទៅកាន់បុគ្គលិកផ្ទាល់
            user_msg = (
                f"✅ <b>កត់ត្រា {action_title} ជោគជ័យ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>ឈ្មោះ:</b> {user.full_name}\n"
                f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str}\n"
                f"⏰ <b>ម៉ោង:</b> {time_str}\n"
                f"📍 <b>ចម្ងាយ:</b> {distance:.1f} ម៉ែត្រ (ត្រឹមត្រូវ)\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✨ សូមអរគុណ!"
            )
            await update.message.reply_text(user_msg, parse_mode="HTML", disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())

            # សារផ្ញើជូនដំណឹងស្វ័យប្រវត្តិទៅក្នុង Telegram Group
            if GROUP_CHAT_ID:
                group_msg = (
                    f"🔔 <b>របាយការណ៍វត្តមាន: {icon} {action_title}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>បុគ្គលិក:</b> {user.full_name} ({f'@{user.username}' if user.username else 'គ្មាន Username'})\n"
                    f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str}\n"
                    f"⏰ <b>ម៉ោង:</b> {time_str}\n"
                    f"📍 <b>ទីតាំង:</b> <a href='{maps_link}'>ចុចមើលលើ Maps</a>\n"
                    f"📏 <b>គម្លាត:</b> {distance:.1f} ម៉ែត្រ\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"✅ <b>ស្ថានភាព:</b> ត្រឹមត្រូវ"
                )
                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_msg, parse_mode="HTML", disable_web_page_preview=True)

        else:
            # ករណីស្កេនខុសទីតាំង
            reject_msg = (
                f"❌ <b>មិនអាចកត់ត្រាបានទេ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ អ្នកមិនស្ថិតនៅក្នុងទីតាំងដែលបានកំណត់ទេ!\n"
                f"📍 <b>ចម្ងាយរបស់អ្នក:</b> {distance:.1f} ម៉ែត្រពីទីតាំង\n"
                f"📏 <b>ចម្ងាយអនុញ្ញាត:</b> ត្រឹម {ALLOWED_RADIUS_METERS:.0f} ម៉ែត្រប៉ុណ្ណោះ។\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"សូមអញ្ជើញមកដល់កន្លែងធ្វើការផ្ទាល់រួចស្កេនម្តងទៀត!"
            )
            await update.message.reply_text(reject_msg, parse_mode="HTML", disable_web_page_preview=True, reply_markup=ReplyKeyboardRemove())

    except Exception as e:
        print(f"Error: {e}")

# Web Server ជំនួយសម្រាប់ Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

def main():
    print("🤖 Bot កំពុងដំណើរការ...")
    threading.Thread(target=run_web_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.run_polling()

if __name__ == '__main__':
    main()
