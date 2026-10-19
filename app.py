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

# ================== BIẾN TOÀN CỤC ==================
sessions = {}
sessions_lock = threading.Lock()

# LƯU TRỮ THỐNG KÊ THEO TỪNG NICK
NICK_STATS = {}
STATS_LOCK = threading.Lock()

FB_REG_STATE = {
    "running": False,
    "results": [],
    "total_success": 0,
    "total_fail": 0,
    "start_time": 0
}
FB_REG_LOCK = threading.Lock()

IG_LOGIN_STATE = {
    "running": False,
    "total_success": 0,
    "total_fail": 0
}
IG_LOGIN_LOCK = threading.Lock()

# ============================================================================
# ==================== TOOL 1: xsmmv3.2.py ==================================
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
        pts = ck.get('points', 0)
        if 'message' in ck:
            thread_safe_print(f"[{now}] [{tenfb}] {ck['message']} (+{pts} xu)")
            if pts > 0: thread_safe_print(f"[[XU_UPDATE]]|{tenfb}|{pts}|{len(task_list)}")
        elif ck.get("is_timeout"): thread_safe_print(f"[{now}] [{tenfb}] {ck['message']}")
        elif 'error' in ck: thread_safe_print(f"[{now}] [{tenfb}] LỖI: {ck['error']}")
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
    try:
        acc_list = xsmm_thread.get_accounts(account_type="instagram", search=idfb)
        exists = False
        if isinstance(acc_list, dict) and acc_list.get("accounts"):
            for acc in acc_list["accounts"]:
                if acc and (str(acc.get("account_id")) == str(idfb) or str(acc.get("name", "")).lower() == str(tenfb).lower()):
                    exists = True; break
        if not exists: xsmm_thread.add_account("instagram", f"https://www.instagram.com/{tenfb}")
    except: pass
    max_job = 0; cache = []
    while True:
        job = random.choice(listnv)
        if job == 'instagram_like':
            lv = xsmm_thread.get_tasks(job, uid=idfb)
            if isinstance(lv, list) and len(lv) > 0:
                solo = 0
                for nv in lv:
                    csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
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
                    csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
                    thread_safe_print(f"{yellow}[Follow] {tid}{reset}")
                    chay = follow(tid, cookie, csf, lj, proxy=proxy)
                    max_job += 1
                    try:
                        g = json.loads(chay)
                        if 'data' not in g and g.get('status') not in ('ok', 'success'): solo += 1
                        else:
                            cache.append(nv.get('id')); solo = 0
                            thread_safe_print(f"{green}[+] Follow OK ({len(cache)}/8){reset}")
                            if len(cache) == 8:
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
                    csf_m = re.search(r'csrftoken=([^;]+)', cookie); csf = csf_m.group(1) if csf_m else ""
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
    print(f"{cyan}===== XSMM TOOL V3.2 ====={reset}")
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
# ==================== TOOL 2: xsmmigv5.2.py ================================
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
from concurrent.futures import ThreadPoolExecutor
import threading

red = "\033[1;31m"; green = "\033[1;32m"; yellow = "\033[1;33m"
cyan = "\033[1;36m"; white = "\033[0;37m"; reset = "\033[0m"

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

def gui_nhan_xu(job_type, task_list, uid, cookie_check, xsmm, tenfb):
    if not task_list: return
    thread_safe_print(f"[{tenfb}] Gom {len(task_list)} task -> Gửi duyệt...")
    ck = xsmm.complete_tasks(job_type, task_list, uid=uid, cookie_check=cookie_check)
    now = datetime.now().strftime("%H:%M:%S")
    if isinstance(ck, dict):
        pts = ck.get('points', 0)
        if 'message' in ck:
            thread_safe_print(f"[{now}] [{tenfb}] {ck['message']} (+{pts} xu)")
            if pts > 0: thread_safe_print(f"[[XU_UPDATE]]|{tenfb}|{pts}|{len(task_list)}")
        elif ck.get("is_timeout"): thread_safe_print(f"[{now}] [{tenfb}] {ck['message']}")
        elif 'error' in ck: thread_safe_print(f"[{now}] [{tenfb}] LỖI: {ck['error']}")
        if ck.get('countdown', 0) > 0: time.sleep(ck['countdown'])

def run_account_v52(ad, listnv, dly, xsmm_token, doi, ck_global):
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
        thread_safe_print(f"{red}[!] Cookie die{reset}"); return
    thread_safe_print(f"{green}[+] NICK [{tenfb} | {idfb}]{reset}")

    try:
        al = XSMMTool(token=xsmm_token).get_accounts(account_type="instagram", search=idfb)
        if not (isinstance(al, dict) and al.get("accounts") and any(str(a.get("account_id")) == str(idfb) for a in al["accounts"])):
            XSMMTool(token=xsmm_token).add_account("instagram", f"https://www.instagram.com/{tenfb}")
    except Exception: pass

    xsmm = XSMMTool(token=xsmm_token)
    max_j = 0; cache = []
    while max_j < doi:
        jt = random.choice(listnv)
        jl = random.randint(3, 5); jdt = 0
        if jt == 'instagram_like':
            lv = xsmm.get_tasks(jt, uid=idfb)
            if isinstance(lv, list) and lv:
                solo = 0
                for nv in lv:
                    csf_m = re.search(r'csrftoken=([^;]+)', c); csf = csf_m.group(1) if csf_m else ""
                    thread_safe_print(f"{yellow}[{tenfb}] [Tym] {nv.get('target_url', '')[:30]}...{reset}")
                    r = tym(nv.get('target_id', ''), c, csf, nv.get('target_url', ''), proxy=p, profile=prof)
                    max_j += 1; jdt += 1
                    ok, err = parse_resp(r)
                    if ok:
                        gui_nhan_xu("instagram_like", [nv.get('id')], idfb, target_ck, xsmm, tenfb); solo = 0
                    else: solo += 1
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
                    r = follow(tid, c, csf, lj, proxy=p, profile=prof)
                    max_j += 1; jdt += 1
                    ok, _ = parse_resp(r)
                    if ok: 
                        solo = 0
                        cache.append(nv.get('id'))
                        thread_safe_print(f"{green}[+] [{tenfb}] Follow OK -> Đã gom ({len(cache)}/8){reset}")
                        if len(cache) >= 8:
                            gui_nhan_xu("instagram_follow", cache, idfb, target_ck, xsmm, tenfb)
                            cache = []
                    else: solo += 1
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
                    r = cmt(idm, nd, c, csf, lj, proxy=p, profile=prof)
                    max_j += 1; jdt += 1
                    ok, err = parse_resp(r)
                    if ok:
                        gui_nhan_xu("instagram_comment", [nv.get('id')], idfb, target_ck, xsmm, tenfb); solo = 0
                    else: solo += 1
                    time.sleep(random.randint(*dly['cmt']) + random.uniform(0, 5))
                    if solo > 4 or jdt >= jl or max_j >= doi: break
        time.sleep(15)

def main():
    print(f"{cyan}===== XSMM IG V5.2 ====={reset}")
    sys.stdout.write("Số luồng (1-50): "); sys.stdout.flush()
    try:
        max_threads = int(input().strip())
        if max_threads < 1: max_threads = 1
        if max_threads > 50: max_threads = 50
    except: max_threads = 10

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

    print(f"{cyan}[*] Chạy {len(mangcookie)} nick | {max_threads} luồng{reset}\n")
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(run_account_v52, ad, listnv, dly, token, doi, ck_global) for ad in mangcookie]
        for f in futures: f.result()

if __name__ == "__main__":
    main()
'''

# ============================================================================
# ==================== TOOL 3: 11223.py =====================================
# ============================================================================
TOOL_CODE_11223 = r'''import sys
print("Tool 11223 đang bảo trì...")
'''

EMBEDDED_TOOLS = {
    "xsmmv3.2": {"name": "XSMM Tool V3.2", "color": "#00d4ff", "filename": "xsmmv3.2.py", "code": TOOL_CODE_XSMMV32},
    "xsmmigv5.2": {"name": "XSMM IG V5.2", "color": "#ff6b9d", "filename": "xsmmigv5.2.py", "code": TOOL_CODE_XSMMIGV52},
    "11223": {"name": "Simple IG Bot", "color": "#ffd93d", "filename": "11223.py", "code": TOOL_CODE_11223},
}
TOOL_INFO = {k: {"name": v["name"], "color": v["color"]} for k, v in EMBEDDED_TOOLS.items()}

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

def fb_invite_admin(cookie, page_id, target_uid, proxies):
    fb_dtsg, jazoest = fb_get_dtsg(cookie, proxies)
    if not fb_dtsg: return False
    actor_m = re.search(r'c_user=(\d+)', cookie); actor_id = actor_m.group(1) if actor_m else ""
    headers = {'cookie': cookie, 'user-agent': 'Mozilla/5.0', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.facebook.com'}
    payload = {'fb_dtsg': fb_dtsg, 'jazoest': jazoest, 'variables': json.dumps({"input": {"actor_id": actor_id, "profile_id": page_id, "target_user_id": target_uid, "task_ids": [1, 2, 3, 4, 5]}}), 'doc_id': '5278783472212933'}
    try:
        r = requests.post("https://www.facebook.com/api/graphql/", headers=headers, data=payload, proxies=proxies, timeout=20)
        return 'errors' not in r.json()
    except: return False

def fb_reg_worker(idx, cookie, page_name, cat, proxy, avt, cover, target_uid, result_list):
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
        if target_uid: fb_invite_admin(cookie, res["page_id"], target_uid, proxies)
        
        res["status"] = "OK + QTV"; res["ok"] = True
        result_list.append(res)
    except Exception as e:
        res["status"] = "Lỗi"; result_list.append(res)

def run_fb_reg(tasks, threads):
    FB_REG_STATE["running"] = True; FB_REG_STATE["total_success"] = 0; FB_REG_STATE["total_fail"] = 0
    q = Queue(); [q.put((i+1, t['cookie'], t['page_name'], '2200', t.get('proxy',''), t.get('avatar',''), t.get('cover',''), t.get('target_uid',''))) for i, t in enumerate(tasks)]
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
# ==================== IG LOGIN (TK|MK|2FA) =================================
# ============================================================================
def ig_login_worker(idx, acc_str, proxy, rl):
    res = {"idx": idx, "acc": "", "status": "Đang xử lý...", "ok": False, "cookie": ""}
    try:
        parts = acc_str.strip().split('|')
        user, pwd = parts[0], parts[1]
        twofa = parts[2] if len(parts) > 2 else ""
        res["acc"] = user
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        session = c_requests.Session(impersonate="chrome120")
        if proxies: session.proxies = proxies
        
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'x-ig-app-id': '936619743392459', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.instagram.com', 'referer': 'https://www.instagram.com/'}
        
        session.get("https://www.instagram.com/", headers=headers)
        csrf = session.cookies.get('csrftoken', '')
        headers['x-csrftoken'] = csrf
        
        payload = {'username': user, 'enc_password': f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{pwd}", 'queryParams': '{}', 'optIntoOneTap': 'false'}
        r = session.post("https://www.instagram.com/api/v1/web/accounts/login/ajax/", headers=headers, data=payload)
        rj = r.json()
        
        if rj.get("authenticated"):
            res["ok"] = True; res["status"] = "OK"
        elif rj.get("two_factor_required"):
            res["status"] = "2FA..."
            two_fa_id = rj.get("two_factor_info", {}).get("two_factor_identifier")
            r2 = session.post("https://www.instagram.com/api/v1/web/accounts/login/ajax/two_factor/", headers=headers, data={'username': user, 'verificationCode': twofa, 'two_factor_identifier': two_fa_id, 'trust_this_device': '0'})
            if r2.json().get("authenticated"):
                res["ok"] = True; res["status"] = "OK (2FA)"
            else: res["status"] = "Sai 2FA"
        else: res["status"] = "Die/Sai MK"
        
        if res["ok"]:
            cookies = session.cookies.get_dict()
            res["cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items() if k in ['csrftoken', 'sessionid', 'ds_user_id', 'mid']])
        rl.append(res)
    except Exception as e:
        res["status"] = "Lỗi"; rl.append(res)

def run_ig_login(tasks, threads):
    IG_LOGIN_STATE["running"] = True; IG_LOGIN_STATE["total_success"] = 0; IG_LOGIN_STATE["total_fail"] = 0
    q = Queue(); [q.put((i+1, t['acc'], t.get('proxy',''))) for i, t in enumerate(tasks)]
    def worker():
        while True:
            try: task = q.get_nowait()
            except: break
            try:
                rl = []
                ig_login_worker(*task, rl)
                if rl:
                    res = rl[0]
                    with IG_LOGIN_LOCK:
                        if res["ok"]: IG_LOGIN_STATE["total_success"] += 1
                        else: IG_LOGIN_STATE["total_fail"] += 1
                        socketio.emit('ig_login_update', {"result": res})
            except: pass
            finally: q.task_done()
    ts = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    for t in ts: t.start()
    for t in ts: t.join()
    IG_LOGIN_STATE["running"] = False
    socketio.emit('ig_login_done', {"success": IG_LOGIN_STATE["total_success"], "fail": IG_LOGIN_STATE["total_fail"]})

@app.route('/api/ig_login_start', methods=['POST'])
def api_ig_login_start():
    data = request.json or {}
    if not data.get('tasks'): return jsonify({"ok": False})
    threading.Thread(target=run_ig_login, args=(data['tasks'], int(data.get('threads', 5))), daemon=True).start()
    return jsonify({"ok": True})

# ============================================================================
# ==================== ROUTES CƠ BẢN & XỬ LÝ STATS ==========================
# ============================================================================
def ensure_tool_file(k):
    f = os.path.join(TEMP_TOOLS_DIR, EMBEDDED_TOOLS[k]["filename"])
    with open(f, "w", encoding="utf-8") as fw: fw.write(EMBEDDED_TOOLS[k]["code"])
    return f

def update_nick_stats(sid, nick, is_job=False, xu_amount=0, status="Đang chạy"):
    global NICK_STATS
    with STATS_LOCK:
        if nick not in NICK_STATS:
            NICK_STATS[nick] = {"jobs": 0, "xu": 0, "status": status}
        
        if is_job:
            NICK_STATS[nick]["jobs"] += 1
            
        if xu_amount > 0:
            NICK_STATS[nick]["xu"] += xu_amount
            
        NICK_STATS[nick]["status"] = status
        socketio.emit('table_update', NICK_STATS, room=sid)

def read_process_output(sid, process):
    current_nick = "Chưa xác định"
    try:
        for line in iter(process.stdout.readline, ''):
            if line == '' and process.poll() is not None: break
            if line:
                line_str = line.rstrip()
                
                # Gửi log thô
                socketio.emit('output', {'session_id': sid, 'line': line_str, 'ts': datetime.now().strftime('%H:%M:%S')}, room=sid)
                
                # BẮT LOG TÊN NICK ĐỂ HIỂN THỊ LÊN BẢNG
                match_nick = re.search(r'NICK(?:\s+LIVE)?\s*\[([^|\]]+)', line_str)
                if match_nick:
                    current_nick = match_nick.group(1).strip()
                    update_nick_stats(sid, current_nick, is_job=False, status="Đang chạy")

                # BẮT LOG XU & JOB THEO ĐỊNH DẠNG RIÊNG CỦA TOOL
                match_xu_custom = re.search(r'\[\[XU_UPDATE\]\]\|(.*?)\|(\d+)\|(\d+)', line_str)
                if match_xu_custom:
                    nick_in_log = match_xu_custom.group(1).strip()
                    xu_nhan = int(match_xu_custom.group(2))
                    jobs_done = int(match_xu_custom.group(3))
                    update_nick_stats(sid, nick_in_log, is_job=True, xu_amount=xu_nhan)
                
                # 2. Đề phòng tool in chuỗi text thông thường: "Thành công (+51 xu, 3/3 job)"
                elif "Thành công" in line_str and "xu" in line_str:
                    match_xu_text = re.search(r'\[(.*?)\].*?\(\+(\d+)\s*xu', line_str)
                    if match_xu_text:
                        nick_in_log = match_xu_text.group(1).strip()
                        xu_nhan = int(match_xu_text.group(2))
                        update_nick_stats(sid, nick_in_log, is_job=True, xu_amount=xu_nhan)
                    else:
                        update_nick_stats(sid, current_nick, is_job=True)

    except Exception as e:
        print(f"Lỗi đọc log: {e}")
    finally:
        process.wait()
        with STATS_LOCK:
            for n in NICK_STATS:
                NICK_STATS[n]["status"] = "Đã dừng"
            socketio.emit('table_update', NICK_STATS, room=sid)
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
