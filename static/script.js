const socket = io();
const state = {};

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }
function now() { return new Date().toLocaleTimeString('vi-VN', { hour12: false }); }
function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function classifyLine(line) {
    if (/\b(traceback|exception|error|lỗi|die|fail|thất bại)\b/i.test(line)) return 'err';
    if (/\b(warn|cảnh báo|retry|timeout)\b/i.test(line)) return 'warn';
    if (/\b(success|thành công|✔|✅|ok|done)\b/i.test(line)) return 'ok';
    if (/\b(info|đang|bắt đầu|nick|job)\b/i.test(line)) return 'info';
    return '';
}
function appendLine(el, line, ts = null) {
    if (!el) return;
    const d = document.createElement('div');
    d.className = 'term-line ' + classifyLine(line);
    d.innerHTML = `<span class="ts">[${ts||now()}]</span>${escapeHtml(line)}`;
    el.appendChild(d); el.scrollTop = el.scrollHeight;
}

$$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const t = btn.dataset.tool;
        $$('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
        $$('.tool-panel').forEach(p => p.classList.toggle('active', p.dataset.tool === t));
    });
});

function getPanel(t) { return $(`.tool-panel[data-tool="${t}"]`); }
function getTerm(t) { const p = getPanel(t); return p ? p.querySelector('.terminal') : null; }
function getStatusBadge(t) { return $(`.session-info[data-tool="${t}"] .status-badge`); }
function getSessionIdEl(t) { return $(`.session-info[data-tool="${t}"] .session-id`); }
function getOutputCount(t) { return $(`.session-info[data-tool="${t}"] .output-count`); }
function getBtn(t, c) { return $(`.btn-${c}[data-tool="${t}"]`); }
function getCfg(t, c) { const p = getPanel(t); return p ? p.querySelector('.' + c) : null; }

function setStatus(t, s, sid = null) {
    const b = getStatusBadge(t); if (!b) return;
    b.className = 'status-badge ' + (s === 'running' ? 'running' : s === 'stopped' ? 'stopped' : 'idle');
    b.textContent = s === 'running' ? '● RUNNING' : s === 'stopped' ? '● STOPPED' : '● IDLE';
    if (sid !== null) getSessionIdEl(t).textContent = sid ? `Session: ${sid}` : '';
    const run = s === 'running';
    getBtn(t, 'start').disabled = run;
    getBtn(t, 'stop').disabled = !run;
    const stdin = $(`.stdin-input[data-tool="${t}"]`); if (stdin) stdin.disabled = !run;
    const send = $(`.btn-send[data-tool="${t}"]`); if (send) send.disabled = !run;
    const form = $(`#form-${t.replace('.','_')}`);
    if (form) form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = run);
}

function buildInputSequence(t) {
    const token = (getCfg(t, 'cfg-token')?.value || '').trim();
    const ckRaw = (getCfg(t, 'cfg-cookies')?.value || '').trim();
    const ckCk = (getCfg(t, 'cfg-cookiecheck')?.value || '').trim();
    const dTym = getCfg(t, 'cfg-delay-tym')?.value || '10';
    const dFol = getCfg(t, 'cfg-delay-follow')?.value || '15';
    const dCmt = getCfg(t, 'cfg-delay-comment')?.value || '20';
    const thr = getCfg(t, 'cfg-threads')?.value || '10';
    const rot = getCfg(t, 'cfg-rotate')?.value || '99999';
    const wait = getCfg(t, 'cfg-wait')?.value || '150';
    const jL = getCfg(t, 'cfg-job-like')?.checked;
    const jF = getCfg(t, 'cfg-job-follow')?.checked;
    const jC = getCfg(t, 'cfg-job-comment')?.checked;

    const lines = ckRaw.split('\n').map(s => s.trim()).filter(Boolean);
    const cookies = [], proxies = [];
    for (const l of lines) { const p = l.split('|'); cookies.push(p[0].trim()); proxies.push(p[1] ? p[1].trim() : ''); }

    const seq = [];
    if (t === 'xsmmv3.2') {
        seq.push(thr, token, String(cookies.length));
        for (let i = 0; i < cookies.length; i++) seq.push(cookies[i], proxies[i] || '');
        seq.push(cookies.length === 1 ? wait : rot);
        seq.push(jL ? 'on' : 'off'); if (jL) seq.push(dTym);
        seq.push(jF ? 'on' : 'off'); if (jF) seq.push(dFol);
        seq.push(jC ? 'on' : 'off'); if (jC) seq.push(dCmt);
    } else if (t === 'xsmmigv5.2') {
        seq.push(thr, token);
        if (ckCk) { seq.push('1', ckCk); } else seq.push('0');
        seq.push(String(cookies.length));
        for (let i = 0; i < cookies.length; i++) seq.push(cookies[i], proxies[i] || '');
        seq.push(rot);
        seq.push(jL ? 'on' : 'off'); if (jL) seq.push(dTym);
        seq.push(jF ? 'on' : 'off'); if (jF) seq.push(dFol);
        seq.push(jC ? 'on' : 'off'); if (jC) seq.push(dCmt);
    } else if (t === '11223') {
        seq.push(token, cookies[0] || '', '1', dTym, String(parseInt(dTym)+5), '3', '5');
    }
    return seq.filter(x => x !== undefined && x !== null);
}

$$('.btn-start[data-tool]').forEach(btn => {
    if (btn.id === 'btn_fb_reg' || btn.id === 'btn_ig_login') return;
    btn.addEventListener('click', async () => {
        const t = btn.dataset.tool;
        if (!['xsmmv3.2','xsmmigv5.2','11223'].includes(t)) return;
        const token = (getCfg(t, 'cfg-token')?.value || '').trim();
        const ck = (getCfg(t, 'cfg-cookies')?.value || '').trim();
        if (!token) { alert('Nhập Token XSMM!'); return; }
        if (!ck) { alert('Nhập Cookie!'); return; }
        btn.disabled = true;
        try {
            const res = await fetch(`/api/start/${t}`, { method: 'POST' });
            const d = await res.json();
            if (!d.ok) { alert('Lỗi: ' + (d.error || '')); btn.disabled = false; return; }
            state[t] = { sessionId: d.session_id, status: 'running' };
            setStatus(t, 'running', d.session_id);
            socket.emit('join', { session_id: d.session_id });
            const term = getTerm(t); if (term) { term.innerHTML = ''; appendLine(term, `▶ Bắt đầu [${t}] — Session: ${d.session_id}`); }
            
            const safeT = t.replace(/\./g, '\\.');
            const tbody = document.querySelector(`.stats-table-body-${safeT}`);
            if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #888;">Đang chờ dữ liệu...</td></tr>';

            await new Promise(r => setTimeout(r, 3000));
            const seq = buildInputSequence(t);
            for (let i = 0; i < seq.length; i++) {
                await new Promise(r => setTimeout(r, 300));
                await fetch(`/api/input/${d.session_id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: seq[i] }) });
                if (term) { appendLine(term, `> [auto] ${seq[i]}`, now()); }
            }
            $(`.tab-btn[data-tool="${t}"]`).click();
        } catch (e) { alert('Lỗi: ' + e.message); btn.disabled = false; }
    });
});

$$('.btn-stop').forEach(btn => {
    btn.addEventListener('click', async () => {
        const t = btn.dataset.tool; const s = state[t]; if (!s) return;
        if (!confirm('Dừng tool?')) return;
        await fetch(`/api/stop/${s.sessionId}`, { method: 'POST' });
        setStatus(t, 'stopped');
    });
});

// Bắt sự kiện nút Reset Bảng Thống Kê
document.querySelectorAll('.btn-reset-stats').forEach(btn => {
    btn.addEventListener('click', async () => {
        if (!confirm('Bạn có chắc muốn xóa toàn bộ dữ liệu thống kê (Job/Xu) trên bảng?')) return;
        try {
            const res = await fetch('/api/reset_stats', { method: 'POST' });
            if ((await res.json()).ok) {
                console.log('Đã reset bảng thống kê');
            }
        } catch (e) { alert('Lỗi khi reset: ' + e.message); }
    });
});

function sendStdin(t) {
    const inp = $(`.stdin-input[data-tool="${t}"]`); if (!inp) return;
    const s = state[t]; if (!s || !s.sessionId) return;
    fetch(`/api/input/${s.sessionId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: inp.value }) });
    const term = getTerm(t); if (term) appendLine(term, `> ${inp.value}`, now());
    inp.value = '';
}
$$('.btn-send').forEach(btn => btn.addEventListener('click', () => sendStdin(btn.dataset.tool)));
$$('.stdin-input').forEach(inp => inp.addEventListener('keydown', e => { if (e.key === 'Enter') sendStdin(inp.dataset.tool); }));

// ================== IG LOGIN ==================
document.getElementById('btn_ig_login')?.addEventListener('click', async () => {
    const tasksRaw = document.getElementById('ig_login_tasks').value.trim();
    const threads = document.getElementById('ig_login_threads').value;
    if (!tasksRaw) return alert('Nhập danh sách TK!');
    
    const lines = tasksRaw.split('\n').map(l => l.trim()).filter(Boolean);
    const tasks = lines.map(l => {
        const p = l.split('|');
        return { acc: l, proxy: p[3] || '' };
    });
    
    document.getElementById('ig_login_tbody').innerHTML = '';
    const res = await fetch('/api/ig_login_start', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({tasks, threads}) });
});

socket.on('ig_login_update', d => {
    const tbody = document.getElementById('ig_login_tbody');
    if (!tbody || !d.result) return;
    if (tbody.querySelector('tr td[colspan]')) tbody.innerHTML = '';
    const r = d.result;
    const color = r.ok ? '#22c55e' : '#ef4444';
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.idx}</td><td>${r.acc.split('|')[0]}</td><td style="color:${color}">${r.status}</td><td style="font-size:10px;max-width:100px;overflow:hidden;white-space:nowrap">${r.cookie}</td>`;
    tbody.appendChild(tr);
    tbody.scrollTop = tbody.scrollHeight;
});

// ================== FB REG PAGE ==================
document.getElementById('btn_fb_reg')?.addEventListener('click', async () => {
    const tasksRaw = document.getElementById('fb_reg_tasks').value.trim();
    const namesRaw = document.getElementById('fb_reg_names').value.trim();
    const avatarsRaw = document.getElementById('fb_reg_avatars').value.trim();
    const coversRaw = document.getElementById('fb_reg_covers').value.trim();
    const uidNhan = document.getElementById('fb_reg_uid').value.trim();
    const threads = document.getElementById('fb_reg_threads').value;
    
    if (!tasksRaw || !namesRaw) return alert('Nhập Cookie và Tên Page!');
    const taskLines = tasksRaw.split('\n').map(s => s.trim()).filter(Boolean);
    const nameLines = namesRaw.split('\n').map(s => s.trim()).filter(Boolean);
    const avatarLines = avatarsRaw ? avatarsRaw.split('\n').map(s => s.trim()).filter(Boolean) : [];
    const coverLines = coversRaw ? coversRaw.split('\n').map(s => s.trim()).filter(Boolean) : [];
    
    const tasks = [];
    for (let i = 0; i < taskLines.length; i++) {
        const parts = taskLines[i].split('|');
        tasks.push({
            cookie: parts[0].trim(), proxy: parts[1]?.trim() || '', page_name: nameLines[i % nameLines.length],
            avatar: avatarLines[i % avatarLines.length] || '', cover: coverLines[i % coverLines.length] || '', target_uid: uidNhan
        });
    }
    
    document.getElementById('fb_reg_tbody').innerHTML = '';
    const res = await fetch('/api/fb_reg_start', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({tasks, threads}) });
    if ((await res.json()).ok) { alert('Bắt đầu reg page + chuyển QTV!'); }
});

socket.on('fb_reg_update', d => {
    const tbody = document.getElementById('fb_reg_tbody');
    if (!tbody || !d.result) return;
    if (tbody.querySelector('tr td[colspan]')) tbody.innerHTML = '';
    const r = d.result;
    const color = r.ok ? 'status-ok' : 'status-fail';
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.idx}</td><td>${r.uid}</td><td>${r.page_id}</td><td>${r.page_name}</td><td class="${color}">${r.status}</td>`;
    tbody.appendChild(tr);
    tbody.scrollTop = tbody.scrollHeight;
    if(d.stats){ document.getElementById('fb_stat_ok').innerText=d.stats.success; document.getElementById('fb_stat_err').innerText=d.stats.fail; }
});

socket.on('fb_reg_done', d => {
    alert(`Hoàn tất FB! OK: ${d.success}, Lỗi: ${d.fail}`);
});

// ================== SOCKET CHUNG & BẢNG THỐNG KÊ ==================
socket.on('output', d => {
    const { session_id, line, ts } = d;
    const t = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!t) return;
    const term = getTerm(t); if (!term) return;
    
    let isFollowGom = line.includes('Đã gom (') && line.includes('/8)');
    let isXuUpdate = line.includes('[[XU_UPDATE]]');
    
    if (isXuUpdate) return; 

    const div = document.createElement('div');
    if (isFollowGom) {
        div.style.color = '#22c55e';
        div.style.fontWeight = 'bold';
        div.style.textShadow = '0 0 8px #22c55e';
    } else {
        div.className = 'term-line ' + classifyLine(line);
    }
    div.innerHTML = `<span class="ts">[${ts||now()}]</span>${escapeHtml(line)}`;
    term.appendChild(div);
    term.scrollTop = term.scrollHeight;

    const cnt = getOutputCount(t); if (cnt) cnt.textContent = term.children.length + ' dòng';
});

socket.on('table_update', function(nickStats) {
    const tbody = document.querySelector('.tool-panel.active .stats-table-wrap tbody');
    if (!tbody) return;
    
    tbody.innerHTML = ''; 
    let stt = 1;
    let hasData = false;

    for (const [nickname, data] of Object.entries(nickStats)) {
        hasData = true;
        let statusColor = data.status === "Đang chạy" ? "#00ff00" : "#ff4444";
        
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid #333';
        tr.innerHTML = `
            <td style="padding: 10px;">${stt}</td>
            <td style="padding: 10px; font-weight: bold; color: #00d4ff;">${nickname}</td>
            <td style="padding: 10px;">${data.jobs} job</td>
            <td style="padding: 10px; color: #ffd93d; font-weight: bold;">+${data.xu} xu</td>
            <td style="padding: 10px; color: ${statusColor};">${data.status}</td>
        `;
        tbody.appendChild(tr);
        stt++;
    }

    if (!hasData) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #888;">Chưa có dữ liệu...</td></tr>';
    }
});

socket.on('status', d => {
    const { session_id, status, message, return_code } = d;
    const t = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!t) return;
    if (status === 'stopped') {
        state[t].status = 'stopped';
        setStatus(t, 'stopped');
        const term = getTerm(t);
        if (term) appendLine(term, `■ ${message || 'Đã dừng'} (exit: ${return_code ?? '?'})`);
    }
});

// Lưu config tự động
const CFG_FIELDS = ['cfg-token', 'cfg-cookies', 'cfg-cookiecheck', 'cfg-delay-tym', 'cfg-delay-follow', 'cfg-delay-comment', 'cfg-threads', 'cfg-rotate', 'cfg-wait', 'cfg-delaycoin'];
CFG_FIELDS.forEach(cls => {
    $$('.' + cls).forEach(inp => {
        const t = inp.closest('.tool-panel')?.dataset.tool; if (!t) return;
        const key = `ta_cfg_${t}_${cls}`;
        const saved = localStorage.getItem(key);
        if (saved !== null && inp.type !== 'checkbox') inp.value = saved;
        inp.addEventListener('input', () => localStorage.setItem(key, inp.value));
    });
});
