const socket = io();
const state = {};

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }
function now() { return new Date().toLocaleTimeString('vi-VN', { hour12: false }); }
function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// ================== HIỆU ỨNG TRONG PANEL ==================
function createEffectForPanel(canvas) {
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    let W = 0, H = 0, ACTIVE = false;

    function resize() {
        const rect = canvas.getBoundingClientRect();
        W = canvas.width = Math.max(1, rect.width);
        H = canvas.height = Math.max(1, rect.height);
    }
    new ResizeObserver(resize).observe(canvas);
    setTimeout(resize, 100);

    let ACCENT = '#ec4899';
    function getAccent() {
        const panel = canvas.closest('.tool-panel');
        return panel ? getComputedStyle(panel).getPropertyValue('--panel-color').trim() : '#ec4899';
    }

    const flowers = []; const FLOWER_COLORS = ['#ff6b9d', '#ffd93d', '#a78bfa', '#ff8fab', '#f9a8d4'];
    const hearts = []; const bolts = [];

    function newFlower() { return { x: Math.random()*W, y: -20, size: 6+Math.random()*8, speedY: 0.4+Math.random()*0.8, speedX: (Math.random()-0.5)*0.6, rot: Math.random()*Math.PI*2, rotSpeed: (Math.random()-0.5)*0.05, color: FLOWER_COLORS[Math.floor(Math.random()*FLOWER_COLORS.length)], type: Math.random()<0.5?'flower':'petal' }; }
    function newHeart() { return { x: Math.random()*W, y: -20, size: 6+Math.random()*7, speedY: 0.6+Math.random()*1, speedX: (Math.random()-0.5)*0.5, color: ['#ef4444','#ec4899','#f43f5e','#fb7185'][Math.floor(Math.random()*4)], alpha: 0.6+Math.random()*0.4, pulse: Math.random()*Math.PI*2 }; }
    function newBolt() { const sx = Math.random()*W, segs = []; let x = sx, y = 0; const endY = H*(0.4+Math.random()*0.5); while (y < endY) { segs.push({x,y}); x += (Math.random()-0.5)*60; y += 10+Math.random()*20; } return { segments: segs, life: 1, fadeSpeed: 0.03+Math.random()*0.02, width: 1+Math.random()*1.5 }; }
    
    for (let i = 0; i < 8; i++) { const f = newFlower(); f.y = Math.random()*H; flowers.push(f); }
    for (let i = 0; i < 6; i++) { const h = newHeart(); h.y = Math.random()*H; hearts.push(h); }

    function drawLightning(bolt, color) {
        if (bolt.segments.length < 2) return;
        ctx.save(); ctx.globalAlpha = bolt.life; ctx.strokeStyle = color; ctx.lineWidth = bolt.width; ctx.shadowBlur = 15; ctx.shadowColor = color; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(bolt.segments[0].x, bolt.segments[0].y);
        for (let i = 1; i < bolt.segments.length; i++) ctx.lineTo(bolt.segments[i].x, bolt.segments[i].y);
        ctx.stroke(); ctx.restore();
    }
    function drawFlower(f) { ctx.save(); ctx.translate(f.x, f.y); ctx.rotate(f.rot); ctx.globalAlpha = 0.85; ctx.fillStyle = f.color; ctx.shadowBlur = 8; ctx.shadowColor = f.color; if (f.type === 'petal') { ctx.beginPath(); ctx.ellipse(0, 0, f.size, f.size*0.5, 0, 0, Math.PI*2); ctx.fill(); } else { for (let i = 0; i < 5; i++) { ctx.save(); ctx.rotate((Math.PI*2/5)*i); ctx.beginPath(); ctx.ellipse(0, -f.size*0.5, f.size*0.4, f.size*0.7, 0, 0, Math.PI*2); ctx.fill(); ctx.restore(); } ctx.fillStyle = '#ffd93d'; ctx.beginPath(); ctx.arc(0, 0, f.size*0.25, 0, Math.PI*2); ctx.fill(); } ctx.restore(); }
    function drawHeart(h) { ctx.save(); ctx.translate(h.x, h.y); const s = h.size + Math.sin(h.pulse)*1.2; ctx.globalAlpha = h.alpha; ctx.fillStyle = h.color; ctx.shadowBlur = 10; ctx.shadowColor = h.color; ctx.beginPath(); ctx.moveTo(0, s*0.3); ctx.bezierCurveTo(0,0,-s*0.5,0,-s*0.5,s*0.3); ctx.bezierCurveTo(-s*0.5,s*0.7,0,s*1.1,0,s*1.3); ctx.bezierCurveTo(0,s*1.1,s*0.5,s*0.7,s*0.5,s*0.3); ctx.bezierCurveTo(s*0.5,0,0,0,0,s*0.3); ctx.fill(); ctx.restore(); }

    function loop() {
        ctx.clearRect(0, 0, W, H);
        if (ACTIVE && W > 0 && H > 0) {
            ACCENT = getAccent();
            for (const f of flowers) { f.y += f.speedY; f.x += f.speedX; f.rot += f.rotSpeed; if (f.y > H+30) Object.assign(f, newFlower()); drawFlower(f); }
            for (const h of hearts) { h.y += h.speedY; h.x += h.speedX; h.pulse += 0.08; if (h.y > H+30) Object.assign(h, newHeart()); drawHeart(h); }
            for (let i = bolts.length-1; i >= 0; i--) { bolts[i].life -= bolts[i].fadeSpeed; if (bolts[i].life <= 0) { bolts.splice(i,1); continue; } drawLightning(bolts[i], ACCENT); }
            if (Math.random() < 0.02 && bolts.length < 2) bolts.push(newBolt());
        }
        requestAnimationFrame(loop);
    }
    loop();
    return {
        start: () => { ACTIVE = true; canvas.classList.add('active'); resize(); for (let i=0;i<3;i++) setTimeout(()=>bolts.push(newBolt()),i*120); },
        stop: () => { ACTIVE = false; canvas.classList.remove('active'); bolts.length = 0; ctx.clearRect(0,0,W,H); }
    };
}

const fxInstances = {};
$$('.tool-panel').forEach(p => { fxInstances[p.dataset.tool] = { form: createEffectForPanel(p.querySelector('.fx-canvas-form')), term: createEffectForPanel(p.querySelector('.fx-canvas-term')) }; });
function fxStart(t) { const fx = fxInstances[t]; if (fx) { fx.form?.start(); fx.term?.start(); } }
function fxStop(t) { const fx = fxInstances[t]; if (fx) { fx.form?.stop(); fx.term?.stop(); } }

// COLOR PICKER
(function() {
    const picker = document.getElementById('theme-color');
    if (!picker) return;
    const saved = localStorage.getItem('theme_accent');
    if (saved) { document.documentElement.style.setProperty('--accent', saved); picker.value = saved; }
    picker.addEventListener('input', (e) => { document.documentElement.style.setProperty('--accent', e.target.value); localStorage.setItem('theme_accent', e.target.value); });
})();

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

setInterval(() => { const el = $('#clock'); if (el) el.textContent = now(); }, 1000);

$$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const t = btn.dataset.tool;
        $$('.tab-btn').forEach(b => b.classList.toggle('active', b === btn));
        $$('.tool-panel').forEach(p => p.classList.toggle('active', p.dataset.tool === t));
    });
});
$$('.tab-btn')[0]?.click();

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
    const mode = getCfg(t, 'cfg-mode')?.value || '1';
    const dCoin = getCfg(t, 'cfg-delaycoin')?.value || '3';

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
        seq.push(token, cookies[0] || '', mode, dTym, String(parseInt(dTym)+5), dCoin, String(parseInt(dCoin)+2));
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
            fxStart(t);
            const term = getTerm(t); if (term) { term.innerHTML = ''; appendLine(term, `▶ Bắt đầu [${t}] — Session: ${d.session_id}`); }
            
            // Xóa bảng thống kê cũ khi bắt đầu chạy lại
            const tbody = document.querySelector(`.stats-table-body-${t}`);
            if (tbody) tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #888;">Đang chờ dữ liệu...</td></tr>';

            await new Promise(r => setTimeout(r, 3000));
            const seq = buildInputSequence(t);
            for (let i = 0; i < seq.length; i++) {
                await new Promise(r => setTimeout(r, 300));
                await fetch(`/api/input/${d.session_id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: seq[i] }) });
                if (term) { const s = seq[i].length > 70 ? seq[i].substring(0,70)+'...' : seq[i]; appendLine(term, `> [auto] ${s}`, now()); }
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
        setStatus(t, 'stopped'); fxStop(t);
    });
});

$$('.btn-clear').forEach(btn => {
    btn.addEventListener('click', () => {
        const t = btn.dataset.tool;
        const term = getTerm(t); if (term) term.innerHTML = '';
        const cnt = getOutputCount(t); if (cnt) cnt.textContent = '0 dòng';
        const s = state[t]; if (s) fetch(`/api/clear/${s.sessionId}`, { method: 'POST' });
    });
});

$$('.btn-save').forEach(btn => {
    btn.addEventListener('click', async () => {
        const t = btn.dataset.tool; const s = state[t];
        if (!s) { alert('Chưa có session!'); return; }
        const res = await fetch(`/api/save/${s.sessionId}`, { method: 'POST' });
        const d = await res.json();
        if (d.ok) alert('Đã lưu: ' + d.filename); else alert('Lỗi: ' + (d.error || ''));
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
    if ((await res.json()).ok) fxStart('ig_login');
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

// ================== FB REG PAGE NÂNG CAO ==================
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
    if ((await res.json()).ok) { fxStart('fb_regpage'); alert('Bắt đầu reg page + chuyển QTV!'); }
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
    fxStop('fb_regpage');
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
    
    // Ẩn dòng XU_UPDATE khỏi console vì đã có bảng thống kê
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

// LẮNG NGHE SỰ KIỆN CẬP NHẬT BẢNG THỐNG KÊ TỪ BACKEND
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
        fxStop(t);
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
