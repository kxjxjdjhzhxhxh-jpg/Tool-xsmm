const socket = io();
const state = {};

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return [...root.querySelectorAll(sel)]; }
function now() { return new Date().toLocaleTimeString('vi-VN', { hour12: false }); }
function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// ================== HIỆU ỨNG ==================
function createEffectForPanel(canvas) {
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    let W = 0, H = 0, ACTIVE = false;
    function resize() { const r = canvas.getBoundingClientRect(); W = canvas.width = Math.max(1, r.width); H = canvas.height = Math.max(1, r.height); }
    new ResizeObserver(resize).observe(canvas); setTimeout(resize, 100);
    let ACCENT = '#ec4899';
    function getAccent() { const p = canvas.closest('.tool-panel'); return p ? getComputedStyle(p).getPropertyValue('--panel-color').trim() : '#ec4899'; }
    const flowers = []; const FLOWER_COLORS = ['#ff6b9d', '#ffd93d', '#a78bfa', '#ff8fab', '#f9a8d4'];
    const hearts = []; const bolts = [];
    function newFlower() { return { x: Math.random()*W, y: -20, size: 6+Math.random()*8, speedY: 0.4+Math.random()*0.8, speedX: (Math.random()-0.5)*0.6, rot: Math.random()*Math.PI*2, rotSpeed: (Math.random()-0.5)*0.05, color: FLOWER_COLORS[Math.floor(Math.random()*FLOWER_COLORS.length)], type: Math.random()<0.5?'flower':'petal' }; }
    function newHeart() { return { x: Math.random()*W, y: -20, size: 6+Math.random()*7, speedY: 0.6+Math.random()*1, speedX: (Math.random()-0.5)*0.5, color: ['#ef4444','#ec4899','#f43f5e','#fb7185'][Math.floor(Math.random()*4)], alpha: 0.6+Math.random()*0.4, pulse: Math.random()*Math.PI*2 }; }
    function newBolt() { const sx = Math.random()*W, segs = []; let x = sx, y = 0; const endY = H*(0.4+Math.random()*0.5); while (y < endY) { segs.push({x,y}); x += (Math.random()-0.5)*60; y += 10+Math.random()*20; } return { segments: segs, life: 1, fadeSpeed: 0.03+Math.random()*0.02, width: 1+Math.random()*1.5 }; }
    for (let i = 0; i < 8; i++) { const f = newFlower(); f.y = Math.random()*H; flowers.push(f); }
    for (let i = 0; i < 6; i++) { const h = newHeart(); h.y = Math.random()*H; hearts.push(h); }
    function drawLightning(bolt, color) { if (bolt.segments.length < 2) return; ctx.save(); ctx.globalAlpha = bolt.life; ctx.strokeStyle = color; ctx.lineWidth = bolt.width; ctx.shadowBlur = 15; ctx.shadowColor = color; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(bolt.segments[0].x, bolt.segments[0].y); for (let i = 1; i < bolt.segments.length; i++) ctx.lineTo(bolt.segments[i].x, bolt.segments[i].y); ctx.stroke(); ctx.restore(); }
    function drawFlower(f) { ctx.save(); ctx.translate(f.x, f.y); ctx.rotate(f.rot); ctx.globalAlpha = 0.85; ctx.fillStyle = f.color; ctx.shadowBlur = 8; ctx.shadowColor = f.color; if (f.type === 'petal') { ctx.beginPath(); ctx.ellipse(0, 0, f.size, f.size*0.5, 0, 0, Math.PI*2); ctx.fill(); } else { for (let i = 0; i < 5; i++) { ctx.save(); ctx.rotate((Math.PI*2/5)*i); ctx.beginPath(); ctx.ellipse(0, -f.size*0.5, f.size*0.4, f.size*0.7, 0, 0, Math.PI*2); ctx.fill(); ctx.restore(); } ctx.fillStyle = '#ffd93d'; ctx.beginPath(); ctx.arc(0, 0, f.size*0.25, 0, Math.PI*2); ctx.fill(); } ctx.restore(); }
    function drawHeart(h) { ctx.save(); ctx.translate(h.x, h.y); const s = h.size + Math.sin(h.pulse)*1.2; ctx.globalAlpha = h.alpha; ctx.fillStyle = h.color; ctx.shadowBlur = 10; ctx.shadowColor = h.color; ctx.beginPath(); ctx.moveTo(0, s*0.3); ctx.bezierCurveTo(0,0,-s*0.5,0,-s*0.5,s*0.3); ctx.bezierCurveTo(-s*0.5,s*0.7,0,s*1.1,0,s*1.3); ctx.bezierCurveTo(0,s*1.1,s*0.5,s*0.7,s*0.5,s*0.3); ctx.bezierCurveTo(s*0.5,0,0,0,0,s*0.3); ctx.fill(); ctx.restore(); }
    function loop() { ctx.clearRect(0, 0, W, H); if (ACTIVE && W > 0 && H > 0) { ACCENT = getAccent(); for (const f of flowers) { f.y += f.speedY; f.x += f.speedX; f.rot += f.rotSpeed; if (f.y > H+30) Object.assign(f, newFlower()); drawFlower(f); } for (const h of hearts) { h.y += h.speedY; h.x += h.speedX; h.pulse += 0.08; if (h.y > H+30) Object.assign(h, newHeart()); drawHeart(h); } for (let i = bolts.length-1; i >= 0; i--) { bolts[i].life -= bolts[i].fadeSpeed; if (bolts[i].life <= 0) { bolts.splice(i,1); continue; } drawLightning(bolts[i], ACCENT); } if (Math.random() < 0.02 && bolts.length < 2) bolts.push(newBolt()); } requestAnimationFrame(loop); }
    loop();
    return { start: () => { ACTIVE = true; canvas.classList.add('active'); resize(); for (let i=0;i<3;i++) setTimeout(()=>bolts.push(newBolt()),i*120); }, stop: () => { ACTIVE = false; canvas.classList.remove('active'); bolts.length = 0; ctx.clearRect(0,0,W,H); } };
}
const fxInstances = {};
$$('.tool-panel').forEach(p => { fxInstances[p.dataset.tool] = { form: createEffectForPanel(p.querySelector('.fx-canvas-form')), term: createEffectForPanel(p.querySelector('.fx-canvas-term')) }; });
function fxStart(t) { const fx = fxInstances[t]; if (fx) { fx.form?.start(); fx.term?.start(); } }
function fxStop(t) { const fx = fxInstances[t]; if (fx) { fx.form?.stop(); fx.term?.stop(); } }

(function() { const p = document.getElementById('theme-color'); if (!p) return; const s = localStorage.getItem('theme_accent'); if (s) { document.documentElement.style.setProperty('--accent', s); p.value = s; } p.addEventListener('input', (e) => { document.documentElement.style.setProperty('--accent', e.target.value); localStorage.setItem('theme_accent', e.target.value); }); })();

function classifyLine(line) { if (/\b(traceback|exception|error|lỗi|die|fail|thất bại)\b/i.test(line)) return 'err'; if (/\b(warn|cảnh báo|retry|timeout)\b/i.test(line)) return 'warn'; if (/\b(success|thành công|✔|✅|ok|done)\b/i.test(line)) return 'ok'; if (/\b(info|đang|bắt đầu|nick|job)\b/i.test(line)) return 'info'; return ''; }
function appendLine(el, line, ts = null) { if (!el) return; const d = document.createElement('div'); d.className = 'term-line ' + classifyLine(line); d.innerHTML = `<span class="ts">[${ts||now()}]</span>${escapeHtml(line)}`; el.appendChild(d); el.scrollTop = el.scrollHeight; }
setInterval(() => { const el = $('#clock'); if (el) el.textContent = now(); }, 1000);

$$('.tab-btn').forEach(btn => { btn.addEventListener('click', () => { const t = btn.dataset.tool; $$('.tab-btn').forEach(b => b.classList.toggle('active', b === btn)); $$('.tool-panel').forEach(p => p.classList.toggle('active', p.dataset.tool === t)); }); });
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
    getBtn(t, 'start').disabled = run; getBtn(t, 'stop').disabled = !run;
}

function buildInputSequence(t) {
    const token = (getCfg(t, 'cfg-token')?.value || '').trim();
    const ckRaw = (getCfg(t, 'cfg-cookies')?.value || '').trim();
    const dTym = getCfg(t, 'cfg-delay-tym')?.value || '10';
    const dFol = getCfg(t, 'cfg-delay-follow')?.value || '15';
    const dCmt = getCfg(t, 'cfg-delay-comment')?.value || '20';
    const thr = getCfg(t, 'cfg-threads')?.value || '10';
    const rot = getCfg(t, 'cfg-rotate')?.value || '99999';
    const jL = getCfg(t, 'cfg-job-like')?.checked;
    const jF = getCfg(t, 'cfg-job-follow')?.checked;
    const jC = getCfg(t, 'cfg-job-comment')?.checked;

    const lines = ckRaw.split('\n').map(s => s.trim()).filter(Boolean);
    const seq = [];
    seq.push(thr, token, String(lines.length));
    for (const l of lines) seq.push(l);
    seq.push(rot);
    seq.push(jL ? 'on' : 'off'); if (jL) seq.push(dTym);
    seq.push(jF ? 'on' : 'off'); if (jF) seq.push(dFol);
    seq.push(jC ? 'on' : 'off'); if (jC) seq.push(dCmt);
    return seq;
}

$$('.btn-start[data-tool]').forEach(btn => {
    if (btn.id === 'btn_fb_reg') return;
    btn.addEventListener('click', async () => {
        const t = btn.dataset.tool;
        const token = (getCfg(t, 'cfg-token')?.value || '').trim();
        const ck = (getCfg(t, 'cfg-cookies')?.value || '').trim();
        if (!token) return alert('Nhập Token XSMM!');
        if (!ck) return alert('Nhập Cookie!');
        btn.disabled = true;
        const res = await fetch(`/api/start/${t}`, { method: 'POST' });
        const d = await res.json();
        if (d.ok) {
            state[t] = { sessionId: d.session_id, status: 'running' };
            setStatus(t, 'running', d.session_id); socket.emit('join', { session_id: d.session_id });
            fxStart(t);
            const term = getTerm(t); if (term) { term.innerHTML = ''; appendLine(term, `▶ Bắt đầu [${t}]`); }
            await new Promise(r => setTimeout(r, 3000));
            const seq = buildInputSequence(t);
            for (let s of seq) {
                await new Promise(r => setTimeout(r, 300));
                await fetch(`/api/input/${d.session_id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: s }) });
                if (term) appendLine(term, `> [auto] ${s}`);
            }
        } else btn.disabled = false;
    });
});

$$('.btn-stop').forEach(btn => {
    btn.addEventListener('click', async () => {
        const t = btn.dataset.tool; const s = state[t];
        if (s) { await fetch(`/api/stop/${s.sessionId}`, { method: 'POST' }); }
        setStatus(t, 'stopped'); fxStop(t);
    });
});

$$('.btn-clear[data-tool]').forEach(btn => {
    btn.addEventListener('click', () => {
        const t = btn.dataset.tool;
        const term = getTerm(t); if (term) term.innerHTML = '';
        const cnt = getOutputCount(t); if (cnt) cnt.textContent = '0 dòng';
        const tbody = document.getElementById('v52_xu_tbody'); if (tbody) tbody.innerHTML = '<tr><td colspan="2" style="text-align:center;color:#888;padding:10px">Chưa có dữ liệu...</td></tr>';
        const total = document.getElementById('v52_total_xu'); if (total) total.innerText = '0';
        const c = document.getElementById('v52_nick_count'); if (c) c.innerText = '0';
        for (let k in xuTracker) delete xuTracker[k];
        
        const s = state[t]; if (s) fetch(`/api/stop/${s.sessionId}`, { method: 'POST' });
        setStatus(t, 'stopped'); fxStop(t);
    });
});

// 4. FB REG PAGE
document.getElementById('btn_fb_reg')?.addEventListener('click', async () => {
    const tasksRaw = document.getElementById('fb_reg_tasks').value.trim();
    const namesRaw = document.getElementById('fb_reg_names').value.trim();
    const avatarsRaw = document.getElementById('fb_reg_avatars').value.trim();
    const coversRaw = document.getElementById('fb_reg_covers').value.trim();
    const uid = document.getElementById('fb_reg_uid').value.trim();
    const pwd = document.getElementById('fb_reg_pwd').value.trim();
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
            avatar: avatarLines[i % avatarLines.length] || '', cover: coverLines[i % coverLines.length] || '', target_uid: uid, pwd: pwd
        });
    }
    
    document.getElementById('fb_reg_tbody').innerHTML = '';
    const res = await fetch('/api/fb_reg_start', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({tasks, threads}) });
    if ((await res.json()).ok) { fxStart('fb_regpage'); alert('Bắt đầu reg page + chuyển QTV!'); }
});

document.getElementById('btn_fb_clear')?.addEventListener('click', () => {
    document.getElementById('fb_reg_tbody').innerHTML = '<tr><td colspan="5" style="text-align:center;color:#888;padding:20px">Chưa có dữ liệu...</td></tr>';
    document.getElementById('fb_stat_ok').innerText = '0';
    document.getElementById('fb_stat_err').innerText = '0';
    fxStop('fb_regpage');
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

// SOCKET CHUNG
const xuTracker = {};
socket.on('output', d => {
    const { session_id, line, ts } = d;
    const t = Object.keys(state).find(k => state[k].sessionId === session_id);
    if (!t) return;
    const term = getTerm(t); if (!term) return;
    
    let isFollowGom = line.includes('Đã gom (') && line.includes('/8)');
    let isXuUpdate = line.includes('[[XU_UPDATE]]');
    
    if (isXuUpdate) {
        const parts = line.split('|');
        if (parts.length >= 4) {
            const nick = parts[1]; const xu = parseInt(parts[2]);
            xuTracker[nick] = (xuTracker[nick] || 0) + xu;
            
            const tbody = document.getElementById('v52_xu_tbody');
            const totalEl = document.getElementById('v52_total_xu');
            const countEl = document.getElementById('v52_nick_count');
            if (tbody) {
                if (tbody.querySelector('tr td[colspan]')) tbody.innerHTML = '';
                let existingRow = null;
                tbody.querySelectorAll('tr').forEach(tr => { if (tr.cells[0].innerText === nick) existingRow = tr; });
                if (existingRow) { existingRow.cells[1].innerText = "+" + xuTracker[nick] + " xu"; } 
                else { const tr = document.createElement('tr'); tr.innerHTML = `<td>${nick}</td><td style="color:#22c55e;font-weight:bold">+${xuTracker[nick]} xu</td>`; tbody.appendChild(tr); }
            }
            if (totalEl) totalEl.innerText = Object.values(xuTracker).reduce((a, b) => a + b, 0);
            if (countEl) countEl.innerText = Object.keys(xuTracker).length;
            return; 
        }
    }

    const div = document.createElement('div');
    if (isFollowGom) { div.style.color = '#22c55e'; div.style.fontWeight = 'bold'; div.style.textShadow = '0 0 8px #22c55e'; } 
    else { div.className = 'term-line ' + classifyLine(line); }
    div.innerHTML = `<span class="ts">[${ts||now()}]</span>${escapeHtml(line)}`;
    term.appendChild(div);
    term.scrollTop = term.scrollHeight;

    const cnt = getOutputCount(t); if (cnt) cnt.textContent = term.children.length + ' dòng';
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
