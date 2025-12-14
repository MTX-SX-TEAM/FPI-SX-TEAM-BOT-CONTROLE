import requests
import json
import logging
import sys
import os
import threading
import time
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, filters, CallbackQueryHandler, MessageHandler, ConversationHandler
from telegram.constants import ParseMode

# ==============================================================================
# ⚜️ --- الإعدادات الرئيسية والتوكنات --- ⚜️
# ==============================================================================

# --- إعدادات البوت الأساسي ---
TOKEN = "8293311446:AAFeyTfPiOy3-SWSjspbwtc8L7H37-b28y0"  # <-- ضع توكن البوت هنا
OWNER_ID = 7375963526  # <-- ضع معرف المالك الرئيسي هنا

# --- معلومات البوت والروابط ---
BOT_NAME = "𝐅𝐏𝐈 𝐒𝐗 𝐓𝐄𝐀𝐌 모"
DEVELOPER_NAME = "𝐅𝐏𝐈 𝐒𝐗 𝐀𝐘𝐎𝐔𝐁 모"
DEVELOPER_USERNAME = "noseyrobot"
CHANNEL_LINK = "https://t.me/T_z_X_team"
GROUP_LINK = "https://t.me/MTX_SX_CHAT_TEAM"
WELCOME_IMAGE_URL = "https://i.ibb.co/PZ1hLRQx/file-00000000eca072439f53c045fa767c89-1.png"

# --- إعدادات البروكسي (اختياري) ---
# ضع رابط البروكسي هنا إذا كنت تحتاجه (مثال: "http://user:pass@ip:port")
PROXY_URL = None # تم تعطيل البروكسي لتجنب مشاكل الاتصال 

# --- إعدادات بوت الأصدقاء ---
ALLOWED_USERS = [OWNER_ID]
ALLOWED_GROUPS = [-1002928032223]

# --- الحسابات العشوائية لإرسال الطلبات ---
ACCOUNTS_RANDOM = {
    "410082": "40DF496E12E241022B3FA20FC",
    "410199": "C5A71801A5A41E17934BA0B3F16A9CAC0E0666",
    "41673": "F386621ED8485FAEF8D7C5855E8A2B53E"
}

# --- حسابات الأدمن (للاختيار عند الإضافة) ---
ADMIN_ACCOUNTS = {
    "1": {"name": "FPI SX BOT", "uid": "4315618979", "pass": "604D6D707361F19D20192E2891D126388F175B555ABD5E25A051BF89EFB17217"},
    "2": {"name": "FPI SX BOT V1", "uid": "4315618979", "pass": "604D6D707361F19D20192E2891D126388F175B555ABD5E25A051BF89EFB17217"},
    "3": {"name": "FPI SX BIT VIP", "uid": "4315618979", "pass": "604D6D707361F19D20192E2891D126388F175B555ABD5E25A051BF89EFB17217"}
}

# --- روابط API ---
INFO_API_URL = "http://217.154.161.167:10152/info="
ADD_FRIEND_API_URL = "https://lnc-yasser-api-add-yr.vercel.app/add/{acc_uid}/{acc_pass}/{target_uid}"
REMOVE_FRIEND_API_URL = "https://lnc-yasser-api-remove.vercel.app/remove/{acc_uid}/{acc_pass}/{uid}"
SPM_MSG_API_URL = "https://s1x-amine-spm-msg.vercel.app/msg"
CHECK_BAN_API_URL = "https://amin-team-api.vercel.app/check_banned"
GHOST_API_URL = "http://217.154.239.23:14008/ghost"
REGION_API_URL = "https://danger-info-alpha.vercel.app/region"
OUTFIT_API_URL = "https://danger-info-alpha.vercel.app/outfit-image"
BANNER_API_URL = "https://danger-banner.vercel.app/banner"

# --- مفاتيح API (إذا لزم الأمر) ---
DANGER_INFO_KEY = "DANGERxINFO"
DANGER_OUTFIT_KEY = "DANGER-OUTFIT"

# --- ملفات التخزين ---
ADMINS_FILE = "admins.json"
ACTIVE_CHATS_FILE = "active_chats.json"
FRIENDS_FILE = "friends.json"
LAST_ADD_FILE = "last_add.json"

# --- إعدادات التسجيل ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================================================================
# ⚜️ --- الدوال المساعدة وإدارة الملفات --- ⚜️
# ==============================================================================

def load_json_data(filename: str, default_value=None):
    if default_value is None: default_value = {}
    try:
        with open(filename, 'r') as f:
            content = f.read()
            if not content: return default_value
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        save_json_data(filename, default_value)
        return default_value

def save_json_data(filename: str, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# --- تحميل البيانات عند بدء التشغيل ---
ADMIN_IDS = load_json_data(ADMINS_FILE, [])
if OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.append(OWNER_ID)
    save_json_data(ADMINS_FILE, ADMIN_IDS)
ACTIVE_CHATS = load_json_data(ACTIVE_CHATS_FILE, [])
FRIENDS = load_json_data(FRIENDS_FILE, {})
LAST_ADD = load_json_data(LAST_ADD_FILE, {})

# ==============================================================================
# ⚜️ --- دوال الصلاحيات والتحقق --- ⚜️
# ==============================================================================

async def is_owner(update: Update) -> bool:
    return update.effective_user.id == OWNER_ID

async def is_bot_admin(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS

async def is_friend_command_allowed(update: Update) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        return user_id in ALLOWED_USERS
    return chat_id in ALLOWED_GROUPS

# ==============================================================================
# ⚜️ --- الواجهة الرئيسية والأوامر الأساسية --- ⚜️
# ==============================================================================

async def show_home_interface(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    caption = (
        f"👑━━━━━━━━━━━━━━━━━━━━━━👑\n"
        f"✨ مرحباً بك أيها <b>{user.mention_html()}</b> في مملكة البوت:\n"
        f"💎 <b>{BOT_NAME}</b> 💎\n\n"
        f"نحن هنا لخدمتك بأرقى وأقوى الخدمات الحصرية. استكشف القائمة الملكية للأوامر أدناه.\n\n"
        f"<b>⚜️ المطور الملكي:</b> {DEVELOPER_NAME}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    keyboard = [
        [InlineKeyboardButton("⚔️ قائمة الأوامر الملكية ⚔️", callback_data='show_commands')],
        [
            InlineKeyboardButton("📢 قناة الأوامر", url=CHANNEL_LINK),
            InlineKeyboardButton("👥 مجموعة النخبة", url=GROUP_LINK)
        ],
        [InlineKeyboardButton("👑 تواصل مع المطور 👑", url=f"https://t.me/{DEVELOPER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_caption(caption=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_photo(
            photo=WELCOME_IMAGE_URL,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def show_commands_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    commands_text = (
        "👑━━━━━━━━━━━━━━━━━━━━━━👑\n"
        "⚔️ <b>قائمة الأوامر الملكية المتاحة</b> ⚔️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "🛡️ <b>الأوامر العامة:</b>\n"
        "• <code>/info &lt;UID&gt;</code> - 🔍 جلب معلومات لاعب.\n"
        "• <code>/add &lt;UID&gt; &lt;Days&gt;</code> - ➕ إضافة صديق.\n"
        "• <code>/list</code> - 📜 عرض قائمة الأصدقاء.\n"
        "• <code>/chekban &lt;UID&gt;</code> - 🚫 التحقق من حظر الحساب.\n"
        "• <code>/region &lt;UID&gt;</code> - 🌍 معرفة منطقة الحساب.\n"
        "• <code>/outfit &lt;UID&gt;</code> - 👕 عرض صورة طقم اللاعب.\n"
        "• <code>/banner &lt;UID&gt;</code> - 🖼️ عرض صورة بانر اللاعب.\n\n"
        
        "✨ <b>أوامر النخبة الإضافية:</b>\n"
        "• <code>/spmmsg &lt;TeamCode&gt; &lt;Msg&gt;</code> - 💣 إرسال رسالة سبام.\n"
        "• <code>/ghost &lt;Name&gt; &lt;TeamCode&gt;</code> - 👻 إضافة شبح.\n\n"
        
        "🔑 <b>أوامر المشرفين:</b>\n"
        "• <code>/on</code> - ✅ تفعيل البوت في المجموعة.\n"
        "• <code>/off</code> - ❌ إلغاء تفعيل البوت.\n"
        "• <code>/admins</code> - 👥 عرض قائمة مشرفي البوت.\n\n"
        
        "👑 <b>أوامر المالك الأسمى:</b>\n"
        "• <code>/addadmin &lt;UID&gt;</code> - ➕ إضافة مشرف للبوت.\n"
        "• <code>/deladmin &lt;UID&gt;</code> - ➖ إزالة مشرف من البوت.\n"
        "• <code>/remove &lt;UID&gt;</code> - 🗑️ حذف صديق من القائمة.\n\n"
        "👑━━━━━━━━━━━━━━━━━━━━━━👑"
    )
    keyboard = [[InlineKeyboardButton("🔙 العودة إلى القائمة الرئيسية 🔙", callback_data='back_to_home')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_caption(
        caption=commands_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

# ==============================================================================
# ⚜️ --- دوال الأصدقاء (Add, Remove, List) --- ⚜️
# ==============================================================================

CHOOSE_ACCOUNT = 0

def get_random_account():
    uid = random.choice(list(ACCOUNTS_RANDOM.keys()))
    password = ACCOUNTS_RANDOM[uid]
    return uid, password

def get_account_name(uid):
    for acc in ADMIN_ACCOUNTS.values():
        if acc["uid"] == uid: return acc["name"]
    return "حساب عشوائي"

def format_remaining_time(remove_time_iso: str) -> str:
    try:
        remove_time = datetime.fromisoformat(remove_time_iso)
        remaining = remove_time - datetime.now()
        if remaining.total_seconds() <= 0: return "⛔ انتهت الصلاحية"
        days, rem = divmod(remaining.total_seconds(), 86400)
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        return f"{int(days)} يوم و {int(hours)} ساعة و {int(minutes)} دقيقة"
    except (ValueError, TypeError):
        return "تاريخ غير صالح"

async def add_friend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return ConversationHandler.END

    try:
        _, target_uid, days_str = update.message.text.split()
        days = int(days_str)
        if not target_uid.isdigit(): raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text("🚫 الصيغة: <code>/add &lt;UID&gt; &lt;Days&gt;</code>", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    context.user_data['target_uid'] = target_uid
    context.user_data['days'] = days

    if update.effective_user.id == OWNER_ID:
        options_text = "اختر الحساب:\n" + "\n".join([f"{k}️⃣ {v['name']}" for k, v in ADMIN_ACCOUNTS.items()])
        await update.message.reply_text(options_text)
        return CHOOSE_ACCOUNT
    else:
        user_id_str = str(update.effective_user.id)
        if user_id_str in LAST_ADD:
            last_time = datetime.fromisoformat(LAST_ADD[user_id_str])
            if datetime.now() - last_time < timedelta(hours=5):
                await update.message.reply_text("❌ يجب الانتظار 5 ساعات بين كل عملية إضافة.")
                return ConversationHandler.END
        
        await update.message.reply_text("⏳ جاري محاولة الإضافة بحساب عشوائي...")
        await execute_add_friend(update, context, None)
        return ConversationHandler.END

async def choose_account_for_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        choice = update.message.text.strip()
        if choice not in ADMIN_ACCOUNTS:
            await update.message.reply_text("❌ اختيار غير صالح. يرجى إدخال رقم الحساب.")
            return CHOOSE_ACCOUNT
        
        await update.message.reply_text(f"⏳ جاري محاولة الإضافة بحساب {ADMIN_ACCOUNTS[choice]['name']}...")
        await execute_add_friend(update, context, choice)
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"خطأ في اختيار الحساب: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع.")
        return ConversationHandler.END

async def execute_add_friend(update: Update, context: ContextTypes.DEFAULT_TYPE, account_key: str = None) -> None:
    target_uid = context.user_data['target_uid']
    days = context.user_data['days']
    user_id = update.effective_user.id
    
    if account_key:
        acc_uid = ADMIN_ACCOUNTS[account_key]['uid']
        acc_pass = ADMIN_ACCOUNTS[account_key]['pass']
    else:
        acc_uid, acc_pass = get_random_account()
    
    url = ADD_FRIEND_API_URL.format(acc_uid=acc_uid, acc_pass=acc_pass, target_uid=target_uid)
    
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            remove_time = datetime.now() + timedelta(days=days)
            remove_time_iso = remove_time.isoformat()
            
            FRIENDS[target_uid] = {
                "user_id": user_id,
                "add_time": datetime.now().isoformat(),
                "remove_time": remove_time_iso,
                "account_uid": acc_uid
            }
            save_json_data(FRIENDS_FILE, FRIENDS)
            
            LAST_ADD[str(user_id)] = datetime.now().isoformat()
            save_json_data(LAST_ADD_FILE, LAST_ADD)
            
            remaining_time = format_remaining_time(remove_time_iso)
            
            await update.message.reply_text(
                f"✅ تم إرسال طلب الصداقة بنجاح للاعب <code>{target_uid}</code>.\n"
                f"⏱️ **مدة الصداقة:** {days} أيام.\n"
                f"⏳ **الوقت المتبقي:** {remaining_time}.\n"
                f"👤 **الحساب المستخدم:** {get_account_name(acc_uid)}.",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(f"❌ فشل إرسال الطلب: {data.get('message', 'خطأ غير معروف')}")
            
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ خطأ في الاتصال بالـ API: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في execute_add_friend: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء معالجة الطلب.")

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("✅ تم إلغاء العملية.")
    return ConversationHandler.END

async def list_friends_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return

    user_id = update.effective_user.id
    user_friends = {uid: data for uid, data in FRIENDS.items() if data['user_id'] == user_id}
    
    if not user_friends:
        await update.message.reply_text("❌ ليس لديك أي أصدقاء مضافين حاليًا.")
        return

    message = "📋 <b>قائمة الأصدقاء المضافين:</b>\n\n"
    for uid, data in user_friends.items():
        remaining = format_remaining_time(data['remove_time'])
        message += (
            f"🆔 <code>{uid}</code>\n"
            f"⏳ **الوقت المتبقي:** {remaining}\n"
            f"👤 **الحساب المستخدم:** {get_account_name(data['account_uid'])}\n"
            f"--------------------------------------\n"
        )
    
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

async def remove_friend_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update):
        await update.message.reply_text("❌ هذا الأمر مخصص لمالك البوت فقط.")
        return
    
    try:
        uid = context.args[0]
        if uid not in FRIENDS:
            await update.message.reply_text(f"❌ اللاعب <code>{uid}</code> غير موجود في قائمة الأصدقاء المضافة.", parse_mode=ParseMode.HTML)
            return
        
        friend_data = FRIENDS[uid]
        acc_uid = friend_data['account_uid']
        
        # البحث عن بيانات الحساب المستخدم للإزالة
        account_info = next((acc for acc in ADMIN_ACCOUNTS.values() if acc['uid'] == acc_uid), None)
        if not account_info:
            # إذا لم يتم العثور على الحساب في قائمة الأدمن، نستخدم حساب عشوائي للإزالة
            acc_uid, acc_pass = get_random_account()
            account_name = "حساب عشوائي"
        else:
            acc_pass = account_info['pass']
            account_name = account_info['name']
            
        url = REMOVE_FRIEND_API_URL.format(acc_uid=acc_uid, acc_pass=acc_pass, uid=uid)
        
        processing_message = await update.message.reply_text(f"⏳ جاري محاولة إزالة اللاعب <code>{uid}</code> باستخدام {account_name}...", parse_mode=ParseMode.HTML)
        
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            del FRIENDS[uid]
            save_json_data(FRIENDS_FILE, FRIENDS)
            await processing_message.edit_text(f"✅ تم إزالة اللاعب <code>{uid}</code> بنجاح.", parse_mode=ParseMode.HTML)
        else:
            await processing_message.edit_text(f"❌ فشل إزالة اللاعب <code>{uid}</code>: {data.get('message', 'خطأ غير معروف')}", parse_mode=ParseMode.HTML)
            
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 الصيغة: <code>/remove &lt;UID&gt;</code>", parse_mode=ParseMode.HTML)
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ خطأ في الاتصال بالـ API: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في remove_friend_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء معالجة الطلب.")

# ==============================================================================
# ⚜️ --- أوامر إضافية (Spam, CheckBan, Ghost) --- ⚜️
# ==============================================================================

async def spam_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return
    
    try:
        _, team_code, *msg_parts = update.message.text.split()
        message_text = " ".join(msg_parts)
        
        if not team_code.isdigit() or not message_text:
            raise ValueError
        
        url = SPM_MSG_API_URL
        payload = {
            "team_code": team_code,
            "msg": message_text
        }
        
        processing_message = await update.message.reply_text("⏳ جاري إرسال رسالة السبام...")
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            await processing_message.edit_text(f"✅ تم إرسال رسالة السبام بنجاح إلى الفريق <code>{team_code}</code>.", parse_mode=ParseMode.HTML)
        else:
            await processing_message.edit_text(f"❌ فشل إرسال رسالة السبام: {data.get('message', 'خطأ غير معروف')}", parse_mode=ParseMode.HTML)
            
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 الصيغة: <code>/spmmsg &lt;TeamCode&gt; &lt;Msg&gt;</code>", parse_mode=ParseMode.HTML)
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ خطأ في الاتصال بالـ API: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في spam_message_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء معالجة الطلب.")

async def check_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return
    
    try:
        uid = context.args[0]
        if not uid.isdigit(): raise ValueError
        
        url = CHECK_BAN_API_URL
        params = {"uid": uid}
        
        processing_message = await update.message.reply_text(f"⏳ جاري التحقق من حالة حظر اللاعب <code>{uid}</code>...", parse_mode=ParseMode.HTML)
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        is_banned = data.get("banned", False)
        message = f"🆔 اللاعب <code>{uid}</code>\n"
        if is_banned:
            message += "🚫 **الحالة:** محظور (Banned) ❌"
        else:
            message += "✅ **الحالة:** غير محظور (Not Banned) ✅"
            
        await processing_message.edit_text(message, parse_mode=ParseMode.HTML)
            
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 الصيغة: <code>/chekban &lt;UID&gt;</code>", parse_mode=ParseMode.HTML)
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ خطأ في الاتصال بالـ API: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في check_ban_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء معالجة الطلب.")

async def ghost_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return
    
    try:
        _, name, team_code = update.message.text.split()
        
        if not team_code.isdigit() or not name:
            raise ValueError
        
        url = GHOST_API_URL
        payload = {
            "name": name,
            "team_code": team_code
        }
        
        processing_message = await update.message.reply_text(f"⏳ جاري محاولة إضافة الشبح <code>{name}</code> إلى الفريق <code>{team_code}</code>...", parse_mode=ParseMode.HTML)
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "success":
            await processing_message.edit_text(f"✅ تم إضافة الشبح <code>{name}</code> بنجاح.", parse_mode=ParseMode.HTML)
        else:
            await processing_message.edit_text(f"❌ فشل إضافة الشبح: {data.get('message', 'خطأ غير معروف')}", parse_mode=ParseMode.HTML)
            
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 الصيغة: <code>/ghost &lt;Name&gt; &lt;TeamCode&gt;</code>", parse_mode=ParseMode.HTML)
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ خطأ في الاتصال بالـ API: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في ghost_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء معالجة الطلب.")

# ==============================================================================
# ⚜️ --- أوامر جلب الصور والمعلومات (Region, Outfit, Banner) --- ⚜️
# ==============================================================================

async def region_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return
    
    try:
        uid = context.args[0]
        if not uid.isdigit(): raise ValueError
        
        url = REGION_API_URL
        params = {"uid": uid, "key": DANGER_INFO_KEY}
        
        processing_message = await update.message.reply_text(f"⏳ جاري جلب منطقة اللاعب <code>{uid}</code>...", parse_mode=ParseMode.HTML)
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        region_name = data.get("region", "غير متوفر")
        
        await processing_message.edit_text(
            f"🆔 اللاعب <code>{uid}</code>\n"
            f"🌍 **المنطقة:** {region_name}",
            parse_mode=ParseMode.HTML
        )
            
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 الصيغة: <code>/region &lt;UID&gt;</code>", parse_mode=ParseMode.HTML)
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ خطأ في الاتصال بالـ API: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في region_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء معالجة الطلب.")

async def banner_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return
    
    try:
        uid = context.args[0]
        if not uid.isdigit(): raise ValueError
        
        url = BANNER_API_URL
        params = {"uid": uid}
        
        processing_message = await update.message.reply_text(f"⏳ جاري جلب بانر اللاعب <code>{uid}</code>...", parse_mode=ParseMode.HTML)
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        # Telegram can handle sending the image directly from the URL
        await update.message.reply_photo(photo=response.url, caption=f"بانر اللاعب <code>{uid}</code>", parse_mode=ParseMode.HTML)
        await processing_message.delete()
        
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 الصيغة: <code>/banner &lt;UID&gt;</code>", parse_mode=ParseMode.HTML)
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ فشل جلب الصورة: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع في banner_command: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء معالجة الطلب.")

async def outfit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_friend_command_allowed(update):
        await update.message.reply_text("🚫 هذا الأمر غير مسموح به في هذه المحادثة.")
        return
    
    try:
        uid = context.args[0]
        if not uid.isdigit(): raise ValueError
        
        # Note: This API seems to return the image data directly, not a URL.
        # The original code attempts to use response.raw, which is correct for file-like objects.
        params = {"uid": uid, "key": DANGER_OUTFIT_KEY}
        response = requests.get(OUTFIT_API_URL, params=params, timeout=15, stream=True)
        response.raise_for_status()
        
        # The original code used update.message.reply_photo(photo=response.raw)
        # which is the correct way to send a photo from a stream.
        await update.message.reply_photo(photo=response.raw, caption=f"طقم اللاعب <code>{uid}</code>", parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.message.reply_text("🚫 الصيغة: <code>/outfit &lt;UID&gt;</code>", parse_mode=ParseMode.HTML)
    except requests.RequestException as e:
        await update.message.reply_text(f"❌ فشل جلب الصورة: {e}")

# ==============================================================================
# ⚜️ --- أمر المعلومات الرئيسي (Info) --- ⚜️
# ==============================================================================

def fetch_user_info(uid: str) -> str:
    url = f"{INFO_API_URL}{uid}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            basic_info = data.get("basicInfo", {})
            clan_info = data.get("clanBasicInfo", {})
            social_info = data.get("socialInfo", {})
            credit_info = data.get("creditScoreInfo", {})

            nickname = basic_info.get("nickname", "غير متوفر")
            region = basic_info.get("region", "غير متوفر")
            level = basic_info.get("level", "غير متوفر")
            exp = basic_info.get("exp", "غير متوفر")
            liked = basic_info.get("liked", "غير متوفر")
            credit_score = credit_info.get("creditScore", "غير متوفر")
            
            rank = basic_info.get("rank", "غير متوفر")
            ranking_points = basic_info.get("rankingPoints", "غير متوفر")
            max_rank = basic_info.get("maxRank", "غير متوفر")
            
            cs_rank = basic_info.get("csRank", "غير متوفر")
            cs_ranking_points = basic_info.get("csRankingPoints", "غير متوفر")
            cs_max_rank = basic_info.get("csMaxRank", "غير متوفر")
            
            clan_name = clan_info.get("clanName", "لا يوجد عشيرة")
            clan_level = clan_info.get("clanLevel", "غير متوفر")
            
            signature = social_info.get("signature", "لا يوجد توقيع")

            try: create_date = datetime.fromtimestamp(int(basic_info.get("createAt", 0))).strftime('%Y-%m-%d %H:%M:%S')
            except: create_date = "غير متوفر"
            
            try: last_login_date = datetime.fromtimestamp(int(basic_info.get("lastLoginAt", 0))).strftime('%Y-%m-%d %H:%M:%S')
            except: last_login_date = "غير متوفر"

            message = (
                f"👑━━━<b> ملف اللاعب </b>━━━👑\n"
                f"✨ <b>الاسم:</b> {nickname}\n"
                f"🆔 <b>المعرف (UID):</b> <code>{uid}</code>\n"
                f"🌍 <b>المنطقة:</b> {region}\n"
                f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"📊 <b>الإحصائيات الأساسية</b>\n"
                f"⭐ <b>المستوى:</b> {level}\n"
                f"🔥 <b>الخبرة (EXP):</b> {exp}\n"
                f"❤️ <b>الإعجابات:</b> {liked}\n"
                f"🛡️ <b>نقاط السمعة:</b> {credit_score}\n"
                f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"⚔️ <b>رتبة الباتل رويال (BR)</b>\n"
                f"🏆 <b>الرتبة الحالية:</b> {rank}\n"
                f"📈 <b>نقاط الرتبة:</b> {ranking_points}\n"
                f"🔝 <b>أعلى رتبة:</b> {max_rank}\n"
                f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"💥 <b>رتبة الكلاش سكواد (CS)</b>\n"
                f"🏅 <b>الرتبة الحالية:</b> {cs_rank}\n"
                f"📉 <b>نقاط الرتبة:</b> {cs_ranking_points}\n"
                f"⬆️ <b>أعلى رتبة:</b> {cs_max_rank}\n"
                f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"🏰 <b>معلومات العشيرة</b>\n"
                f"⚜️ <b>اسم العشيرة:</b> {clan_name}\n"
                f"🆙 <b>مستوى العشيرة:</b> {clan_level}\n"
                f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                f"🕰️ <b>التواريخ</b>\n"
                f"🗓️ <b>تاريخ الإنشاء:</b> {create_date}\n"
                f"🚪 <b>آخر تسجيل دخول:</b> {last_login_date}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"✍️ <b>التوقيع:</b>\n{signature}"
            )
            return message
            
        elif response.status_code == 404:
            return f"❌ <b>خطأ:</b> لم يتم العثور على اللاعب <code>{uid}</code>."
        else:
            return f"❌ <b>خطأ API:</b> الرمز: {response.status_code}"
    except requests.RequestException:
        return "❌ <b>خطأ اتصال:</b> فشل الاتصال بالـ API."
    except (json.JSONDecodeError, KeyError):
        return "❌ <b>خطأ بيانات:</b> استجابة API غير مكتملة."

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != 'private' and update.effective_chat.id not in ACTIVE_CHATS:
        await update.message.reply_text("❌ البوت غير مفعل هنا. استخدم /on لتفعيله.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ <b>خطأ:</b> أدخل UID.\nمثال: <code>/info 123456789</code>", parse_mode=ParseMode.HTML)
        return
    uid = context.args[0]
    if not uid.isdigit():
        await update.message.reply_text("❌ <b>خطأ:</b> UID يجب أن يكون رقمًا.", parse_mode=ParseMode.HTML)
        return
    
    processing_message = await update.message.reply_text(f"⏳ جاري جلب معلومات <code>{uid}</code>...", parse_mode=ParseMode.HTML)
    result_message = fetch_user_info(uid)
    
    try:
        await processing_message.edit_text(result_message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"فشل تعديل الرسالة: {e}.")
        await update.message.reply_text(result_message, parse_mode=ParseMode.HTML)

# ==============================================================================
# ⚜️ --- أوامر الإدارة (Admin Commands) --- ⚜️
# ==============================================================================

async def activate_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_bot_admin(update):
        await update.message.reply_text("❌ هذا الأمر لمشرفي البوت فقط.")
        return

    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_CHATS:
        await update.message.reply_text("✅ البوت مفعل بالفعل هنا.")
    else:
        ACTIVE_CHATS.append(chat_id)
        save_json_data(ACTIVE_CHATS_FILE, ACTIVE_CHATS)
        await update.message.reply_text("✅ تم تفعيل البوت بنجاح.")

async def deactivate_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_bot_admin(update):
        await update.message.reply_text("❌ هذا الأمر لمشرفي البوت فقط.")
        return
        
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_CHATS:
        ACTIVE_CHATS.remove(chat_id)
        save_json_data(ACTIVE_CHATS_FILE, ACTIVE_CHATS)
        await update.message.reply_text("✅ تم إلغاء تفعيل البوت.")
    else:
        await update.message.reply_text("❌ البوت غير مفعل أصلاً.")


async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update):
        await update.message.reply_text("❌ هذا الأمر مخصص لمالك البوت فقط.")
        return
    if not context.args:
        await update.message.reply_text("استخدام الأمر: <code>/addadmin &lt;user_id&gt;</code>", parse_mode=ParseMode.HTML)
        return
    try:
        admin_id = int(context.args[0])
        if admin_id in ADMIN_IDS:
            await update.message.reply_text("✅ هذا المستخدم هو مشرف بالفعل.")
        else:
            ADMIN_IDS.append(admin_id)
            save_json_data(ADMINS_FILE, ADMIN_IDS)
            await update.message.reply_text(f"✅ تم إضافة المستخدم <code>{admin_id}</code> كمشرف جديد.", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقمًا.")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update):
        await update.message.reply_text("❌ هذا الأمر مخصص لمالك البوت فقط.")
        return
    if not context.args:
        await update.message.reply_text("استخدام الأمر: <code>/deladmin &lt;user_id&gt;</code>", parse_mode=ParseMode.HTML)
        return
    try:
        admin_id = int(context.args[0])
        if admin_id == OWNER_ID:
            await update.message.reply_text("❌ لا يمكنك إزالة مالك البوت.")
            return
        if admin_id in ADMIN_IDS:
            ADMIN_IDS.remove(admin_id)
            save_json_data(ADMINS_FILE, ADMIN_IDS)
            await update.message.reply_text(f"✅ تم إزالة المستخدم <code>{admin_id}</code> من قائمة المشرفين.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("❌ هذا المستخدم ليس مشرفًا.")
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقمًا.")

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_bot_admin(update):
        await update.message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط.")
        return
    if not ADMIN_IDS:
        await update.message.reply_text("لا يوجد مشرفون حاليًا.")
        return
    message = "📋 <b>قائمة مشرفي البوت:</b>\n"
    message += f"👑 <b>المالك:</b> <code>{OWNER_ID}</code>\n"
    other_admins = [admin_id for admin_id in ADMIN_IDS if admin_id != OWNER_ID]
    if other_admins:
        message += "👤 <b>المشرفون:</b>\n"
        for admin_id in other_admins:
            message += f"- <code>{admin_id}</code>\n"
    message += f"\n<b>العدد الإجمالي للمشرفين:</b> {len(ADMIN_IDS)}"
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

# ==============================================================================
# ⚜️ --- الوظيفة الرئيسية وتسجيل الأوامر --- ⚜️
# ==============================================================================

def main() -> None:
    """يبدأ تشغيل البوت ويسجل جميع الأوامر."""
    application = Application.builder().token(TOKEN).build()

    # --- محادثة إضافة صديق ---
    add_friend_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_friend_command)],
        states={
            CHOOSE_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_account_for_add)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # --- تسجيل الأوامر والمعالجات ---
    # الواجهة الرئيسية
    application.add_handler(CommandHandler("start", show_home_interface))
    application.add_handler(CommandHandler("help", show_home_interface))
    application.add_handler(CallbackQueryHandler(show_commands_list, pattern='^show_commands$'))
    application.add_handler(CallbackQueryHandler(show_home_interface, pattern='^back_to_home$'))

    # أوامر المعلومات والأصدقاء
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(add_friend_conv_handler)
    application.add_handler(CommandHandler("remove", remove_friend_command))
    application.add_handler(CommandHandler("list", list_friends_command))

    # الأوامر الإضافية
    application.add_handler(CommandHandler("spmmsg", spam_message_command))
    application.add_handler(CommandHandler("chekban", check_ban_command))
    application.add_handler(CommandHandler("ghost", ghost_command))
    application.add_handler(CommandHandler("region", region_command))
    application.add_handler(CommandHandler("outfit", outfit_command))
    application.add_handler(CommandHandler("banner", banner_command))

    # أوامر الإدارة
    application.add_handler(CommandHandler("on", activate_chat))
    application.add_handler(CommandHandler("off", deactivate_chat))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("deladmin", remove_admin))
    application.add_handler(CommandHandler("admins", list_admins))

    # --- بدء تشغيل البوت ---
    logger.info("تم بدء تشغيل البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
