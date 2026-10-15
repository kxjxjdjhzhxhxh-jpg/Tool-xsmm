import os
import sys
import json
import uuid
import time
import threading
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ta_tool_secret_2024'

# ⚠️ Đã đổi từ eventlet -> threading để tương thích Python 3.13 trên Railway
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(TOOLS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

# ================== QUẢN LÝ SESSIONS ==================
sessions = {}
sessions_lock = threading.Lock()

TOOL_FILES = {
    "xsmmv3.2": os.path.join(TOOLS_DIR, "xsmmv3.2.py"),
    "xsmmigv5.2": os.path.join(TOOLS_DIR, "xsmmigv5.2.py"),
    "11223": os.path.join(TOOLS_DIR, "11223.py"),
}

TOOL_INFO = {
    "xsmmv3.2": {
        "name": "XSMM Tool V3.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API (Multi-thread ThreadPoolExecutor 10 luồng)",
        "color": "#00d4ff"
    },
    "xsmmigv5.2": {
        "name": "XSMM IG V5.2",
        "desc": "Tool Instagram Auto Jobs - XSMM API V2 (25 Browser Profiles + Full Telemetry + JSON Queue)",
        "color": "#ff6b9d"
    },
    "11223": {
        "name": "Simple IG Bot",
        "desc": "Tool đơn giản - Like / Follow / Comment với XSMM (chạy tuần tự)",
        "color": "#ffd93d"
    },
}


def read_process_output(session_id, process):
    """Đọc output từ subprocess theo thời gian thực và push qua socketio"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line == '' and process.poll() is not None:
                break
            if line:
                line = line.rstrip('\n').rstrip('\r')
                with sessions_lock:
                    if session_id in sessions:
                        sessions[session_id]["output_lines"].append(line)
                        if len(sessions[session_id]["output_lines"]) > 5000:
                            sessions[session_id]["output_lines"] = sessions[session_id]["output_lines"][-5000:]
                socketio.emit('output', {
                    'session_id': session_id,
                    'line': line,
                    'ts': datetime.now().strftime('%H:%M:%S')
                }, room=session_id)
    except Exception:
        pass
    finally:
        try:
            process.wait()
            rc = process.returncode
        except Exception:
            rc = -1
        with sessions_lock:
            if session_id in sessions:
                sessions[session_id]["status"] = "stopped" if rc == 0 else f"exited({rc})"
        socketio.emit('status', {
            'session_id': session_id,
            'status': 'stopped',
            'return_code': rc,
            'message': f'Tool đã kết thúc (code {rc})'
        }, room=session_id)


def start_tool_process(session_id, tool_key):
    tool_path = TOOL_FILES.get(tool_key)
    if not tool_path or not os.path.exists(tool_path):
        return None, f"Không tìm thấy file tool: {tool_path}"

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'
    env['TERM'] = 'xterm-256color'
    env['LC_ALL'] = 'C.UTF-8'
    env['LANG'] = 'C.UTF-8'

    process = subprocess.Popen(
        [sys.executable, '-u', tool_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=TOOLS_DIR,
        env=env,
        bufsize=1,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace',
    )
    return process, None


# ================== ROUTES ==================
@app.route('/')
def index():
    return render_template('index.html', tools=TOOL_INFO)


@app.route('/health')
def health():
    return jsonify({"ok": True, "time": datetime.now().isoformat()})


@app.route('/api/tools')
def api_tools():
    return jsonify(TOOL_INFO)


@app.route('/api/sessions')
def api_sessions():
    with sessions_lock:
        result = []
        for sid, s in sessions.items():
            result.append({
                "session_id": sid,
                "tool": s["tool"],
                "status": s["status"],
                "started_at": s["started_at"],
                "output_count": len(s["output_lines"]),
            })
        return jsonify(result)


@app.route('/api/start/<tool_key>', methods=['POST'])
def api_start(tool_key):
    if tool_key not in TOOL_FILES:
        return jsonify({"ok": False, "error": "Tool không hợp lệ"}), 400

    if not os.path.exists(TOOL_FILES[tool_key]):
        return jsonify({"ok": False, "error": f"Không tìm thấy file: {TOOL_FILES[tool_key]}"}), 404

    session_id = str(uuid.uuid4())[:8]
    process, err = start_tool_process(session_id, tool_key)
    if err:
        return jsonify({"ok": False, "error": err}), 500

    with sessions_lock:
        sessions[session_id] = {
            "tool": tool_key,
            "process": process,
            "output_lines": [],
            "status": "running",
            "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    t = threading.Thread(target=read_process_output, args=(session_id, process), daemon=True)
    t.start()

    return jsonify({"ok": True, "session_id": session_id})


@app.route('/api/stop/<session_id>', methods=['POST'])
def api_stop(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return jsonify({"ok": False, "error": "Session không tồn tại"}), 404

    try:
        proc = s["process"]
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        with sessions_lock:
            sessions[session_id]["status"] = "stopped"
        socketio.emit('status', {
            'session_id': session_id,
            'status': 'stopped',
            'message': 'Đã dừng theo yêu cầu'
        }, room=session_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/input/<session_id>', methods=['POST'])
def api_input(session_id):
    data = request.get_json() or {}
    text = data.get("text", "")
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return jsonify({"ok": False, "error": "Session không tồn tại"}), 404

    try:
        proc = s["process"]
        if proc.poll() is not None:
            return jsonify({"ok": False, "error": "Process đã kết thúc"}), 400
        proc.stdin.write(text + "\n")
        proc.stdin.flush()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/output/<session_id>')
def api_output(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return jsonify({"ok": False, "error": "Session không tồn tại"}), 404
    return jsonify({
        "ok": True,
        "tool": s["tool"],
        "status": s["status"],
        "started_at": s["started_at"],
        "lines": s["output_lines"]
    })


@app.route('/api/clear/<session_id>', methods=['POST'])
def api_clear(session_id):
    with sessions_lock:
        if session_id in sessions:
            sessions[session_id]["output_lines"] = []
    socketio.emit('cleared', {'session_id': session_id}, room=session_id)
    return jsonify({"ok": True})


@app.route('/api/save/<session_id>', methods=['POST'])
def api_save(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return jsonify({"ok": False, "error": "Session không tồn tại"}), 404

    filename = f"{s['tool']}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    filepath = os.path.join(SESSIONS_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Tool: {s['tool']}\n")
            f.write(f"# Started: {s['started_at']}\n")
            f.write(f"# Session: {session_id}\n")
            f.write("=" * 60 + "\n")
            f.write("\n".join(s["output_lines"]))
        return jsonify({"ok": True, "filename": filename})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ================== SOCKETIO ==================
@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined', {'session_id': session_id})


# ================== RUN ==================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print(" 🚀 TA TOOL WEB MANAGER")
    print(f" 📁 Tools dir: {TOOLS_DIR}")
    print(f" 🌐 Port: {port}")
    print("=" * 60)
    # allow_unsafe_werkzeug=True để chạy socketio với async_mode='threading'
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )
