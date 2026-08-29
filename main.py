import os
import subprocess
import logging
import shutil
import ast
import re
import sys
from telebot import TeleBot, types

# --- AYARLAR ---
BOT_TOKEN = "8683988458:AAEsW3O_uGoT5VWfpuTLwq1yK9I-zSlHoBM"
ADMIN_ID = 8629520501
CHANNEL_ID = "@tgfreehosting" 
BASE_DIR = os.path.expanduser("~/termux")
TEMP_DIR = os.path.expanduser("~/temp_bots")
bot = TeleBot(BOT_TOKEN)

# Klasörleri oluştur ve TEMP_DIR'i her açılışta temizle
for folder in [BASE_DIR, TEMP_DIR]:
    if not os.path.exists(folder): os.makedirs(folder)
else:
    # Başlangıçta TEMP_DIR içini tamamen boşalt (Otomatik temizlik)
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        try:
            if os.path.isfile(file_path): os.unlink(file_path)
        except Exception as e: print(e)

# --- YARDIMCI FONKSİYONLAR ---
def is_user_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

def force_join_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📢 Kanala Katıl", url="https://t.me/tgfreehosting"))
    m.add(types.InlineKeyboardButton("✅ Katıldım", callback_data="check_join"))
    return m

def get_pid_file(b): return os.path.join(BASE_DIR, f"{b}.pid")
def get_log_file(b): return os.path.join(BASE_DIR, f"{b}.log")

def is_running(b):
    pid_file = get_pid_file(b)
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            try: return os.path.exists(f"/proc/{f.read().strip()}")
            except: return False
    return False

# --- PAKET ANALİZ VE YÜKLEME FONKSİYONLARI ---
# Özel paket eşleştirme (import adı -> pip paket adı)
PACKAGE_MAP = {
    'telegram': 'python-telegram-bot',  # Bu çok önemli!
    'discord': 'discord.py',
    'PIL': 'pillow',
    'cv2': 'opencv-python',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'requests': 'requests',
    'flask': 'flask',
    'django': 'django',
    'aiohttp': 'aiohttp',
    'websockets': 'websockets',
    'asyncpg': 'asyncpg',
    'psycopg2': 'psycopg2-binary',
    'mysql': 'mysql-connector-python',
    'pymongo': 'pymongo',
    'redis': 'redis',
    'celery': 'celery',
    'jwt': 'pyjwt',
    'cryptography': 'cryptography',
    'bcrypt': 'bcrypt',
    'passlib': 'passlib',
    'beautifulsoup4': 'beautifulsoup4',
    'bs4': 'beautifulsoup4',
    'selenium': 'selenium',
    'scrapy': 'scrapy',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'plotly': 'plotly',
    'tensorflow': 'tensorflow',
    'torch': 'torch',
    'keras': 'keras',
    'transformers': 'transformers',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'gunicorn': 'gunicorn',
    'python-dotenv': 'python-dotenv',
}

def analyze_python_imports(file_path):
    """Python dosyasındaki importları analiz et"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except:
            # AST ile parse edilemezse regex ile dene
            imports = set(re.findall(r'^(?:from|import)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE))
    except:
        pass
    
    return imports

def get_pip_package_name(import_name):
    """Import adını pip paket adına çevir"""
    # Özel eşleştirme varsa kullan
    if import_name in PACKAGE_MAP:
        return PACKAGE_MAP[import_name]
    # Yoksa aynı adı kullan
    return import_name

def install_python_package(package_name):
    """Tek bir Python paketini yükle"""
    # Önce pip paket adını al
    pip_package = get_pip_package_name(package_name)
    
    try:
        # Önce yüklü mü kontrol et (import_name ile dene)
        __import__(package_name)
        return True, f"✅ {package_name} zaten yüklü"
    except ImportError:
        try:
            print(f"📦 {pip_package} yükleniyor...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_package])
            return True, f"✅ {package_name} başarıyla yüklendi (pip: {pip_package})"
        except Exception as e:
            # Eğer pip paket adı farklıysa tekrar dene
            if pip_package != package_name:
                try:
                    print(f"📦 {package_name} yükleniyor (alternatif)...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                    return True, f"✅ {package_name} başarıyla yüklendi"
                except Exception as e2:
                    return False, f"❌ {package_name} yüklenemedi: {str(e2)}"
            return False, f"❌ {package_name} yüklenemedi: {str(e)}"

def install_required_packages(file_path):
    """Dosyadaki gerekli paketleri yükle"""
    if not file_path.endswith('.py'):
        return []
    
    packages = analyze_python_imports(file_path)
    results = []
    
    # Standart kütüphaneler
    std_libs = {
        'os', 'sys', 're', 'json', 'time', 'datetime', 'math', 'random', 
        'collections', 'itertools', 'functools', 'typing', 'io', 'pathlib',
        'subprocess', 'logging', 'shutil', 'ast', 'hashlib', 'base64',
        'urllib', 'http', 'socket', 'threading', 'multiprocessing', 'queue',
        'xml', 'html', 'csv', 'sqlite3', 'zipfile', 'tarfile', 'tempfile',
        'fileinput', 'glob', 'fnmatch', 'pickle', 'copy', 'pprint', 'string',
        'textwrap', 'contextlib', 'abc', 'dataclasses', 'enum', 'fractions',
        'decimal', 'statistics', 'calendar', 'uuid', 'secrets', 'getpass',
        'platform', 'signal', 'faulthandler', 'atexit', 'gc', 'inspect',
        'dis', 'traceback', 'linecache', 'codecs', 'encodings', 'pydoc',
        'doctest', 'unittest', 'argparse', 'optparse', 'getopt', 'configparser',
        'profile', 'pstats', 'cProfile', 'turtle', 'tkinter', 'ctypes',
        'struct', 'mmap', 'msvcrt', 'winreg', 'winsound', 'curses'
    }
    
    # Özel bot kütüphaneleri (her zaman yükle)
    always_install = {'telegram'}
    
    for package in packages:
        # Standart kütüphane değilse veya her zaman yüklenecekler listesindeyse
        if package not in std_libs or package in always_install:
            status, message = install_python_package(package)
            results.append((package, status, message))
    
    return results

# --- MENÜLER ---
def main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("📤 Dosya Yükle", callback_data="upload_doc"),
          types.InlineKeyboardButton("🤖 Botlarım", callback_data="my_bots"))
    return m

def control_menu(b):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("▶️ Başlat", callback_data=f"start_{b}"),
          types.InlineKeyboardButton("⏸️ Durdur", callback_data=f"stop_{b}"))
    m.add(types.InlineKeyboardButton("📜 Log", callback_data=f"log_{b}"),
          types.InlineKeyboardButton("🗑️ Sil", callback_data=f"del_{b}"))
    m.add(types.InlineKeyboardButton("🔙 Geri", callback_data="back"))
    return m

# --- KOMUTLAR ---
@bot.message_handler(commands=['start'])
def start(m):
    if not is_user_member(m.chat.id):
        bot.send_message(m.chat.id, "⚠️ LÜTFEN ZORUNLU KANALLARA KATILIN", reply_markup=force_join_menu())
        return
    bot.send_message(m.chat.id, "💎 **Premium Bot Yönetim Paneli**", parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join(call):
    if is_user_member(call.from_user.id):
        bot.edit_message_text("✅ Başarıyla katıldın!", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "💎 Ana Menü:", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ Henüz katılmamışsın!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "upload_doc")
def upload_ask(call):
    bot.edit_message_text("📝 Lütfen `.py`, `.html` veya `.js` dosyanızı gönderin.", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['document'])
def handle_doc(m):
    if not m.document.file_name.lower().endswith(('.py', '.html', '.js')):
        bot.reply_to(m, "❌ Sadece `.py`, `.html` veya `.js` dosyaları yükleyebilirsiniz!")
        return
    
    path = os.path.join(TEMP_DIR, f"{m.from_user.id}_{m.document.file_name}")
    file_info = bot.get_file(m.document.file_id)
    # Binary indirme (dosyanın bozulmaması için)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(path, 'wb') as new_file: 
        new_file.write(downloaded_file)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Onayla", callback_data=f"app_{m.from_user.id}_{m.document.file_name}"),
               types.InlineKeyboardButton("❌ Reddet", callback_data=f"deny_{m.from_user.id}_{m.document.file_name}"))
    bot.send_document(ADMIN_ID, m.document.file_id, caption=f"👤 Kullanıcı: `{m.from_user.id}`", parse_mode="Markdown", reply_markup=markup)
    bot.reply_to(m, "⏳ Dosyanız admin onayına gönderildi.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("app_", "deny_")))
def admin_actions(call):
    if call.from_user.id != ADMIN_ID: return
    action, uid, name = call.data.split("_", 2)
    if action == "app":
        temp_path = os.path.join(TEMP_DIR, f"{uid}_{name}")
        final_path = os.path.join(BASE_DIR, f"{uid}_{name}")
        os.rename(temp_path, final_path)
        
        # Dosya Python ise gerekli paketleri yükle
        if name.endswith('.py'):
            try:
                bot.send_message(int(uid), f"🔍 `{name}` dosyası analiz ediliyor ve gerekli paketler yükleniyor...", parse_mode="Markdown")
                results = install_required_packages(final_path)
                
                # Sonuçları hazırla
                success_msgs = []
                fail_msgs = []
                for package, status, message in results:
                    if status:
                        success_msgs.append(message)
                    else:
                        fail_msgs.append(message)
                
                # Kullanıcıya bildir
                result_text = f"🎉 `{name}` dosyanız onaylandı!\n\n"
                if success_msgs:
                    result_text += "✅ Yüklenen paketler:\n" + "\n".join(success_msgs) + "\n\n"
                if fail_msgs:
                    result_text += "⚠️ Yüklenemeyen paketler:\n" + "\n".join(fail_msgs)
                if not results:
                    result_text += "📦 Ek paket gerekmiyor."
                
                bot.send_message(int(uid), result_text, parse_mode="Markdown")
                
            except Exception as e:
                bot.send_message(int(uid), f"⚠️ Paket yükleme sırasında hata: {str(e)}", parse_mode="Markdown")
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        msg = bot.send_message(call.message.chat.id, "✍️ Lütfen ret sebebini yazın (bu mesaja cevap verin):")
        bot.register_for_reply(msg, lambda m: send_rejection(m, uid, name, call.message.message_id))

def send_rejection(m, uid, name, admin_msg_id):
    bot.send_message(int(uid), f"❌ `{name}` dosyanız reddedildi.\nSebep: {m.text}", parse_mode="Markdown")
    if os.path.exists(os.path.join(TEMP_DIR, f"{uid}_{name}")): os.remove(os.path.join(TEMP_DIR, f"{uid}_{name}"))
    bot.delete_message(m.chat.id, admin_msg_id)
    bot.reply_to(m, "✅ Red mesajı iletildi.")

@bot.callback_query_handler(func=lambda call: call.data == "my_bots")
def list_bots(call):
    files = [f for f in os.listdir(BASE_DIR) if f.startswith(f"{call.from_user.id}_") and not (f.endswith(".pid") or f.endswith(".log"))]
    if not files: return bot.answer_callback_query(call.id, "❌ Hiç botunuz yok.")
    m = types.InlineKeyboardMarkup()
    for f in files: m.add(types.InlineKeyboardButton(f"🤖 {f.replace(f'{call.from_user.id}_', '')}", callback_data=f"man_{f}"))
    m.add(types.InlineKeyboardButton("🔙 Geri", callback_data="back"))
    bot.edit_message_text("🛠 **Botlarım:**", call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("man_"))
def manage(call):
    b = call.data.split("_", 1)[1]
    status = "🟢 Çalışıyor" if is_running(b) else "🔴 Durduruldu"
    bot.edit_message_text(f"⚙️ **Bot:** `{b.replace(f'{call.from_user.id}_', '')}`\n📊 **Durum:** {status}", call.message.chat.id, call.message.message_id, reply_markup=control_menu(b), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("start_", "stop_", "del_", "log_")))
def action(call):
    act, b = call.data.split("_", 1)
    if act == "start" and not is_running(b):
        run_cmd = "python" if b.endswith(".py") else "node" if b.endswith(".js") else "echo"
        cmd = f"nohup {run_cmd} {os.path.join(BASE_DIR, b)} > {get_log_file(b)} 2>&1 & echo $! > {get_pid_file(b)}"
        subprocess.Popen(cmd, shell=True)
        bot.answer_callback_query(call.id, "✅ Başlatıldı.")
    elif act == "stop" and is_running(b):
        with open(get_pid_file(b), 'r') as f: os.kill(int(f.read()), 9)
        os.remove(get_pid_file(b))
        bot.answer_callback_query(call.id, "⏸️ Durduruldu.")
    elif act == "del":
        if is_running(b): os.kill(int(open(get_pid_file(b)).read()), 9)
        if os.path.exists(get_pid_file(b)): os.remove(get_pid_file(b))
        if os.path.exists(get_log_file(b)): os.remove(get_log_file(b))
        os.remove(os.path.join(BASE_DIR, b))
        return list_bots(call)
    elif act == "log":
        log = open(get_log_file(b)).read()[-1000:] if os.path.exists(get_log_file(b)) else "Log yok."
        bot.send_message(call.message.chat.id, f"📋 **Log Kayıtları:**\n```\n{log}\n```", parse_mode="Markdown")
        return
    manage(call)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back(call):
    bot.edit_message_text("💎 **Premium Yönetim Paneli**", call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")

bot.infinity_polling()
