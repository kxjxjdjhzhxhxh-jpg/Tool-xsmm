import os
import sys
import json
import uuid
import time
import threading
import subprocess
import tempfile
import random
import string
import re
from datetime import datetime
from queue import Queue
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import requests
from curl_cffi import requests as c_requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ta_tool_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)
TEMP_TOOLS_DIR = os.path.join(tempfile.gettempdir(), "ta_tool_embedded")
os.makedirs(TEMP_TOOLS_DIR, exist_ok=True)

sessions = {}
sessions_lock = threading.Lock()

FB_REG_STATE = {"running": False, "total_success": 0, "total_fail": 0}
FB_REG_LOCK = threading.Lock()

# ============================================================================
# ==================== TOOL 2: xsmmigv5.2.py (CHỈ COOKIE) ===================
# ============================================================================
TOOL_CODE_XSMMIGV52 = r'''import os, sys, time, json, re, random
from datetime import datetime
from urllib.parse import unquote
from curl_cffi import requests as c_requests
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

red = "\033[1;31m"; green = "\033[1;32m"; yellow = "\033[1;33m"
cyan = "\033[1;36m"; reset = "\033[0m"
print_lock = threading.Lock()
def thread_safe_print(msg):
    with print_lock: print(msg)

class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    def get_accounts(self, search=None):
        try: return requests.get(f"{self.base_url}/accounts2", headers=self.headers, params={"account_type": "instagram", "search": search}, timeout=20).json()
        except: return {}
    def add_account(self, link):
        try: return requests.post(f"{self.base_url}/accounts2", headers=self.headers, json={"type": "instagram", "link_account": link}, timeout=20).json()
        except: return {}
    def get_tasks(self, type_job, uid):
        try: return requests.get(f"{self.base_url}/tasks2", headers=self.headers, params={"type": type_job, "uid": uid, "typejob": "normal,better,best"}, timeout=20).json()
        except: return []
    def complete_tasks(self, type_job, task_ids, uid, cookie_check=""):
        try: return requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json={"type": type_job, "task_id": task_ids, "uid": uid, "cookie_check": cookie_check}, timeout=35).json()
        except: return {}

def get_headers(cookie, csrf):
    return {'accept': '*/*', 'cookie': cookie, 'x-csrftoken': csrf, 'x-ig-app-id': '936619743392459', 'user-agent': 'Mozilla/5.0'}

def follow(tid, c, csrf, url, proxy):
    if not tid: return '{"status":"error"}'
    session = c_requests.Session(impersonate="chrome120")
    if proxy: session.proxies = {"http": proxy, "https": proxy}
    for item in c.split(';'):
        if '=' in item:
            k,v = item.strip().split('=',1); session.cookies.set(k,v,domain='.instagram.com')
    session.headers.update(get_headers(c, csrf))
    data = {"av": "0", "__d": "www", "fb_dtsg": "", "lsd": "Jfq8", "doc_id": "26508036048874888", "variables": json.dumps({"target_user_id": tid, "container_module": "profile"})}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, timeout=15).text
    except: return '{"status":"error"}'

def tym(mid, c, csrf, url, proxy):
    if not mid: return '{"status":"error"}'
    session = c_requests.Session(impersonate="chrome120")
    if proxy: session.proxies = {"http": proxy, "https": proxy}
    for item in c.split(';'):
        if '=' in item:
            k,v = item.strip().split('=',1); session.cookies.set(k,v,domain='.instagram.com')
    session.headers.update(get_headers(c, csrf))
    data = {"av": "0", "__d": "www", "fb_dtsg": "", "lsd": "GyeZl", "doc_id": "27182485238052618", "variables": json.dumps({"input": {"media_id": mid}})}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, timeout=15).text
    except: return '{"status":"error"}'

def cmt(mid, nd, c, csrf, url, proxy):
    if not mid: return '{"status":"error"}'
    session = c_requests.Session(impersonate="chrome120")
    if proxy: session.proxies = {"http": proxy, "https": proxy}
    for item in c.split(';'):
        if '=' in item:
            k,v = item.strip().split('=',1); session.cookies.set(k,v,domain='.instagram.com')
    session.headers.update(get_headers(c, csrf))
    data = {"av": "0", "__d": "www", "fb_dtsg": "", "lsd": "9zei3", "doc_id": "27261905640092552", "variables": json.dumps({"data": {"comment_text": nd, "media_id": mid}})}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, timeout=15).text
    except: return '{"status":"error"}'

def run_account(acc, listnv, config_delays, xsmm_token, dl, doi):
    c = acc.get("cookie", "")
    proxy = acc.get("proxy", "")
    xsmm = XSMMTool(token=xsmm_token)
    
    try:
        r = c_requests.get('https://www.instagram.com/api/v1/accounts/edit/web_form_data/', headers=get_headers(c,""), proxies={"http":proxy,"https":proxy} if proxy else None, impersonate="chrome120", timeout=20).text
        cfg = json.loads(r)
        if not (cfg and 'form_data' in cfg and cfg['form_data'].get('username')): return
        tenfb = cfg['form_data']['username']
        m = re.search(r'ds_user_id=(\d+)', c); idfb = m.group(1) if m else "0"
    except: return
    
    thread_safe_print(f"{green}[+] NICK [{tenfb}]{reset}")
    try:
        al = xsmm.get_accounts(search=idfb)
        if not (isinstance(al, dict) and al.get("accounts")): xsmm.add_account(f"https://www.instagram.com/{tenfb}")
    except: pass

    max_job = 0; cache = []
    while True:
        job = random.choice(listnv)
        if job == 'instagram_like':
            lv = xsmm.get_tasks(job, idfb)
            if isinstance(lv, list) and lv:
                for nv in lv:
                    csf_m = re.search(r'csrftoken=([^;]+)', c); csf = csf_m.group(1) if csf_m else ""
                    chay = tym(nv.get('target_id',''), c, csf, nv.get('target_url',''), proxy)
                    max_job += 1
                    if 'data' in chay or 'ok' in chay:
                        ck = xsmm.complete_tasks(job, [nv.get('id')], idfb, c)
                        pts = ck.get('points', 0)
                        thread_safe_print(f"{green}[+] TYM OK (+{pts} xu){reset}")
                        if pts > 0: thread_safe_print(f"[[XU_UPDATE]]|{tenfb}|{pts}|1")
                    time.sleep(config_delays['tym'])
                    if max_job >= doi: break
        elif job == 'instagram_follow':
            lv = xsmm.get_tasks(job, idfb)
            if isinstance(lv, list) and lv:
                for nv in lv:
                    csf_m = re.search(r'csrftoken=([^;]+)', c); csf = csf_m.group(1) if csf_m else ""
                    chay = follow(nv.get('target_id',''), c, csf, nv.get('target_url',''), proxy)
                    max_job += 1
                    if 'data' in chay or 'ok' in chay:
                        cache.append(nv.get('id'))
                        thread_safe_print(f"{green}[+] Follow OK ({len(cache)}/8){reset}")
                        if len(cache) >= 8:
                            ck = xsmm.complete_tasks(job, cache, idfb, c)
                            pts = ck.get('points', 0)
                            thread_safe_print(f"{green}[+] XSMM: OK (+{pts} xu){reset}")
                            if pts > 0: thread_safe_print(f"[[XU_UPDATE]]|{tenfb}|{pts}|8")
                            cache = []
                    time.sleep(config_delays['follow'])
                    if max_job >= doi: break
        elif job == 'instagram_comment':
            lv = xsmm.get_tasks(job, idfb)
            if isinstance(lv, list) and lv:
                for nv in lv:
                    csf_m = re.search(r'csrftoken=([^;]+)', c); csf = csf_m.group(1) if csf_m else ""
                    chay = cmt(nv.get('target_id',''), nv.get('comment','❤️'), c, csf, nv.get('target_url',''), proxy)
                    max_job += 1
                    if 'data' in chay or 'ok' in chay:
                        ck = xsmm.complete_tasks(job, [nv.get('id')], idfb, c)
                        pts = ck.get('points', 0)
                        thread_safe_print(f"{green}[+] CMT OK (+{pts} xu){reset}")
                        if pts > 0: thread_safe_print(f"[[XU_UPDATE]]|{tenfb}|{pts}|1")
                    time.sleep(config_delays['comment'])
                    if max_job >= doi: break
        if max_job >= doi: max_job = 0

def main():
    sys.stdout.write("Số luồng: "); sys.stdout.flush()
    try: threads = int(input().strip())
    except: threads = 10
    sys.stdout.write("Token XSMM: "); sys.stdout.flush()
    token = input().strip()
    sys.stdout.write("Số nick: "); sys.stdout.flush()
    try: sl = int(input().strip())
    except: sl = 1
    mang = []
    for i in range(sl):
        print(f"Nhập Cookie ({i+1}): "); sys.stdout.flush()
        c = input().strip()
        if c: mang.append({"cookie": c, "proxy": ""})
    
    listnv = []
    for job in ['instagram_like', 'instagram_follow', 'instagram_comment']:
        sys.stdout.write(f"{job} (on/off): "); sys.stdout.flush()
        if input().strip().lower() == 'on': listnv.append(job)
    if not listnv: sys.exit()
    
    with ThreadPoolExecutor(max_workers=threads) as ex:
        for ad in mang: ex.submit(run_account, ad, listnv, {'tym':10,'follow':15,'comment':20}, token, 150, 99999)

if __name__ == "__main__": main()
'''

TOOL_INFO = {"xsmmigv5.2": {"name": "XSMM IG V5.2", "color": "#ff6b9d"}}

# ============================================================================
# ==================== FB REG PAGE NÂNG CAO =================================
# ============================================================================
def fb_get_dtsg(cookie, proxies):
    try:
        r = requests.get('https://www.facebook.com/settings', headers={'cookie': cookie, 'user-agent': 'Mozilla/5.0'}, proxies=proxies, timeout=15)
        dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', r.text)
        jz = re.search(r'name="jazoest" value="(.*?)"', r.text)
        if dtsg and jz: return dtsg.group(1), jz.group(1)
    except: pass
    return None, None

def fb_upload_photo(cookie, page_id, img_url, img_type, proxies):
    try: img_data = requests.get(img_url, timeout=15).content
    except: return False
    boundary = '----WebKitFormBoundary' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    headers = {'cookie': cookie, 'user-agent': 'Mozilla/5.0', 'content-type': f'multipart/form-data; boundary={boundary}'}
    url = f"https://www.facebook.com/api/v1/pages/{page_id}/{'picture' if img_type=='avatar' else 'cover'}/"
    field_name = "profile_pic" if img_type=='avatar' else "cover_photo"
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="{field_name}"; filename="img.jpg"\r\nContent-Type: image/jpeg\r\n\r\n').encode() + img_data + f'\r\n--{boundary}--\r\n'.encode()
    try:
        r = requests.post(url, headers=headers, data=body, proxies=proxies, timeout=30)
        return r.status_code == 200
    except: return False

def fb_invite_admin(cookie, page_id, target_uid, password, proxies):
    fb_dtsg, jazoest = fb_get_dtsg(cookie, proxies)
    if not fb_dtsg: return False
    actor_m = re.search(r'c_user=(\d+)', cookie); actor_id = actor_m.group(1) if actor_m else ""
    
    headers = {'cookie': cookie, 'user-agent': 'Mozilla/5.0', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com'}
    payload = {
        'fb_dtsg': fb_dtsg, 'jazoest': jazoest,
        'variables': json.dumps({"input": {"actor_id": actor_id, "profile_id": page_id, "target_user_id": target_uid, "task_ids": [1, 2, 3, 4, 5], "password": password}}),
        'doc_id': '5278783472212933'
    }
    try:
        r = requests.post("https://www.facebook.com/api/graphql/", headers=headers, data=payload, proxies=proxies, timeout=20)
        return 'errors' not in r.json()
    except: return False

def fb_reg_worker(idx, cookie, page_name, cat, proxy, avt, cover, target_uid, pwd, result_list):
    res = {"idx": idx, "uid": "", "page_id": "", "page_name": page_name, "status": "Đang xử lý...", "ok": False}
    try:
        m = re.search(r'c_user=(\d+)', cookie); res["uid"] = m.group(1) if m else ""
        proxies = {"http": proxy, "https": proxy} if proxy else None
        fb_dtsg, jazoest = fb_get_dtsg(cookie, proxies)
        if not fb_dtsg: res["status"] = "Cookie die"; result_list.append(res); return
        
        headers = {'cookie': cookie, 'user-agent': 'Mozilla/5.0', 'content-type': 'application/x-www-form-urlencoded'}
        payload = {'fb_dtsg': fb_dtsg, 'jazoest': jazoest, 'variables': json.dumps({"input": {"actor_id": res["uid"], "name": page_name, "category_id": cat, "creation_source": "comet"}}), 'doc_id': '5814795813638014'}
        r = requests.post("https://www.facebook.com/api/graphql/", headers=headers, data=payload, proxies=proxies, timeout=25)
        pid_match = re.search(r'"page_id":"(\d+)"', json.dumps(r.json().get('data', {})))
        if not pid_match: res["status"] = "Lỗi tạo Page"; result_list.append(res); return
        
        res["page_id"] = pid_match.group(1)
        if avt: fb_upload_photo(cookie, res["page_id"], avt, 'avatar', proxies)
        if cover: fb_upload_photo(cookie, res["page_id"], cover, 'cover', proxies)
        if target_uid and pwd: fb_invite_admin(cookie, res["page_id"], target_uid, pwd, proxies)
        
        res["status"] = "OK + QTV"; res["ok"] = True
        result_list.append(res)
    except Exception as e:
        res["status"] = "Lỗi"; result_list.append(res)

def run_fb_reg(tasks, threads):
    FB_REG_STATE["running"] = True; FB_REG_STATE["total_success"] = 0; FB_REG_STATE["total_fail"] = 0
    q = Queue(); [q.put((i+1, t['cookie'], t['page_name'], '2200', t.get('proxy',''), t.get('avatar',''), t.get('cover',''), t.get('target_uid',''), t.get('pwd',''))) for i, t in enumerate(tasks)]
    def worker():
        while True:
            try: task = q.get_nowait()
            except: break
            try:
                rl = []
                fb_reg_worker(*task, rl)
                if rl:
                    res = rl[0]
                    with FB_REG_LOCK:
                        if res["ok"]: FB_REG_STATE["total_success"] += 1
                        else: FB_REG_STATE["total_fail"] += 1
                        socketio.emit('fb_reg_update', {"result": res, "stats": {"success": FB_REG_STATE["total_success"], "fail": FB_REG_STATE["total_fail"]}})
            except: pass
            finally: q.task_done()
    ts = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    for t in ts: t.start()
    for t in ts: t.join()
    FB_REG_STATE["running"] = False
    socketio.emit('fb_reg_done', {"success": FB_REG_STATE["total_success"], "fail": FB_REG_STATE["total_fail"]})

@app.route('/api/fb_reg_start', methods=['POST'])
def api_fb_reg_start():
    data = request.json or {}
    if not data.get('tasks'): return jsonify({"ok": False})
    threading.Thread(target=run_fb_reg, args=(data['tasks'], int(data.get('threads', 10))), daemon=True).start()
    return jsonify({"ok": True})

# ============================================================================
# ==================== ROUTES CƠ BẢN =========================================
# ============================================================================
def ensure_tool_file(k):
    f = os.path.join(TEMP_TOOLS_DIR, "xsmmigv5.2.py")
    with open(f, "w", encoding="utf-8") as fw: fw.write(TOOL_CODE_XSMMIGV52)
    return f

def read_process_output(sid, process):
    try:
        for line in iter(process.stdout.readline, ''):
            if line == '' and process.poll() is not None: break
            if line: socketio.emit('output', {'session_id': sid, 'line': line.rstrip(), 'ts': datetime.now().strftime('%H:%M:%S')}, room=sid)
    except: pass
    finally:
        process.wait()
        socketio.emit('status', {'session_id': sid, 'status': 'stopped'}, room=sid)

@app.route('/')
def index(): return render_template('index.html', tools=TOOL_INFO)

@app.route('/api/start/<k>', methods=['POST'])
def api_start(k):
    sid = str(uuid.uuid4())[:8]; f = ensure_tool_file(k)
    p = subprocess.Popen([sys.executable, '-u', f], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=TEMP_TOOLS_DIR, bufsize=1, universal_newlines=True, encoding='utf-8')
    with sessions_lock: sessions[sid] = {"tool": k, "process": p}
    threading.Thread(target=read_process_output, args=(sid, p), daemon=True).start()
    return jsonify({"ok": True, "session_id": sid})

@app.route('/api/stop/<sid>', methods=['POST'])
def api_stop(sid):
    s = sessions.get(sid)
    if s:
        try:
            p = s["process"]
            p.terminate()
            try: p.wait(timeout=2)
            except subprocess.TimeoutExpired: p.kill()
            socketio.emit('status', {'session_id': sid, 'status': 'stopped'}, room=sid)
            return jsonify({"ok": True})
        except: return jsonify({"ok": False}), 500
    return jsonify({"ok": False}), 404

@app.route('/api/input/<sid>', methods=['POST'])
def api_input(sid):
    s = sessions.get(sid)
    if s:
        try: s["process"].stdin.write((request.json or {}).get("text", "") + "\n"); s["process"].stdin.flush()
        except: pass
    return jsonify({"ok": True})

@socketio.on('join')
def on_join(data): join_room(data.get('session_id'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), allow_unsafe_werkzeug=True)
