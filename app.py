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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ta_tool_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

TEMP_TOOLS_DIR = os.path.join(tempfile.gettempdir(), "ta_tool_embedded")
os.makedirs(TEMP_TOOLS_DIR, exist_ok=True)

# ================== BIẾN DÙNG CHUNG ==================
sessions = {}
sessions_lock = threading.Lock()

FB_REG_STATE = {
    "running": False,
    "results": [],
    "threads": 0,
    "running_threads": 0,
    "start_time": 0,
    "total_success": 0,
    "total_fail": 0,
}
FB_REG_LOCK = threading.Lock()

# ============================================================================
# ==================== TOOL 1: xsmmv3.2.py (WARMUP) =========================
# ============================================================================
TOOL_CODE_XSMMV32 = r'''import os
import sys
import time
import json
import re
from datetime import datetime
import random
from urllib.parse import unquote
from curl_cffi import requests as c_requests
import requests
import threading
from concurrent.futures import ThreadPoolExecutor

red = "\033[1;31m"; pink = "\033[1;35m"; green = "\033[1;32m"
yellow = "\033[1;33m"; white = "\033[0;37m"; cyan = "\033[1;36m"
blue = "\033[1;34m"; cam = "\033[38;5;208m"; reset = "\033[0m"

print_lock = threading.Lock()
def thread_safe_print(msg):
    with print_lock: print(msg)

class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    def get_user_info(self):
        try: return requests.get(f"{self.base_url}/user", headers=self.headers, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def get_accounts(self, account_type=None, search=None):
        params = {}
        if account_type: params['account_type'] = account_type
        if search: params['search'] = search
        try: return requests.get(f"{self.base_url}/accounts2", headers=self.headers, params=params, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def add_account(self, account_type, link_account):
        try: return requests.post(f"{self.base_url}/accounts2", headers=self.headers, json={"type": account_type, "link_account": link_account}, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        try: return requests.get(f"{self.base_url}/tasks2", headers=self.headers, params={"type": job_type, "uid": str(uid), "typejob": typejob}, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        payload = {"type": job_type, "task_id": task_ids if isinstance(task_ids, list) else [task_ids], "uid": str(uid), "cookie_check": cookie_check}
        attempt = 0
        while attempt < max_retries:
            try:
                r = requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json=payload, timeout=35)
                rd = r.json()
                if isinstance(rd, dict) and rd.get("retry") is True:
                    time.sleep(random.randint(1, 3)); attempt += 1; continue
                return rd
            except requests.exceptions.Timeout:
                return {"is_timeout": True, "message": "Server chậm"}
            except Exception as e: return {"error": str(e)}
        return {"error": "Retry failed"}

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
sec_ch_ua_120 = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'

def format_proxy(p):
    if not p: return None
    p = p.strip()
    if not p: return None
    scheme = "http"
    if "://" in p: scheme, p = p.split("://", 1)
    parts = p.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        f = f"{scheme}://{user}:{pwd}@{ip}:{port}"
    else: f = f"{scheme}://{p}"
    return {"http": f, "https": f}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/"):
    return {'accept': '*/*', 'accept-language': 'vi-VN,vi;q=0.9',
            'content-type': 'application/x-www-form-urlencoded', 'cookie': cookie,
            'origin': 'https://www.instagram.com', 'priority': 'u=1, i', 'referer': referer,
            'sec-ch-ua': sec_ch_ua_120, 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
            'user-agent': useragent, 'x-asbd-id': '129477', 'x-csrftoken': csrftoken,
            'x-ig-app-id': '936619743392459', 'x-ig-www-claim': '0', 'x-requested-with': 'XMLHttpRequest'}

def check_cookie_ig(cookie, proxy=None):
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    headers = {'x-ig-app-id': '936619743392459', 'x-requested-with': 'XMLHttpRequest',
               'referer': 'https://www.instagram.com/accounts/edit/', 'cookie': cookie,
               'user-agent': useragent, 'sec-ch-ua': sec_ch_ua_120}
    try: return c_requests.get(url, headers=headers, proxies=format_proxy(proxy), impersonate="chrome120", timeout=30).text
    except: return "{}"

def ig_warmup(session, cookie, proxy, tenfb):
    thread_safe_print(f"{cyan}[*] [{tenfb}] Warmup...{reset}")
    try:
        session.get("https://www.instagram.com/", impersonate="chrome120", timeout=15)
        time.sleep(random.uniform(3, 6))
        targets = ["instagram", "cristiano", "natgeo", "therock", "leomessi"]
        for t in random.sample(targets, random.randint(1, 2)):
            try:
                r = session.get(f"https://www.instagram.com/{t}/", impersonate="chrome120", timeout=10)
                m_id = re.search(r'"profile_id":"(\d+)"', r.text) or re.search(r'profilePage_(\d+)', r.text)
                if not m_id: continue
                tid = m_id.group(1)
                actor_m = re.search(r'ds_user_id=(\d+)', cookie)
                actor = actor_m.group(1) if actor_m else "0"
                h = get_ig_headers(cookie, "", f"https://www.instagram.com/{t}/")
                data = {
                    "av": actor, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
                    "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
                    "__rev": "1046917461", "__comet_req": "7", "lsd": "Jfq8VQNmkkkJufHSbEE9bf",
                    "fb_api_caller_class": "RelayModern",
                    "fb_api_req_friendly_name": "usePolarisFollowMutation",
                    "server_timestamps": "true", "doc_id": "26508036048874888",
                    "variables": json.dumps({"target_user_id": tid, "container_module": "profile",
                        "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link,PolarisProfileRoot:profilePage:6:unexpected"})
                }
                session.post("https://www.instagram.com/api/graphql", data=data, impersonate="chrome120", timeout=15)
                thread_safe_print(f"{green}[+] [{tenfb}] Follow @{t}{reset}")
                time.sleep(random.uniform(4, 8))
            except: pass
        session.get("https://www.instagram.com/explore/", impersonate="chrome120", timeout=15)
        time.sleep(random.uniform(5, 10))
        thread_safe_print(f"{green}[+] [{tenfb}] Warmup done{reset}")
        return True
    except Exception as e:
        thread_safe_print(f"{yellow}[!] [{tenfb}] Warmup fail: {e}{reset}")
        return False

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None):
    if not target_id: return '{"status": "error"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "Jfq8VQNmkkkJufHSbEE9bf", "26328"
    try:
        r = session.get(profile_url or "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', r)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', r) or re.search(r'name="fb_dtsg" value="([^"]+)"', r)
        if m: fb_dtsg = m.group(1)
    except: pass
    dyn = session.cookies.get('csrftoken')
    if not dyn:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn, profile_url or "https://www.instagram.com/"))
    actor_m = re.search(r'ds_user_id=(\d+)', cookie)
    actor = actor_m.group(1) if actor_m else "0"
    variables = {"target_user_id": str(target_id), "container_module": "profile",
                 "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link,PolarisProfileRoot:profilePage:6:unexpected"}
    data = {"av": actor, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "usePolarisFollowMutation",
            "server_timestamps": "true", "doc_id": "26508036048874888", "variables": json.dumps(variables)}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "GyeZl-huflHZ0K5L3-pzBi", "26492"
    try:
        r = session.get("https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', r)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', r) or re.search(r'name="fb_dtsg" value="([^"]+)"', r)
        if m: fb_dtsg = m.group(1)
    except: pass
    dyn = session.cookies.get('csrftoken')
    if not dyn:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn, link_job or "https://www.instagram.com/"))
    actor_m = re.search(r'ds_user_id=(\d+)', cookie)
    actor = actor_m.group(1) if actor_m else "0"
    tt = ""
    try:
        if link_job:
            rg = session.get(link_job, impersonate="chrome120", timeout=10).text
            m = re.search(r'"tracking_token":"([^"]+)"', rg)
            if m: tt = m.group(1)
    except: pass
    variables = {"input": {"actor_id": actor, "client_mutation_id": str(random.randint(1000000, 9999999)),
                           "container_module": "single_post", "media_id": str(mediaid)}}
    if tt: variables["input"]["tracking_token"] = tt
    data = {"av": actor, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
            "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None):
    if not mediaid: return '{"status": "error"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except: pass
    fb_dtsg, lsd, jazoest = "", "9zei3OjvTBQ-9YG6E0OMzm", "26312"
    try:
        r = session.get(link_job or "https://www.instagram.com/", impersonate="chrome120", timeout=10).text
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', r)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', r) or re.search(r'name="fb_dtsg" value="([^"]+)"', r)
        if m: fb_dtsg = m.group(1)
    except: pass
    dyn = session.cookies.get('csrftoken')
    if not dyn:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn, link_job or "https://www.instagram.com/"))
    actor_m = re.search(r'ds_user_id=(\d+)', cookie)
    actor = actor_m.group(1) if actor_m else "0"
    variables = {"connections": [f'client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:"{mediaid}",sort_order:"popular")'],
                 "data": {"comment_text": text, "media_id": str(mediaid)}}
    data = {"av": actor, "__d": "www", "__user": "0", "__a": "1", "__req": "10",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
            "server_timestamps": "true", "doc_id": "27261905640092552", "variables": json.dumps(variables)}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate="chrome120", timeout=15).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm, tenfb):
    if not task_list: return
    thread_safe_print(f"[{tenfb}] Gom {len(task_list)} task -> Gửi duyệt...")
    ck = xsmm.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        if 'message' in ck:
            thread_safe_print(f"[{now}] [{tenfb}] {ck['message']} (+{ck.get('points', 0)} xu)")
        elif ck.get("is_timeout"):
            thread_safe_print(f"[{now}] [{tenfb}] {ck['message']}")
        elif 'error' in ck:
            thread_safe_print(f"[{now}] [{tenfb}] LỖI: {ck['error']}")
        if ck.get('countdown', 0) > 0: time.sleep(ck['countdown'])

def run_single_account(acc_data, listnv, config_delays, xsmm_token, dl, doi):
    cookie = acc_data["cookie"]; proxy = acc_data.get("proxy", "")
    xsmm_thread = XSMMTool(token=xsmm_token)
    access = check_cookie_ig(cookie, proxy)
    is_live = False; tenfb = ""; idfb = ""
    try:
        cfg = json.loads(access)
        if cfg and 'form_data' in cfg and cfg['form_data'].get('username'):
            is_live = True; tenfb = cfg['form_data']['username']
            idfb_match = re.search(r'ds_user_id=(\d+)', cookie)
            idfb = idfb_match.group(1) if idfb_match else str(cfg['form_data'].get('id', ''))
    except: is_live = False
    if not is_live or not idfb:
        thread_safe_print(f"{red}[!] Cookie lỗi{reset}")
        return
    px = f" | Proxy: {proxy}" if proxy else ""
    thread_safe_print(f"{green}[+] NICK [{tenfb} | {idfb}{px}]{reset}")

    warmup_sess = c_requests.Session()
    wp = format_proxy(proxy)
    if wp: warmup_sess.proxies = wp
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); warmup_sess.cookies.set(k, v, domain='.instagram.com')
            except: pass
    ig_warmup(warmup_sess, cookie, proxy, tenfb)
    time.sleep(random.uniform(8, 15))

    try:
        acc_list = xsmm_thread.get_accounts(account_type="instagram", search=idfb)
        exists = False
        if isinstance(acc_list, dict) and acc_list.get("accounts"):
            for acc in acc_list["accounts"]:
                if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                    exists = True; break
        if not exists:
            xsmm_thread.add_account("instagram", f"https://www.instagram.com/{tenfb}")
    except: pass

    max_job = 0; cache = []
    while True:
        job = random.choice(listnv)
        if job == 'instagram_like':
            lv = xsmm_thread.get_tasks(job, uid=idfb)
            if isinstance(lv, list) and len(lv) > 0:
                solo = 0
                for nv in lv:
                    csf_m = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_m.group(1) if csf_m else ""
                    thread_safe_print(f"{yellow}[Tym] {nv.get('target_url', '')}{reset}")
                    chay = tym(nv.get('target_id', ''), cookie, csf, nv.get('target_url', ''), proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay)
                        if 'data' not in g and g.get('status') != 'ok': raise Exception(g.get('message', 'Block'))
                        thread_safe_print(f"{green}[+] TYM OK{reset}")
                        gui_nhan_xu("instagram_like", [nv.get('id')], idfb, cookie, xsmm_thread, tenfb)
                        solo = 0
                    except Exception as e:
                        thread_safe_print(f"{red}[!] TYM LỖI: {e}{reset}")
                        solo += 1
                    time.sleep(config_delays['tym'] + random.uniform(0, 3))
                    if solo > 4 or max_job >= doi: break
            else: time.sleep(dl)
        elif job == 'instagram_follow':
            lv = xsmm_thread.get_tasks(job, uid=idfb)
            if isinstance(lv, list) and len(lv) > 0:
                solo = 0
                for nv in lv:
                    tid = nv.get('target_id', ''); lj = nv.get('target_url', '')
                    if not tid or not str(tid).isdigit(): continue
                    csf_m = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_m.group(1) if csf_m else ""
                    thread_safe_print(f"{yellow}[Follow] {tid}{reset}")
                    chay = follow(tid, cookie, csf, lj, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay)
                        if 'data' not in g and g.get('status') not in ('ok', 'success'): solo += 1
                        else:
                            cache.append(nv.get('id')); solo = 0
                            thread_safe_print(f"{green}[+] Follow OK ({len(cache)}/10){reset}")
                            if len(cache) == 10:
                                gui_nhan_xu("instagram_follow", cache, idfb, cookie, xsmm_thread, tenfb)
                                cache = []; break
                    except: solo += 1
                    time.sleep(config_delays['follow'] + random.uniform(0, 5))
                    if solo > 4 or max_job >= doi: break
            else: time.sleep(dl)
        elif job == 'instagram_comment':
            lv = xsmm_thread.get_tasks(job, uid=idfb)
            if isinstance(lv, list) and len(lv) > 0:
                solo = 0
                for nv in lv:
                    idm = nv.get('target_id', ''); nd = nv.get('comment', '❤️❤️❤️'); lj = nv.get('target_url', '')
                    if not idm: continue
                    csf_m = re.search(r'csrftoken=([^;]+)', cookie)
                    csf = csf_m.group(1) if csf_m else ""
                    thread_safe_print(f"{yellow}[CMT] {lj}{reset}")
                    chay = cmt(idm, nd, cookie, csf, lj, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay)
                        if g.get('status') != 'ok' and 'data' not in g: raise Exception(g.get('message', 'Block'))
                        thread_safe_print(f"{green}[+] CMT OK{reset}")
                        gui_nhan_xu("instagram_comment", [nv.get('id')], idfb, cookie, xsmm_thread, tenfb)
                        solo = 0
                    except Exception as e:
                        thread_safe_print(f"{red}[!] CMT LỖI: {e}{reset}")
                        solo += 1
                    time.sleep(config_delays['comment'] + random.uniform(0, 5))
                    if solo > 4 or max_job >= doi: break
            else: time.sleep(dl)
        if max_job >= doi:
            thread_safe_print(f"{cyan}[*] Nghỉ {dl}s{reset}")
            time.sleep(dl); max_job = 0

def main():
    print(f"{cyan}===== XSMM TOOL V3.2 (WARMUP) ====={reset}")
    sys.stdout.write("Số luồng (1-50): "); sys.stdout.flush()
    try:
        max_threads = int(input().strip())
        if max_threads < 1: max_threads = 1
        if max_threads > 50: max_threads = 50
    except: max_threads = 10

    sys.stdout.write("Access Token XSMM: "); sys.stdout.flush()
    xsmm_token = input().strip()

    xsmm = XSMMTool(token=xsmm_token)
    ui = xsmm.get_user_info()
    if not (isinstance(ui, dict) and "user" in ui):
        print(f"{red}[!] Token sai{reset}"); sys.exit()

    print(f"{green}[+] XSMM: {ui['user'].get('username')}{reset}")

    sys.stdout.write("Số nick: "); sys.stdout.flush()
    try: luong = int(input().strip())
    except: luong = 1
    mangcookie = []; thu = 1
    while len(mangcookie) < luong:
        print(f"Cookie {thu}: "); sys.stdout.flush()
        c = input().strip()
        print(f"Proxy (Enter bỏ qua): "); sys.stdout.flush()
        p = input().strip()
        if not c: continue
        mangcookie.append({"cookie": c, "proxy": p}); thu += 1

    dl = 150; doi = 99999
    if len(mangcookie) == 1:
        sys.stdout.write("Dừng khi hết job (giây): "); sys.stdout.flush()
        try: dl = int(input().strip())
        except: dl = 150
    else:
        sys.stdout.write("Số job đổi nick: "); sys.stdout.flush()
        try:
            doi = int(input().strip())
            if doi < 1: doi = 99999
        except: doi = 99999

    listnv = []; cd = {'tym': 10, 'follow': 15, 'comment': 20}
    while True:
        sys.stdout.write("Tym (on/off): "); sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_like')
            sys.stdout.write("Delay Tym: "); sys.stdout.flush()
            try:
                cd['tym'] = int(input().strip())
                if cd['tym'] < 1: cd['tym'] = 10
            except: cd['tym'] = 10
        sys.stdout.write("Follow (on/off): "); sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_follow')
            sys.stdout.write("Delay Follow: "); sys.stdout.flush()
            try:
                cd['follow'] = int(input().strip())
                if cd['follow'] < 1: cd['follow'] = 15
            except: cd['follow'] = 15
        sys.stdout.write("CMT (on/off): "); sys.stdout.flush()
        if input().strip().lower() == 'on':
            listnv.append('instagram_comment')
            sys.stdout.write("Delay CMT: "); sys.stdout.flush()
            try:
                cd['comment'] = int(input().strip())
                if cd['comment'] < 10: cd['comment'] = 20
            except: cd['comment'] = 20
        if len(listnv) == 0: print(f"{red}Chọn ít nhất 1 job{reset}")
        else: break

    print(f"{cyan}[*] Chạy {len(mangcookie)} nick | {max_threads} luồng{reset}\n")
    with ThreadPoolExecutor(max_workers=max_threads) as ex:
        futures = [ex.submit(run_single_account, ad, listnv, cd, xsmm_token, dl, doi) for ad in mangcookie]
    print(f"{green}[+] Xong!{reset}")

if __name__ == "__main__":
    main()
'''

# ============================================================================
# ==================== TOOL 2: xsmmigv5.2.py (WARMUP + ĐẾM FL) ==============
# ============================================================================
TOOL_CODE_XSMMIGV52 = r'''import os
import sys
import time
import json
import re
from datetime import datetime
import random
from urllib.parse import unquote
from curl_cffi import requests as c_requests
import requests

red = "\033[1;31m"; green = "\033[1;32m"; yellow = "\033[1;33m"
cyan = "\033[1;36m"; white = "\033[0;37m"; reset = "\033[0m"

class XSMMTool:
    def __init__(self, token):
        self.base_url = "https://xsmm.net/api/taskapi"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    def get_user_info(self):
        try: return requests.get(f"{self.base_url}/user", headers=self.headers, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def get_accounts(self, account_type=None, search=None):
        params = {}
        if account_type: params['account_type'] = account_type
        if search: params['search'] = search
        try: return requests.get(f"{self.base_url}/accounts2", headers=self.headers, params=params, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def add_account(self, account_type, link_account):
        try: return requests.post(f"{self.base_url}/accounts2", headers=self.headers, json={"type": account_type, "link_account": link_account}, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def get_tasks(self, job_type, uid, typejob="normal,better,best"):
        try: return requests.get(f"{self.base_url}/tasks2", headers=self.headers, params={"type": job_type, "uid": str(uid), "typejob": typejob}, timeout=20).json()
        except Exception as e: return {"error": str(e)}
    def complete_tasks(self, job_type, task_ids, uid, cookie_check="", max_retries=3):
        payload = {"type": job_type, "task_id": task_ids if isinstance(task_ids, list) else [task_ids], "uid": str(uid)}
        if cookie_check: payload["cookie_check"] = cookie_check
        attempt = 0
        while attempt < max_retries:
            try:
                r = requests.post(f"{self.base_url}/tasks2/complete", headers=self.headers, json=payload, timeout=35)
                rd = r.json()
                if isinstance(rd, dict) and rd.get("retry") is True:
                    time.sleep(random.randint(10, 15)); attempt += 1; continue
                return rd
            except requests.exceptions.Timeout:
                return {"is_timeout": True, "message": "Server chậm"}
            except Exception as e: return {"error": str(e)}
        return {"error": "Retry failed"}

BROWSER_PROFILES = [
    {"name": "Chrome 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Chrome 120", "impersonate": "chrome120", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"', "sec_ch_ua_platform": '"Windows"'},
    {"name": "Edge 124", "impersonate": "chrome124", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0", "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"', "sec_ch_ua_platform": '"Windows"'},
]

def format_proxy(p):
    if not p: return None
    p = p.strip()
    if not p: return None
    scheme = "http"
    if "://" in p: scheme, p = p.split("://", 1)
    parts = p.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        f = f"{scheme}://{user}:{pwd}@{ip}:{port}"
    else: f = f"{scheme}://{p}"
    return {"http": f, "https": f}

def get_ig_headers(cookie, csrftoken, referer="https://www.instagram.com/", profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    return {'accept': '*/*', 'accept-language': 'vi,en-US;q=0.9,en;q=0.8,vi-VN;q=0.7',
            'content-type': 'application/x-www-form-urlencoded', 'cookie': cookie,
            'origin': 'https://www.instagram.com', 'priority': 'u=1, i', 'referer': referer,
            'sec-ch-prefers-color-scheme': 'dark', 'sec-ch-ua': profile['sec_ch_ua'],
            'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': profile['sec_ch_ua_platform'],
            'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
            'user-agent': profile['user_agent'], 'x-asbd-id': '359341', 'x-csrftoken': csrftoken,
            'x-ig-app-id': '936619743392459', 'x-ig-www-claim': '0', 'x-requested-with': 'XMLHttpRequest'}

CACHE_TOKENS = {}
def get_tokens(session, cookie, profile_url, imp):
    m = re.search(r'ds_user_id=(\d+)', cookie)
    uid = m.group(1) if m else "default"
    if uid in CACHE_TOKENS and CACHE_TOKENS[uid][1]: return CACHE_TOKENS[uid]
    fb_dtsg, lsd, jazoest = "", "7q44S3aBoCQ_1VuGgqlys8", "26485"
    try:
        r = session.get(profile_url or "https://www.instagram.com/", impersonate=imp, timeout=20).text
        m = re.search(r'"LSD",\[\],{"token":"([^"]+)"}', r)
        if m: lsd = m.group(1)
        m = re.search(r'"dtsg":\{"token":"([^"]+)"', r) or re.search(r'name="fb_dtsg" value="([^"]+)"', r)
        if m: fb_dtsg = m.group(1)
    except Exception: pass
    CACHE_TOKENS[uid] = (fb_dtsg, lsd, jazoest)
    return CACHE_TOKENS[uid]

def check_cookie_ig(cookie, proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    url = 'https://www.instagram.com/api/v1/accounts/edit/web_form_data/'
    h = {'x-ig-app-id': '936619743392459', 'x-requested-with': 'XMLHttpRequest',
         'referer': 'https://www.instagram.com/accounts/edit/', 'cookie': cookie,
         'user-agent': profile['user_agent'], 'sec-ch-ua': profile['sec_ch_ua'],
         'sec-ch-ua-platform': profile['sec_ch_ua_platform']}
    try: return c_requests.get(url, headers=h, proxies=format_proxy(proxy), impersonate=profile["impersonate"], timeout=30).text
    except Exception: return "{}"

def ig_warmup_v52(session, cookie, profile):
    print(f"{cyan}[*] Warmup...{reset}")
    try:
        session.get("https://www.instagram.com/", impersonate=profile["impersonate"], timeout=15)
        time.sleep(random.uniform(3, 6))
        targets = ["instagram", "cristiano", "natgeo", "therock", "leomessi"]
        for t in random.sample(targets, random.randint(1, 2)):
            try:
                session.get(f"https://www.instagram.com/{t}/", impersonate=profile["impersonate"], timeout=10)
                time.sleep(random.uniform(4, 8))
            except: pass
        session.get("https://www.instagram.com/explore/", impersonate=profile["impersonate"], timeout=15)
        time.sleep(random.uniform(5, 10))
        print(f"{green}[+] Warmup done{reset}")
        return True
    except Exception as e:
        print(f"{yellow}[!] Warmup fail: {e}{reset}")
        return False

def follow(target_id, cookie, csrftoken, profile_url="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not target_id: return '{"status": "error"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens(session, cookie, profile_url, profile["impersonate"])
    dyn = session.cookies.get('csrftoken')
    if not dyn:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn, profile_url or "https://www.instagram.com/", profile))
    actor_m = re.search(r'ds_user_id=(\d+)', cookie)
    actor = actor_m.group(1) if actor_m else "0"
    variables = {"target_user_id": str(target_id), "container_module": "profile",
                 "nav_chain": "PolarisFeedRoot:feedPage:5:topnav-link,PolarisProfileRoot:profilePage:6:unexpected"}
    data = {"av": actor, "__d": "www", "__user": "0", "__a": "1", "__req": "s",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "usePolarisFollowMutation",
            "server_timestamps": "true", "doc_id": "26508036048874888", "variables": json.dumps(variables)}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def tym(mediaid, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not mediaid: return '{"status": "error"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens(session, cookie, link_job, profile["impersonate"])
    dyn = session.cookies.get('csrftoken')
    if not dyn:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn, link_job or "https://www.instagram.com/", profile))
    actor_m = re.search(r'ds_user_id=(\d+)', cookie)
    actor = actor_m.group(1) if actor_m else "0"
    variables = {"input": {"actor_id": actor, "client_mutation_id": str(random.randint(1000000, 9999999)),
                           "container_module": "single_post", "media_id": str(mediaid)}}
    data = {"av": actor, "__d": "www", "__user": "0", "__a": "1", "__req": "h",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046913831", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "usePolarisLikeMediaXIGLikeMutation",
            "server_timestamps": "true", "doc_id": "27182485238052618", "variables": json.dumps(variables)}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def cmt(mediaid, text, cookie, csrftoken, link_job="", proxy=None, profile=None):
    if not profile: profile = BROWSER_PROFILES[0]
    if not mediaid: return '{"status": "error"}'
    cookie = unquote(cookie); session = c_requests.Session()
    proxies = format_proxy(proxy)
    if proxies: session.proxies = proxies
    for item in cookie.split(';'):
        if '=' in item:
            try:
                k, v = item.strip().split('=', 1); session.cookies.set(k, v, domain='.instagram.com')
            except Exception: pass
    fb_dtsg, lsd, jazoest = get_tokens(session, cookie, link_job, profile["impersonate"])
    dyn = session.cookies.get('csrftoken')
    if not dyn:
        m = re.search(r'csrftoken=([^;]+)', cookie); dyn = m.group(1) if m else "missing"
    session.headers.update(get_ig_headers(cookie, dyn, link_job or "https://www.instagram.com/", profile))
    actor_m = re.search(r'ds_user_id=(\d+)', cookie)
    actor = actor_m.group(1) if actor_m else "0"
    variables = {"connections": [f'client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:"{mediaid}",sort_order:"popular")'],
                 "data": {"comment_text": text, "media_id": str(mediaid)}}
    data = {"av": actor, "__d": "www", "__user": "0", "__a": "1", "__req": "10",
            "__hs": "20702.HYP:instagram_web_pkg.2.1...0", "dpr": "1", "__ccg": "EXCELLENT",
            "__rev": "1046917461", "__comet_req": "7", "fb_dtsg": fb_dtsg, "jazoest": jazoest,
            "lsd": lsd, "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
            "server_timestamps": "true", "doc_id": "27261905640092552", "variables": json.dumps(variables)}
    try: return session.post('https://www.instagram.com/api/graphql', data=data, impersonate=profile["impersonate"], timeout=30).text.strip()
    except Exception as e: return json.dumps({"status": "error", "message": str(e)})

def parse_resp(t):
    try: g = json.loads(t)
    except Exception as e: return False, f"Parse err"
    if not isinstance(g, dict): return False, "Invalid"
    if "errors" in g and g["errors"]: return False, "IG err"
    if g.get("status") == "fail": return False, g.get("message", "fail")
    return True, "OK"

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm):
    if not task_list: return
    print(f"Gom {len(task_list)} task -> Gửi duyệt...")
    ck = xsmm.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        if 'message' in ck:
            print(f"[{now}] {ck['message']} (+{ck.get('points', 0)} xu)")
        elif ck.get("is_timeout"):
            print(f"[{now}] {ck['message']}")
        elif 'error' in ck:
            print(f"[{now}] LỖI: {ck['error']}")
        if ck.get('countdown', 0) > 0: time.sleep(ck['countdown'])

def main():
    print(f"{cyan}===== XSMM IG V5.2 (WARMUP) ====={reset}")
    sys.stdout.write("Access Token XSMM: "); sys.stdout.flush()
    token = input().strip()

    sys.stdout.write("Cookie Check riêng? (1=Có / 0=Không): "); sys.stdout.flush()
    ck_choice = input().strip()
    ck_global = ""
    if ck_choice == '1':
        sys.stdout.write("Dán Cookie Check Web: "); sys.stdout.flush()
        ck_global = input().strip()

    sys.stdout.write("Số nick: "); sys.stdout.flush()
    try: luong = int(input().strip())
    except: luong = 1
    mangcookie = []; thu = 1
    while len(mangcookie) < luong:
        print(f"Cookie App {thu}: "); sys.stdout.flush()
        c = input().strip()
        print("Proxy (Enter bỏ qua): "); sys.stdout.flush()
        p = input().strip()
        if not c: continue
        prof = random.choice(BROWSER_PROFILES)
        acc = check_cookie_ig(c, p, profile=prof)
        try:
            cfg = json.loads(acc)
            if cfg and 'form_data' in cfg and cfg['form_data'].get('username'):
                mangcookie.append({"cookie": c, "proxy": p, "profile": prof}); thu += 1
            else: print("[!] Cookie/Proxy lỗi")
        except Exception: print("[!] Cookie/Proxy lỗi")

    sys.stdout.write("Số job đổi nick: "); sys.stdout.flush()
    try:
        doi = int(input().strip())
        if doi < 1: doi = 99999
    except: doi = 99999

    listnv = []; dly = {'tym': (10, 15), 'follow': (15, 20), 'cmt': (20, 25)}
    def parse_r(v, dmin, dmax):
        v = str(v).strip()
        if not v: return dmin, dmax
        if '-' in v:
            try:
                a, b = v.split('-'); a = int(a.strip()); b = int(b.strip())
                return (a, b) if a <= b else (b, a)
            except: return dmin, dmax
        try: s = int(v); return s, s
        except: return dmin, dmax

    sys.stdout.write("Tym (on/off): "); sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_like')
        sys.stdout.write("Delay Tym: "); sys.stdout.flush()
        dly['tym'] = parse_r(input().strip(), 10, 15)
    sys.stdout.write("Follow (on/off): "); sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_follow')
        sys.stdout.write("Delay Follow: "); sys.stdout.flush()
        dly['follow'] = parse_r(input().strip(), 15, 20)
    sys.stdout.write("CMT (on/off): "); sys.stdout.flush()
    if input().strip().lower() == 'on':
        listnv.append('instagram_comment')
        sys.stdout.write("Delay CMT: "); sys.stdout.flush()
        dly['cmt'] = parse_r(input().strip(), 20, 25)

    if not listnv: print(f"{red}[!] Chưa chọn job{reset}"); sys.exit()

    print(f"{cyan}[*] Chạy {len(mangcookie)} nick{reset}\n")
    xsmm = XSMMTool(token=token)
    while True:
        for l in range(len(mangcookie)-1, -1, -1):
            ad = mangcookie[l]
            c = ad["cookie"]; p = ad.get("proxy", ""); prof = ad.get("profile") or BROWSER_PROFILES[0]
            target_ck = ck_global if ck_global else c
            acc = check_cookie_ig(c, p, profile=prof)
            live = False; tenfb = ""; idfb = ""
            try:
                cfg = json.loads(acc)
                if cfg and 'form_data' in cfg and cfg['form_data'].get('username'):
                    live = True; tenfb = cfg['form_data']['username']
                    m = re.search(r'ds_user_id=(\d+)', c); idfb = m.group(1) if m else str(cfg['form_data'].get('id', ''))
            except: live = False
            if not live or not idfb:
                print(f"{red}[!] Cookie die{reset}"); mangcookie.pop(l); continue
            print(f"{green}[+] [{tenfb} | {idfb}]{reset}")

            warmup_sess = c_requests.Session()
            wp = format_proxy(p)
            if wp: warmup_sess.proxies = wp
            for item in c.split(';'):
                if '=' in item:
                    try:
                        k, v = item.strip().split('=', 1); warmup_sess.cookies.set(k, v, domain='.instagram.com')
                    except Exception: pass
            ig_warmup_v52(warmup_sess, c, prof)
            time.sleep(random.uniform(8, 15))

            try:
                al = xsmm.get_accounts(account_type="instagram", search=idfb)
                if not (isinstance(al, dict) and al.get("accounts") and any(
                    str(a.get("account_id")) == str(idfb) for a in al["accounts"])):
                    xsmm.add_account("instagram", f"https://www.instagram.com/{tenfb}")
            except Exception: pass

            max_j = 0
            cache = []
            while max_j < doi:
                jt = random.choice(listnv)
                jl = random.randint(3, 5); jdt = 0
                if jt == 'instagram_like':
                    lv = xsmm.get_tasks(jt, uid=idfb)
                    if isinstance(lv, list) and lv:
                        solo = 0
                        for nv in lv:
                            csf_m = re.search(r'csrftoken=([^;]+)', c); csf = csf_m.group(1) if csf_m else ""
                            print(f"[Tym] {nv.get('target_url', '')}")
                            r = tym(nv.get('target_id', ''), c, csf, nv.get('target_url', ''), proxy=p, profile=prof)
                            max_j += 1; jdt += 1
                            ok, err = parse_resp(r)
                            if ok:
                                gui_nhan_xu("instagram_like", [nv.get('id')], idfb, target_ck, xsmm); solo = 0
                            else: print(f"LỖI: {err}"); solo += 1
                            time.sleep(random.randint(*dly['tym']) + random.uniform(0, 3))
                            if solo > 4 or jdt >= jl or max_j >= doi: break
                elif jt == 'instagram_follow':
                    lv = xsmm.get_tasks(jt, uid=idfb)
                    if isinstance(lv, list) and lv:
                        solo = 0
                        for nv in lv:
                            tid = nv.get('target_id', ''); lj = nv.get('target_url', '')
                            if not tid or not str(tid).isdigit(): continue
                            csf_m = re.search(r'csrftoken=([^;]+)', c); csf = csf_m.group(1) if csf_m else ""
                            print(f"[Follow] {tid}")
                            r = follow(tid, c, csf, lj, proxy=p, profile=prof)
                            max_j += 1; jdt += 1
                            ok, _ = parse_resp(r)
                            
                            if ok: 
                                solo = 0
                                cache.append(nv.get('id'))
                                print(f"   [+] Follow OK -> Đã gom ({len(cache)}/10)")
                                if len(cache) >= 10:
                                    gui_nhan_xu("instagram_follow", cache, idfb, target_ck, xsmm)
                                    cache = [] # Reset
                            else:
                                print(f"   [-] Fail (Private/Block)")
                                solo += 1
                                
                            time.sleep(random.randint(*dly['follow']) + random.uniform(0, 5))
                            if solo > 4 or jdt >= jl or max_j >= doi: break
                elif jt == 'instagram_comment':
                    lv = xsmm.get_tasks(jt, uid=idfb)
                    if isinstance(lv, list) and lv:
                        solo = 0
                        for nv in lv:
                            idm = nv.get('target_id', ''); nd = nv.get('comment', '❤️❤️❤️'); lj = nv.get('target_url', '')
                            if not idm: continue
                            csf_m = re.search(r'csrftoken=([^;]+)', c); csf = csf_m.group(1) if csf_m else ""
                            print(f"[CMT] {lj}")
                            r = cmt(idm, nd, c, csf, lj, proxy=p, profile=prof)
                            max_j += 1; jdt += 1
                            ok, err = parse_resp(r)
                            if ok:
                                gui_nhan_xu("instagram_comment", [nv.get('id')], idfb, target_ck, xsmm); solo = 0
                            else: print(f"LỖI: {err}"); solo += 1
                            time.sleep(random.randint(*dly['cmt']) + random.uniform(0, 5))
                            if solo > 4 or jdt >= jl or max_j >= doi: break
                time.sleep(15)
        if len(mangcookie) == 0: print(f"{red}[!] Hết cookie{reset}"); break

if __name__ == "__main__":
    main()
'''

# ============================================================================
# ==================== TOOL 3: 11223.py (WARMUP) =============================
# ============================================================================
TOOL_CODE_11223 = r'''import time
import json
import urllib.parse
import re
import sys
import os
import random
import requests
import signal

def handle_sigint(sig, frame): os._exit(0)
signal.signal(signal.SIGINT, handle_sigint)

XSMM_TOKEN = ""
XSMM_HEADERS = {}

def set_token(token):
    global XSMM_TOKEN, XSMM_HEADERS
    XSMM_TOKEN = token
    XSMM_HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def parse_cookie_string(s):
    cookies = {}
    s = s.strip().rstrip(',')
    for item in s.split(';'):
        if '=' in item:
            p = item.strip().split('=', 1)
            if len(p) == 2: cookies[p[0].strip()] = p[1].strip()
    return cookies

def get_media_id(inp):
    inp = str(inp).strip()
    m = re.search(r'/p/([A-Za-z0-9_-]+)', inp) or re.search(r'/reel/([A-Za-z0-9_-]+)', inp)
    if m:
        sc = m.group(1)
        alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
        mid = 0
        for ch in sc: mid = (mid * 64) + alpha.index(ch)
        return str(mid)
    return inp

class INSTAGRAM:
    def __init__(self, ck_str):
        self.cookies = parse_cookie_string(ck_str)
        self.csrftoken = self.cookies.get('csrftoken', '')

    def GETINFO(self):
        try:
            h = {'accept': 'text/html,*/*;q=0.8',
                 'accept-language': 'vi-VN,vi;q=0.9',
                 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/135.0.0.0 Safari/537.36'}
            r = requests.get("https://www.instagram.com/", headers=h, cookies=self.cookies).text
            m = re.search(r'"viewerId":"(\d+)"', r)
            if not m:
                m2 = re.findall(r'userID":.*?,', r)
                uid = m2[0].split(':"')[1].split('",')[0] if m2 else None
            else: uid = m.group(1)
            um = re.search(r'"username":"([^"]+)"', r)
            un = um.group(1) if um else uid
            dm = re.search(r'"dtsg":\s*\{"token":"([^"]+)"', r)
            dtsg = dm.group(1) if dm else ""
            return uid, dtsg, "", un
        except Exception: return False, False, False, False

    def LIKE(self, av, dtsg, post_id, cookies, link, lsd):
        mid = get_media_id(link if link else post_id)
        h = {'User-Agent': 'Instagram 269.0.0.18.75 Android',
             'X-IG-App-ID': '1217981644879628', 'X-CSRFToken': self.csrftoken,
             'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        try:
            r = requests.post(f"https://i.instagram.com/api/v1/media/{mid}/like/", cookies=self.cookies,
                              headers=h, data={'module_name': 'feed_timeline', 'media_id': mid})
            if r.status_code == 200:
                try:
                    if r.json().get('status') == 'ok': return True
                except:
                    if "ok" in r.text.lower(): return True
            return False
        except Exception: return False

    def FOLLOW(self, dtsg, tid):
        url = f"https://www.instagram.com/api/v1/friendships/create/{tid}/"
        h = {'accept': '*/*', 'content-type': 'application/x-www-form-urlencoded',
             'origin': 'https://www.instagram.com', 'referer': 'https://www.instagram.com/',
             'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36',
             'x-csrftoken': self.csrftoken, 'x-ig-app-id': '1217981644879628', 'x-requested-with': 'XMLHttpRequest'}
        data = {'container_module': 'profile', 'user_id': str(tid), 'jazoest': '22613',
                'fb_dtsg': dtsg or 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}
        try:
            r = requests.post(url, cookies=self.cookies, headers=h, data=data)
            if r.status_code == 200:
                try:
                    j = r.json()
                    if j.get('status') == 'ok' or j.get('friendship_status', {}).get('following') == True: return True
                except:
                    if "ok" in r.text.lower(): return True
            return False
        except Exception: return False

    def COMMENT(self, av, dtsg, tid, turl, content):
        url = "https://www.instagram.com/api/graphql"
        mid = get_media_id(turl if turl else tid)
        h = {"accept": "*/*", "content-type": "application/x-www-form-urlencoded",
             "origin": "https://www.instagram.com",
             "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36",
             "x-csrftoken": self.csrftoken, "x-ig-app-id": "1217981644879628", "x-requested-with": "XMLHttpRequest"}
        variables = ('{"connections":["client:root:__PolarisPostComments__xdt_api__v1__media__' + mid +
                     '__comments__connection_connection(data:{},media_id:\\"' + mid + '\\",sort_order:\\"popular\\")"],"data":{"comment_text":"' + content + '","media_id":"' + mid + '"}}')
        data = (f"av={av}&__d=www&__user=0&__a=1&__req=31&__hs=20716.HYP%3Ainstagram_web_pkg&dpr=3&__ccg=EXCELLENT"
                f"&fb_dtsg={dtsg or 'NAfw7uEKgkrIMU2uHq9loxwB_G4Ai8jtT0G9FzGOC4w'}&jazoest=26096"
                "&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=PolarisPostCommentInputRevampedMutation&server_timestamps=true"
                f"&variables={urllib.parse.quote(variables)}&doc_id=27261905640092552")
        try:
            r = requests.post(url, headers=h, data=data)
            if r.status_code == 200:
                try:
                    j = r.json()
                    if "data" in j or j.get("status") == "ok": return True
                except:
                    if "ok" in r.text.lower(): return True
            return False
        except Exception: return False

def warmup_simple(ig, av, dtsg, cookie):
    print("[*] Warmup (xem feed + follow nhẹ)...")
    try:
        h = {'accept': 'text/html', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
             'cookie': cookie}
        requests.get("https://www.instagram.com/", headers=h, timeout=15)
        time.sleep(random.uniform(3, 6))
        targets = ["instagram", "cristiano", "natgeo"]
        for t in random.sample(targets, random.randint(1, 2)):
            try:
                requests.get(f"https://www.instagram.com/{t}/", headers=h, timeout=10)
                time.sleep(random.uniform(4, 8))
            except: pass
        requests.get("https://www.instagram.com/explore/", headers=h, timeout=15)
        time.sleep(random.uniform(5, 10))
        print("[+] Warmup done")
        return True
    except Exception as e:
        print(f"[!] Warmup fail: {e}")
        return False

def get_user():
    try: return requests.get("https://xsmm.net/api/taskapi/user", headers=XSMM_HEADERS).json().get("user", {})
    except: return {}

def get_ig_accounts(search_uid=""):
    try:
        url = "https://xsmm.net/api/taskapi/accounts2?account_type=instagram"
        if search_uid: url += f"&search={search_uid}"
        res = requests.get(url, headers=XSMM_HEADERS).json()
        return res.get("accounts", []) if isinstance(res, dict) else []
    except: return []

def sync_xsmm_id(un, fb_av):
    try:
        requests.post("https://xsmm.net/api/taskapi/accounts2", headers=XSMM_HEADERS,
                      json={"type": "instagram", "link_account": f"https://www.instagram.com/{un}"})
    except: pass
    for acc in get_ig_accounts(search_uid=fb_av):
        if isinstance(acc, dict):
            if str(acc.get("account_id")) == str(fb_av) or un.lower() in str(acc.get("link_account", "")).lower():
                return acc.get("account_id") or acc.get("id")
    return fb_av

def get_tasks(tt, uid):
    try:
        r = requests.get(f"https://xsmm.net/api/taskapi/tasks2?type={tt}&uid={uid}&typejob=normal", headers=XSMM_HEADERS).json()
        return r if isinstance(r, list) else []
    except: return []

def complete_tasks(tt, uid, tids, ck_check):
    try:
        r = requests.post("https://xsmm.net/api/taskapi/tasks2/complete", headers=XSMM_HEADERS,
                          json={"type": tt, "task_id": tids, "uid": str(uid), "cookie_check": ck_check}).json()
        return r if isinstance(r, dict) else {}
    except: return {}

def main():
    print("=" * 50)
    print("   SIMPLE IG BOT + WARMUP")
    print("=" * 50)

    sys.stdout.write("Access Token XSMM: "); sys.stdout.flush()
    set_token(input().strip())

    ui = get_user()
    print(f"Tài khoản: {ui.get('username')} | Xu: {ui.get('points')}")

    sys.stdout.write("Cookie Instagram: "); sys.stdout.flush()
    ck = input().strip()
    if not ck: print("Cookie trống!"); return

    sys.stdout.write("Task (1=LIKE 2=FOLLOW 3=COMMENT): "); sys.stdout.flush()
    ch = input().strip()
    tt = {"1": "instagram_like", "2": "instagram_follow", "3": "instagram_comment"}.get(ch, "instagram_like")

    sys.stdout.write("Delay min: "); sys.stdout.flush()
    try: dmin = int(input().strip() or 10)
    except: dmin = 10
    sys.stdout.write("Delay max: "); sys.stdout.flush()
    try: dmax = int(input().strip() or 15)
    except: dmax = 15
    sys.stdout.write("Delay coin min: "); sys.stdout.flush()
    try: dcmin = int(input().strip() or 3)
    except: dcmin = 3
    sys.stdout.write("Delay coin max: "); sys.stdout.flush()
    try: dcmax = int(input().strip() or 5)
    except: dcmax = 5

    print("[*] Check cookie...")
    ig = INSTAGRAM(ck)
    info = ig.GETINFO()
    if info == False: print("Cookie die!"); return
    av, dtsg, _, un = info
    if not av: print("No UID!"); return
    print(f"[+] OK - {un} - AV: {av}")
    xsmm_uid = sync_xsmm_id(un, av)
    print(f"[+] XSMM UID: {xsmm_uid}")

    # Warmup trước khi chạy
    warmup_simple(ig, av, dtsg, ck)
    time.sleep(random.uniform(8, 15))

    total = 0; cache = []
    while True:
        tasks = get_tasks(tt, xsmm_uid)
        if not tasks: print("[-] Không có job. Chờ 10s..."); time.sleep(10); continue
        print(f"[+] {len(tasks)} job")
        for i, task in enumerate(tasks, 1):
            tid = task.get("id"); target = task.get("target_id"); turl = task.get("target_url")
            ccontent = task.get("msg") or task.get("comment") or "Tuyệt vời!"
            idorlink = task.get("idorlink") or turl or target or "?"
            print(f"-> [{i}/{len(tasks)}]: {idorlink}")
            done = False
            if tt == "instagram_like": done = ig.LIKE(av, dtsg, target, ck, turl, "")
            elif tt == "instagram_follow": done = ig.FOLLOW(dtsg, target if target else get_media_id(idorlink))
            elif tt == "instagram_comment": done = ig.COMMENT(av, dtsg, target, turl, ccontent)

            if done:
                print("   [+] OK"); total += 1
                if tt in ["instagram_like", "instagram_comment"]:
                    res = complete_tasks(tt, xsmm_uid, [tid], ck)
                    print(f"   [>>] {res}")
                    time.sleep(random.randint(dcmin, dcmax))
                elif tt == "instagram_follow":
                    cache.append(tid); print(f"   [>>] Cache: {len(cache)}/12")
                    if len(cache) >= 12:
                        res = complete_tasks(tt, xsmm_uid, cache, ck)
                        print(f"   [>>] {res}"); cache = []
                        time.sleep(random.randint(dcmin, dcmax))
                if total % 5 == 0:
                    r = random.randint(20, 30); print(f"[*] Nghỉ {r}s..."); time.sleep(r)
            else: print("   [-] Fail")
            time.sleep(random.randint(dmin, dmax) + random.uniform(0, 3))
        print("--- Đợt tiếp ---"); time.sleep(5)

if __name__ == "__main__":
    main()
'''


# ============================================================================
# ==================== KHAI BÁO TOOLS ========================================
# ============================================================================
EMBEDDED_TOOLS = {
    "xsmmv3.2": {
        "name": "XSMM Tool V3.2",
        "desc": "Tool Instagram Auto Jobs - Multi-thread + Warmup",
        "color": "#00d4ff",
        "filename": "xsmmv3.2.py",
        "code": TOOL_CODE_XSMMV32,
    },
    "xsmmigv5.2": {
        "name": "XSMM IG V5.2",
        "desc": "Tool Instagram - Browser Profiles + Warmup",
        "color": "#ff6b9d",
        "filename": "xsmmigv5.2.py",
        "code": TOOL_CODE_XSMMIGV52,
    },
    "11223": {
        "name": "Simple IG Bot",
        "desc": "Tool Like/Follow/Comment + Warmup",
        "color": "#ffd93d",
        "filename": "11223.py",
        "code": TOOL_CODE_11223,
    },
}

TOOL_INFO = {k: {"name": v["name"], "desc": v["desc"], "color": v["color"]} for k, v in EMBEDDED_TOOLS.items()}

# ============================================================================
# ==================== FB REG PAGE (MULTI-THREAD) ============================
# ============================================================================
def fb_get_dtsg(cookie):
    try:
        headers = {
            'cookie': cookie,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get('https://www.facebook.com/settings', headers=headers, timeout=15)
        dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', r.text)
        jz = re.search(r'name="jazoest" value="(.*?)"', r.text)
        if dtsg and jz: return dtsg.group(1), jz.group(1)
        alt = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', r.text)
        if alt: return alt.group(1), "22"
    except Exception: pass
    return None, None

def fb_create_page_worker(idx, cookie, page_name, category_id, proxy, result_list):
    result = {
        "idx": idx, "uid": "", "page_id": "", "page_name": page_name,
        "ip": proxy or "Direct", "timezone": "Asia/Ho_Chi_Minh",
        "status": "Đang xử lý...", "ok": False,
    }
    try:
        m = re.search(r'c_user=(\d+)', cookie)
        if m: result["uid"] = m.group(1)

        proxies = None
        if proxy:
            p = proxy.strip()
            if "://" not in p: p = "http://" + p
            proxies = {"http": p, "https": p}

        headers = {
            'cookie': cookie,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            r = requests.get('https://www.facebook.com/settings', headers=headers, proxies=proxies, timeout=20)
            dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', r.text)
            jz = re.search(r'name="jazoest" value="(.*?)"', r.text)
            if dtsg and jz:
                fb_dtsg, jazoest = dtsg.group(1), jz.group(1)
            else:
                alt = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"}', r.text)
                if alt: fb_dtsg, jazoest = alt.group(1), "22"
                else:
                    result["status"] = "Cookie die / không lấy được fb_dtsg"
                    result_list.append(result); return
        except Exception as e:
            result["status"] = f"Lỗi kết nối: {str(e)[:50]}"
            result_list.append(result); return

        headers2 = {
            'cookie': cookie,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com/pages/creation/'
        }
        payload = {
            'fb_dtsg': fb_dtsg, 'jazoest': jazoest,
            'variables': json.dumps({
                "input": {
                    "actor_id": result["uid"], "client_mutation_id": "1",
                    "name": page_name, "category_id": category_id, "creation_source": "comet"
                }
            }),
            'doc_id': '5814795813638014'
        }
        try:
            r = requests.post("https://www.facebook.com/api/graphql/", headers=headers2, data=payload, proxies=proxies, timeout=25)
            res = r.json()
            if 'errors' in res:
                result["status"] = f"FB lỗi: {res['errors'][0].get('message', '')[:80]}"
                result_list.append(result); return
            data = res.get('data', {})
            pid_match = re.search(r'"page_id":"(\d+)"', json.dumps(data))
            if pid_match:
                result["page_id"] = pid_match.group(1)
                result["status"] = "Tạo OK"
                result["ok"] = True
            else:
                result["status"] = "Không có page_id (fail)"
        except Exception as e:
            result["status"] = f"Lỗi GraphQL: {str(e)[:50]}"
        result_list.append(result)
    except Exception as e:
        result["status"] = f"Lỗi: {str(e)[:50]}"
        result_list.append(result)

def run_fb_reg_page_thread(task_queue, result_list, threads_count):
    FB_REG_STATE["running"] = True
    FB_REG_STATE["start_time"] = time.time()

    def worker():
        while True:
            try: task = task_queue.get_nowait()
            except: break
            idx, cookie, page_name, category_id, proxy = task
            try:
                fb_create_page_worker(idx, cookie, page_name, category_id, proxy, result_list)
                with FB_REG_LOCK:
                    latest = result_list[-1] if result_list else None
                    if latest and latest.get("ok"): FB_REG_STATE["total_success"] += 1
                    else: FB_REG_STATE["total_fail"] += 1
                    socketio.emit('fb_reg_update', {
                        "result": latest,
                        "stats": {
                            "success": FB_REG_STATE["total_success"],
                            "fail": FB_REG_STATE["total_fail"],
                            "elapsed": int(time.time() - FB_REG_STATE["start_time"]),
                        }
                    })
            except Exception as e:
                with FB_REG_LOCK: FB_REG_STATE["total_fail"] += 1
            finally: task_queue.task_done()

    threads = []
    for _ in range(threads_count):
        t = threading.Thread(target=worker, daemon=True)
        t.start(); threads.append(t)
    for t in threads: t.join()

    FB_REG_STATE["running"] = False
    socketio.emit('fb_reg_done', {
        "success": FB_REG_STATE["total_success"],
        "fail": FB_REG_STATE["total_fail"],
        "elapsed": int(time.time() - FB_REG_STATE["start_time"]),
    })

@app.route('/api/fb_reg_start', methods=['POST'])
def api_fb_reg_start():
    if FB_REG_STATE["running"]: return jsonify({"ok": False, "error": "Đang chạy rồi!"})
    data = request.json or {}
    tasks = data.get('tasks', [])
    threads_count = int(data.get('threads', 10))
    if not tasks: return jsonify({"ok": False, "error": "Không có task"})

    FB_REG_STATE["running"] = True
    FB_REG_STATE["results"] = []
    FB_REG_STATE["total_success"] = 0
    FB_REG_STATE["total_fail"] = 0

    task_queue = Queue()
    for i, t in enumerate(tasks):
        task_queue.put((i + 1, t['cookie'], t['page_name'], t.get('category_id', '2200'), t.get('proxy', '')))

    result_list = []
    thread = threading.Thread(target=run_fb_reg_page_thread, args=(task_queue, result_list, threads_count), daemon=True)
    thread.start()
    return jsonify({"ok": True, "message": f"Đã bắt đầu {len(tasks)} task với {threads_count} luồng"})

@app.route('/api/fb_reg_stop', methods=['POST'])
def api_fb_reg_stop():
    FB_REG_STATE["running"] = False
    return jsonify({"ok": True})

@app.route('/api/fb_reg_stats')
def api_fb_reg_stats():
    return jsonify({
        "running": FB_REG_STATE["running"],
        "success": FB_REG_STATE["total_success"],
        "fail": FB_REG_STATE["total_fail"],
        "elapsed": int(time.time() - FB_REG_STATE["start_time"]) if FB_REG_STATE["start_time"] else 0,
    })

# ============================================================================
# ==================== FLASK ROUTES ==========================================
# ============================================================================
def ensure_tool_file(tool_key):
    if tool_key not in EMBEDDED_TOOLS: return None, f"Tool không hợp lệ: {tool_key}"
    info = EMBEDDED_TOOLS[tool_key]
    filepath = os.path.join(TEMP_TOOLS_DIR, info["filename"])
    try:
        with open(filepath, "w", encoding="utf-8") as f: f.write(info["code"])
        return filepath, None
    except Exception as e: return None, f"Không tạo được file: {e}"

def read_process_output(session_id, process):
    try:
        for line in iter(process.stdout.readline, ''):
            if line == '' and process.poll() is not None: break
            if line:
                line = line.rstrip('\n').rstrip('\r')
                with sessions_lock:
                    if session_id in sessions:
                        sessions[session_id]["output_lines"].append(line)
                        if len(sessions[session_id]["output_lines"]) > 5000:
                            sessions[session_id]["output_lines"] = sessions[session_id]["output_lines"][-5000:]
                socketio.emit('output', {'session_id': session_id, 'line': line, 'ts': datetime.now().strftime('%H:%M:%S')}, room=session_id)
    except Exception: pass
    finally:
        try:
            process.wait(); rc = process.returncode
        except Exception: rc = -1
        with sessions_lock:
            if session_id in sessions: sessions[session_id]["status"] = "stopped" if rc == 0 else f"exited({rc})"
        socketio.emit('status', {'session_id': session_id, 'status': 'stopped', 'return_code': rc, 'message': f'Tool kết thúc (code {rc})'}, room=session_id)

def start_tool_process(session_id, tool_key):
    filepath, err = ensure_tool_file(tool_key)
    if err: return None, err
    if not filepath or not os.path.exists(filepath): return None, f"Không tìm thấy file: {filepath}"
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'; env['PYTHONUNBUFFERED'] = '1'; env['TERM'] = 'xterm-256color'
    process = subprocess.Popen(
        [sys.executable, '-u', filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=TEMP_TOOLS_DIR, env=env, bufsize=1, universal_newlines=True, encoding='utf-8', errors='replace'
    )
    return process, None

@app.route('/')
def index():
    return render_template('index.html', tools=TOOL_INFO)

@app.route('/api/tools')
def api_tools(): return jsonify(TOOL_INFO)

@app.route('/api/sessions')
def api_sessions():
    with sessions_lock:
        return jsonify([{"session_id": k, "tool": v["tool"], "status": v["status"], "started_at": v["started_at"], "output_count": len(v["output_lines"])} for k, v in sessions.items()])

@app.route('/api/start/<tool_key>', methods=['POST'])
def api_start(tool_key):
    if tool_key not in EMBEDDED_TOOLS: return jsonify({"ok": False, "error": "Tool không hợp lệ"}), 400
    session_id = str(uuid.uuid4())[:8]
    process, err = start_tool_process(session_id, tool_key)
    if err: return jsonify({"ok": False, "error": err}), 500
    with sessions_lock:
        sessions[session_id] = {"tool": tool_key, "process": process, "output_lines": [], "status": "running", "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    threading.Thread(target=read_process_output, args=(session_id, process), daemon=True).start()
    return jsonify({"ok": True, "session_id": session_id})

@app.route('/api/stop/<session_id>', methods=['POST'])
def api_stop(session_id):
    with sessions_lock: s = sessions.get(session_id)
    if not s: return jsonify({"ok": False, "error": "Session không tồn tại"}), 404
    try:
        proc = s["process"]
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill()
        with sessions_lock: sessions[session_id]["status"] = "stopped"
        socketio.emit('status', {'session_id': session_id, 'status': 'stopped', 'message': 'Đã dừng'}, room=session_id)
        return jsonify({"ok": True})
    except Exception as e: return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/input/<session_id>', methods=['POST'])
def api_input(session_id):
    data = request.get_json() or {}
    text = data.get("text", "")
    with sessions_lock: s = sessions.get(session_id)
    if not s: return jsonify({"ok": False, "error": "Session không tồn tại"}), 404
    try:
        proc = s["process"]
        if proc.poll() is not None: return jsonify({"ok": False, "error": "Process đã kết thúc"}), 400
        proc.stdin.write(text + "\n"); proc.stdin.flush()
        return jsonify({"ok": True})
    except Exception as e: return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/clear/<session_id>', methods=['POST'])
def api_clear(session_id):
    with sessions_lock:
        if session_id in sessions: sessions[session_id]["output_lines"] = []
    socketio.emit('cleared', {'session_id': session_id}, room=session_id)
    return jsonify({"ok": True})

@app.route('/api/save/<session_id>', methods=['POST'])
def api_save(session_id):
    with sessions_lock: s = sessions.get(session_id)
    if not s: return jsonify({"ok": False, "error": "Session không tồn tại"}), 404
    filename = f"{s['tool']}_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    filepath = os.path.join(SESSIONS_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Tool: {s['tool']}\n# Started: {s['started_at']}\n# Session: {session_id}\n")
            f.write("=" * 60 + "\n")
            f.write("\n".join(s["output_lines"]))
        return jsonify({"ok": True, "filename": filename})
    except Exception as e: return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/test-proxy', methods=['POST'])
def api_test_proxy():
    data = request.get_json() or {}
    p = data.get("proxy", "").strip()
    if not p: return jsonify({"ok": False, "error": "Proxy trống"})
    if "://" not in p: p = "http://" + p
    try:
        r = requests.get("https://api.ipify.org?format=json", proxies={"http": p, "https": p}, timeout=15)
        if r.status_code == 200: return jsonify({"ok": True, "ip": r.json().get("ip", "")})
    except Exception as e: return jsonify({"ok": False, "error": str(e)})
    return jsonify({"ok": False, "error": "Proxy die/timeout"})

@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id); emit('joined', {'session_id': session_id})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print(" 🚀 TA TOOL WEB - 3 TOOL IG (WARMUP) + 2 TOOL FB")
    print(f" 📁 Temp tools: {TEMP_TOOLS_DIR}")
    print(f" 🌐 Port: {port}")
    print(f" 📦 Tools: {list(EMBEDDED_TOOLS.keys())}")
    print(f" 📘 FB: Reg Page (multi-thread), Chuyển Page")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
