import qrcode
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from config import BOT_TOKEN, UPI_ID, CHANNEL_ID
import os
import datetime
import logging
import asyncio
import sqlite3

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Database
def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT,
            started_on TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_plans (
            user_id INTEGER PRIMARY KEY,
            plan TEXT,
            amount TEXT,
            activated_on TEXT
        )
    """)
    c.execute(""" 
        CREATE TABLE IF NOT EXISTS payments (
            user_id INTEGER,
            amount TEXT,
            status TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# In-memory cache for quick access
user_payments = {}
user_plans = {}
registered_users = {}

def load_users_from_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
    c = conn.cursor()
    c.execute("SELECT user_id, name, username, started_on FROM users")
    rows = c.fetchall()
    for row in rows:
        registered_users[row[0]] = {
            'name': row[1],
            'username': row[2],
            'started_on': row[3]
        }
    conn.close()

load_users_from_db()

# Plan links
PLAN_LINKS = {
    '99': 'https://t.me/+C5fJwmnGErE2MzNl',
    '199': 'https://t.me/+C5fJwmnGErE2MzNl',
    '699': 'https://t.me/+C5fJwmnGErE2MzNl'
}

# Broadcast messages
BROADCAST_MESSAGES = [
    {
        "text": "🔥 **NEW VIDEO ADDED!** 🔥\n\n"
                "🍑 **HOTTEST INDIAN CONTENT** 🍑\n\n"
                "➡️ **Desi Bhabhi Special Episode** ⬅️\n\n"
                "💦 Full HD Quality 💦\n\n"
                "🎬 **Watch Now -** `/start`\n\n"
                "⚡ *Don't miss this exclusive content!* ⚡",
        "delay_hours": 2
    },
    {
        "text": "💦 **EXCLUSIVE VIDEO DROPPED!** 💦\n\n"
                "🌶️ **Teen Indian Collection** 🌶️\n\n"
                "🔞 **18+ Adult Content** 🔞\n\n"
                "⚡ **Limited Time Offer** ⚡\n\n"
                "✅ **Tap /start to enjoy** ✅",
        "delay_hours": 4
    }
]

MAIN_CAPTION = "🥵 𝐀𝐋𝐋 𝐓𝐘𝐏𝐄 𝐏*𝐑𝐍 𝐕𝐈𝐃𝐄𝐎𝐒 𝐈𝐧𝐬𝐭𝐚𝐧𝐭 🍑💦\n\n" \
               "🫦 𝐌𝐎𝐌-𝐒𝐎𝐍🫦💦 \n🫦 𝐂𝐇*𝐋𝐃-𝐏*𝐑𝐍🫦💦 \n🫦 𝐑𝐏𝐄-𝐏*𝐑𝐍🫦💦 \n" \
               "🫦 𝐃𝐄𝐒𝐈 𝐁𝐇𝐀𝐁𝐇𝐈🫦💦 \n🫦 𝐈𝐍𝐒𝐓𝐀𝐆𝐑𝐀𝐌 𝐒𝐓𝐀𝐑🫦💦 \n🫦 𝐓𝐄𝐄𝐍 𝐈𝐍𝐃𝐈𝐀𝐍🫦💦\n" \
               "🫦 𝐁𝐑𝐎𝐓𝐇𝐄𝐑-𝐒𝐈𝐒𝐓𝐄𝐑🫦💦 \n🫦 𝐀𝐔𝐍𝐓𝐘-𝐏*𝐑𝐍🫦💦" \
               "\n\n🌚 50𝙆 + 𝙁𝙍𝙀𝙀𝙎 𝙑𝙄𝘿𝙀𝙊 𝙐𝙋𝙇𝙊𝘼𝘿 𝙄𝙉 𝙋𝙑𝙏 𝘾𝙃𝘼𝙉𝙉𝙀𝙇 \n\n🥵 𝘼𝙇𝙇 𝙏𝙃𝙀 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝙎𝙏𝙐𝙁𝙁𝙎."

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id=None):
    if chat_id is None:
        chat_id = update.effective_chat.id
    
    keyboard = [
        [
            InlineKeyboardButton("📋 VIEW PLANS", callback_data="PLANS"),
            InlineKeyboardButton("👤 MY PROFILE", callback_data="PROFILE")
        ],
        [
            InlineKeyboardButton("🛠 SUPPORT", callback_data="SUPPORT")
        ]
    ]
    
    # Check if banner exists in current directory
    banner_path = os.path.join(BASE_DIR, "banner.jpg")
    
    try:
        if os.path.exists(banner_path):
            if update.callback_query:
                await update.callback_query.message.delete()
            
            with open(banner_path, "rb") as photo:
                msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=MAIN_CAPTION,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            if update.callback_query:
                await update.callback_query.message.delete()
            
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=MAIN_CAPTION,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return msg
    except Exception as e:
        logger.error(f"Error sending main menu: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Save to database
    conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users (user_id, name, username, started_on)
        VALUES (?, ?, ?, ?)
    """, (user_id, user_name, update.effective_user.username, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    
    # Update cache
    registered_users[user_id] = {
        'name': user_name,
        'username': update.effective_user.username,
        'started_on': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    logger.info(f"New user registered: {user_id} - {user_name}")
    await send_main_menu(update, context)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    logger.info(f"Button clicked: {query.data} by user {user_id}")

    if query.data == "BROADCAST_BACK" or query.data == "BACK_TO_MAIN":
        try:
            await query.message.delete()
        except:
            pass
        await send_main_menu(update, context)
        return

    if query.data == "PLANS":
        keyboard = [
            [InlineKeyboardButton("📅 Weekly Plan - ₹99", callback_data="plan_99")],
            [InlineKeyboardButton("📆 Monthly Plan - ₹199", callback_data="plan_199")],
            [InlineKeyboardButton("💎 Yearly Plan - ₹699", callback_data="plan_699")],
            [InlineKeyboardButton("⬅️ BACK TO MAIN", callback_data="BACK_TO_MAIN")]
        ]
        
        await query.edit_message_caption(
            caption="💎 CHOOSE YOUR PLAN 💎\n\n"
                   "✨ Select the plan that suits you best:\n\n"
                   "📅 Weekly - ₹99 (7 Days)\n"
                   "📆 Monthly - ₹199 (30 Days)\n"
                   "💎 Yearly - ₹699 (365 Days)\n\n"
                   "🔥 Get access to all premium content!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "PROFILE":
        user = query.from_user
        
        # Check from database if user has plan
        conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
        c = conn.cursor()
        c.execute("SELECT plan, amount, activated_on FROM user_plans WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            plan_text = f"✅ ACTIVE\nPlan: {result[0]}\nActivated: {result[2]}"
        else:
            plan_text = "❌ NOT ACTIVE"
        
        keyboard = [
            [InlineKeyboardButton("⬅️ BACK TO MAIN", callback_data="BACK_TO_MAIN")]
        ]
        
        await query.edit_message_caption(
            caption=f"👤 MY PROFILE\n\n"
                   f"Name: {user.first_name}\n"
                   f"User ID: {user.id}\n"
                   f"Username: @{user.username if user.username else 'Not set'}\n\n"
                   f"📊 Plan Status: {plan_text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "SUPPORT":
        keyboard = [
            [InlineKeyboardButton("⬅️ BACK TO MAIN", callback_data="BACK_TO_MAIN")]
        ]
        
        await query.edit_message_caption(
            caption="🛠 SUPPORT CENTER 🛠\n\n"
                   "📞 Contact Support: @poki_help_bot\n\n"
                   "❓ FAQs:\n"
                   "• How to activate plan?\n"
                   "• Payment issues?\n"
                   "• Content access?\n\n"
                   "💬 Feel free to contact us anytime!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("plan_"):
        amount = query.data.split("_")[1]
        context.user_data['selected_amount'] = amount
        
        upi_link = f"upi://pay?pa={UPI_ID}&pn=Premium%20Plan&am={amount}&cu=INR"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(upi_link)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(SCREENSHOTS_DIR, f"qr_{amount}_{user_id}.png")
        qr_image.save(qr_path)
        
        keyboard = [
            [InlineKeyboardButton("✅ Verify Payment", callback_data="VERIFY_PAYMENT")],
            [InlineKeyboardButton("⬅️ Back to Plans", callback_data="PLANS")]
        ]
        
        with open(qr_path, "rb") as qr_file:
            await query.message.reply_photo(
                photo=qr_file,
                caption=f"💳 PAYMENT QR CODE 💳\n\n"
                       f"💰 Amount: ₹{amount}\n"
                       f"📱 UPI ID: {UPI_ID}\n\n"
                       f"🔹 Scan QR code and pay ₹{amount}\n"
                       f"🔹 After payment, click VERIFY button",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        os.remove(qr_path)
        
        try:
            await query.message.delete()
        except:
            pass

    elif query.data == "VERIFY_PAYMENT":
        amount = context.user_data.get('selected_amount', '0')
        
        if amount == '0':
            await query.message.reply_text("❌ Error: Please select a plan first.")
            return
        
        # Save payment request to database
        conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO payments (user_id, amount, status, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, amount, 'waiting_screenshot', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        user_payments[user_id] = {
            'amount': amount,
            'status': 'waiting_screenshot'
        }
        
        await query.message.reply_text(
            f"📸 Please send me your payment screenshot\n\n"
            f"💰 Amount: ₹{amount}\n\n"
            f"Please take a screenshot of the payment from your UPI app and send it here."
        )
        
        try:
            await query.message.delete()
        except:
            pass

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_payments:
        return
    
    payment_info = user_payments[user_id]
    amount = payment_info['amount']
    
    if payment_info['status'] == 'waiting_screenshot':
        if update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            screenshot_path = os.path.join(SCREENSHOTS_DIR, f"user_{user_id}_amount_{amount}.jpg")
            await photo_file.download_to_drive(screenshot_path)
            
            payment_info['screenshot_path'] = screenshot_path
            payment_info['status'] = 'waiting_name'
            
            await update.message.reply_text(
                f"✅ Screenshot received!\n\n"
                f"💰 Amount: ₹{amount}\n\n"
                f"📝 Now please send me your name\n\n"
                f"Please send the name you used to make the payment."
            )
        else:
            await update.message.reply_text(
                f"❌ Please send a screenshot!\n\n"
                f"💰 Amount: ₹{amount}\n\n"
                f"Please take a screenshot of the payment from your UPI app and send it here."
            )
    
    elif payment_info['status'] == 'waiting_name':
        user_name = update.message.text.strip()
        
        if len(user_name) < 2:
            await update.message.reply_text(
                f"❌ Please send a valid name!\n\n"
                f"Please send your full name (minimum 2 characters)."
            )
            return
        
        payment_info['user_name'] = user_name
        payment_info['user_telegram_name'] = update.effective_user.first_name
        payment_info['username'] = update.effective_user.username
        payment_info['user_id'] = user_id
        payment_info['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        payment_info['status'] = 'pending_review'
        
        await update.message.reply_text(
            f"✅ Payment details submitted!\n\n"
            f"💰 Amount: ₹{amount}\n"
            f"📝 Name: {user_name}\n\n"
            f"⏳ Please wait...\n\n"
            f"Admin will verify your payment.\n"
            f"You will receive confirmation soon."
        )
        
        channel_message = (
            f"🆕 NEW PAYMENT REQUEST\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 USER DETAILS\n"
            f"• Name: {payment_info['user_telegram_name']}\n"
            f"• Username: @{payment_info['username'] if payment_info['username'] else 'Not set'}\n"
            f"• User ID: {user_id}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 PAYMENT DETAILS\n"
            f"• Amount: ₹{amount}\n"
            f"• Name on UPI: {user_name}\n"
            f"• Time: {payment_info['timestamp']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📸 Payment Screenshot:"
        )
        
        admin_keyboard = [
            [
                InlineKeyboardButton("✅ APPROVE", callback_data=f"APPROVE_{user_id}_{amount}"),
                InlineKeyboardButton("❌ REJECT", callback_data=f"REJECT_{user_id}_{amount}")
            ]
        ]
        
        try:
            with open(payment_info['screenshot_path'], 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo,
                    caption=channel_message,
                    reply_markup=InlineKeyboardMarkup(admin_keyboard)
                )
            logger.info(f"Payment request sent to channel for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send to channel: {e}")
            await update.message.reply_text("⚠️ Technical error! Please contact support.")

async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_")
        if len(parts) < 3:
            logger.error(f"Invalid approve data: {query.data}")
            await query.answer("Error: Invalid data!")
            return
            
        target_user_id = int(parts[1])
        amount = parts[2]
        
        plan_link = PLAN_LINKS.get(amount, "https://t.me/poki_mms_bot")
        
        # Save plan to database
        conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO user_plans (user_id, plan, amount, activated_on)
            VALUES (?, ?, ?, ?)
        """, (target_user_id, f"₹{amount} Plan", amount, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        # Update cache
        user_plans[target_user_id] = {
            'plan': f"₹{amount} Plan",
            'amount': amount,
            'activated_on': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ PAYMENT APPROVED! ✅\n\n"
                     f"💰 Amount: ₹{amount}\n\n"
                     f"🎉 Congratulations! Your payment has been verified.\n"
                     f"Your plan is now ACTIVE!\n\n"
                     f"📱 Access your premium content here:\n"
                     f"{plan_link}\n\n"
                     f"Thank you for your purchase!"
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        
        try:
            await query.message.edit_caption(
                caption=f"✅ PAYMENT APPROVED! ✅\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 User ID: {target_user_id}\n"
                        f"💰 Amount: ₹{amount}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"✅ Status: APPROVED\n"
                        f"⏰ Approved on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            try:
                await query.message.edit_reply_markup(reply_markup=None)
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to update channel message: {e}")
        
        # Clean up
        if target_user_id in user_payments:
            if 'screenshot_path' in user_payments[target_user_id]:
                try:
                    os.remove(user_payments[target_user_id]['screenshot_path'])
                except:
                    pass
            del user_payments[target_user_id]
        
        # Update payment status in database
        conn = sqlite3.connect(os.path.join(BASE_DIR, "database.db"))
        c = conn.cursor()
        c.execute("UPDATE payments SET status = 'approved' WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        await query.answer("Payment approved! User notified.")
        
    except Exception as e:
        logger.error(f"Error in approve_payment: {e}")
        await query.answer("Error processing approval!")

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_")
        if len(parts) < 3:
            logger.error(f"Invalid reject data: {query.data}")
            await query.answer("Error: Invalid data!")
            return
            
        target_user_id = int(parts[1])
        amount = parts[2]
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"❌ PAYMENT FAILED ❌\n\n"
                     f"💰 Amount: ₹{amount}\n\n"
                     f"❌ Transaction Failed!\n\n"
                     f"Your payment could not be verified.\n\n"
                     f"🔄 Please try again: /start\n\n"
                     f"📞 Need help? Contact: @poki_mms_bot"
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        
        try:
            await query.message.edit_caption(
                caption=f"❌ PAYMENT REJECTED! ❌\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 User ID: {target_user_id}\n"
                        f"💰 Amount: ₹{amount}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"❌ Status: REJECTED\n"
                        f"⏰ Rejected on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            try:
                await query.message.edit_reply_markup(reply_markup=None)
            except:
                pass
        except Exception as e:
            logger.error(f"Failed to update channel message: {e}")
        
    
