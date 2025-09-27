// ======================= FULL WORKING SCRIPT (24x7 HARDENED) =======================
const express = require("express");
const fs = require("fs");
const path = require("path");
const pino = require("pino");
const multer = require("multer");
const {
  makeInMemoryStore,
  useMultiFileAuthState,
  delay,
  makeCacheableSignalKeyStore,
  Browsers,
  fetchLatestBaileysVersion,
  makeWASocket,
  isJidBroadcast,
  DisconnectReason
} = require("@whiskeysockets/baileys");

const app = express();
const PORT = process.env.PORT || 21215;

// --- folders
if (!fs.existsSync("temp")) fs.mkdirSync("temp");
if (!fs.existsSync("uploads")) fs.mkdirSync("uploads");
const upload = multer({ dest: "uploads/" });

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// === state
const activeClients = new Map();        // sessionId -> { client, number, authPath, reconnectBackoff, lastOpenAt }
const activeTasks = new Map();          // taskId -> taskInfo
const connectionStates = new Map();     // sessionId -> 'open'|'close'|'connecting'

// === TASK ID generator: BHAT-WASU- + 20 uppercase letters/digits ===
function generateStopKey() {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let out = "";
  for (let i = 0; i < 20; i++) out += chars.charAt(Math.floor(Math.random() * chars.length));
  return "BROKEN-NADEEM-" + out;
}

/* ======================= FRONTEND (UI) ======================= */
app.get("/", (req, res) => {
  res.send(`<!doctype html><html><head><meta charset="utf-8">
<title>🫂❤️‍🩹 BHAT WASU WHATSAPP SERVER 🫂❤️‍🩹</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
html,body{height:100%;margin:0;padding:0;background:#e9e9e9;font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif}
.container{max-width:820px;margin:18px auto;padding:10px}
h1{color:#008000;text-align:center;margin:6px 0 14px 0;font-weight:900}
.box{background:#f0f0f0;border-radius:18px;padding:18px;margin:12px 0;border:4px solid rgba(0,255,0,0.55);box-shadow:0 0 18px rgba(0,255,0,0.12)}
.level{font-size:18px;color:#006400;font-weight:800;margin-bottom:8px;text-align:left}
input[type=text],input[type=number],select,textarea{
  width:92%;max-width:720px;padding:12px;margin:8px auto;border-radius:28px;border:3px solid rgba(0,255,0,0.6);
  box-shadow:0 0 12px rgba(0,255,0,0.06);display:block;font-size:16px;background:#fff
}
.file-row{width:92%;max-width:720px;margin:8px auto;display:flex;gap:8px;align-items:center;justify-content:flex-start}
.choose-btn{padding:10px 16px;border-radius:24px;border:3px solid rgba(0,255,0,0.8);background:#00ff00;color:#000;font-weight:800;cursor:pointer}
.file-status{font-weight:700;color:#444;padding:8px 12px;border-radius:8px;background:#fff;border:2px solid rgba(0,0,0,0.06)}
input[type=file]{display:none}
button{width:92%;max-width:720px;margin:10px auto;padding:12px;border-radius:28px;border:3px solid rgba(0,255,0,0.8);
  background:#00ff00;color:#000;font-weight:800;font-size:18px;display:block;cursor:pointer;box-shadow:0 0 20px rgba(0,255,0,0.25)}
button.small{width:auto;padding:8px 14px;border-radius:20px}
.mini{font-size:14px;color:#444;margin-top:6px}
#groupSelection{display:none;background:#fff;border-radius:14px;padding:12px;border:2px solid #e6c200}
#groupList{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:10px}
.groupCard{background:#fffde7;border:2px solid #e6c200;border-radius:14px;padding:10px;text-align:center;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px}
.groupCard img{width:60px;height:60px;border-radius:50%;object-fit:cover}
.groupCard.selected{background:#fff2a8;border-color:#cc9900;box-shadow:0 0 18px rgba(230,200,0,0.08)}
#selectedGroupsBox{display:none;background:#fff;border:2px solid #e6c200;border-radius:12px;padding:12px;margin-top:10px;text-align:left;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.selected-item{display:flex;gap:8px;align-items:center;padding:6px 8px;border-radius:8px;background:#fff8e6;border:1px solid #e6c200}
.selected-item img{width:36px;height:36px;border-radius:50%;object-fit:cover}
.sessions{background:#fff;padding:12px;border-radius:12px;border:2px solid rgba(0,255,0,0.35);margin-top:10px}
@media (max-width:520px){.file-row{flex-direction:column;align-items:stretch}.choose-btn{width:100%}}
</style>
</head>
<body>
<div class="container">
  <h1 id="mainHeader">BROKEN NADEEM</h1>

  <div class="box">
    <div class="level">OWNER BROKEN NADEEM IINSID3</div>
    <input id="numberInput" type="text" placeholder="91 ENTER YOUR NUMBER"/>
    <button type="button" onclick="generatePairingCode()">GENERATE PAIR CODE</button>
    <div id="pairingResult" class="mini"></div>
  </div>

  <div class="box">
    <div class="level"></div>
    <select id="targetType" required>
      <option value="">CHOOSE OPINION</option>
      <option value="number">TARGET NUMBER</option>
      <option value="group">SELECT GROUP</option>
    </select>
    <input id="targetInput" type="text" placeholder="ENTER TARGET NUMBER"/>

    <div id="groupSelection">
      <div class="mini">TAP TO SELECT/DESELECT MULTIPLE GROUPS</div>
      <div id="groupList"></div>
      <input type="hidden" id="groupIds">
      <button id="doneBtn" type="button" class="small">DONE</button>
    </div>

    <div id="selectedGroupsBox"></div>

    <div class="file-row">
      <input id="nativeFile" type="file" accept=".txt"/>
      <button class="choose-btn" type="button" onclick="document.getElementById('nativeFile').click()">CHOOSE FILE</button>
      <div id="fileStatus" class="file-status">NO FILE CHOSEN</div>
    </div>

    <input id="prefix" type="text" placeholder="ENTER HATER NAME"/>
    <input id="delaySec" type="number" min="1" placeholder="ENTER SPEED SECOND"/>
    <button type="button" onclick="startSend()">START SERVER</button>
  </div>

  <div class="box">
    <div class="level">YOUR STOP KEY</div>
    <button type="button" onclick="showMyTaskId()">SHOW MY TASK ID</button>
    <div id="taskIdDisplay" style="display:none;margin-top:10px;padding:12px;background:#fff;border-radius:10px;border:2px solid rgba(0,255,0,0.2)"></div>
  </div>

  <div class="box">
    <div class="level">STOP SERVER</div>
    <input id="stopTaskId" type="text" placeholder="ENTER YOUR STOP KEY"/>
    <button type="button" onclick="stopTask()">STOP SERVER</button>
  </div>

  <div class="sessions">
    <div>ACTIVE SESSION➠ <span id="sCount">0</span></div>
    <div>ACTIVE USER➠ <span id="tCount">0</span></div>
  </div>
</div>

<script>
(function headerCycle(){
  const texts=['BROKEN NADEEM','WHATSAPP SERVER','OFFLINE WHATSAPP'];let i=0;
  const el=document.getElementById('mainHeader');el.innerText=texts[i];
  setInterval(()=>{i=(i+1)%texts.length;el.innerText=texts[i]},5000);
})();
const nativeFile=document.getElementById('nativeFile');
const fileStatus=document.getElementById('fileStatus');
nativeFile.addEventListener('change',()=>{fileStatus.innerText=(nativeFile.files&&nativeFile.files[0])?nativeFile.files[0].name.toUpperCase():'NO FILE CHOSEN'});

async function generatePairingCode(){
  const num=document.getElementById('numberInput').value;
  if(!num){alert('Enter number');return;}
  const r=await fetch('/code?number='+encodeURIComponent(num));
  const obj=await r.json();
  if(obj.error){document.getElementById('pairingResult').innerHTML='<span style="color:#900">'+obj.error+'</span>';return;}
  if(obj.sessionId) localStorage.setItem('wa_session_id',obj.sessionId);
  document.getElementById('pairingResult').innerHTML='<div style="font-weight:800;word-break:break-all;">'+(obj.code||obj.msg||'')+'</div>';
}
document.getElementById('targetType').addEventListener('change', async function(){
  const val=this.value;
  const targetInput=document.getElementById('targetInput');
  const groupSelection=document.getElementById('groupSelection');
  const groupList=document.getElementById('groupList');
  const doneBtn=document.getElementById('doneBtn');
  const groupIds=document.getElementById('groupIds');
  const selBox=document.getElementById('selectedGroupsBox');

  if(val==='group'){
    targetInput.style.display='none';targetInput.removeAttribute('required');
    groupSelection.style.display='block';groupList.innerHTML='<div class="mini">Loading groups...</div>';
    try{
      const sessionId=localStorage.getItem('wa_session_id')||'';
      const res=await fetch('/get-groups?sessionId='+encodeURIComponent(sessionId));
      const groups=await res.json();
      if(groups.error){groupList.innerHTML='<div style="color:#c00">'+groups.error+'</div>';return;}
      let selected=[];groupList.innerHTML='';
      groups.forEach(g=>{
        const div=document.createElement('div');div.className='groupCard';
        const pic=g.profilePic||'https://via.placeholder.com/150';
        div.innerHTML='<img src="'+pic+'" alt="pic"><div style="margin-top:6px;font-weight:700;color:#8a6d00">'+(g.name||'Unnamed Group')+'</div>';
        div.dataset.gid=g.id;div.dataset.gname=g.name||'Unnamed Group';div.dataset.gpic=pic;
        div.onclick=()=>{if(selected.includes(g.id)){selected=selected.filter(x=>x!==g.id);div.classList.remove('selected');}
                         else{selected.push(g.id);div.classList.add('selected');}
                         groupIds.value=selected.join(',');};
        groupList.appendChild(div);
      });
      doneBtn.onclick=()=>{
        if(groupIds.value.trim()===''){alert('Please select at least one group first.');return;}
        groupSelection.style.display='none';doneBtn.style.display='none';
        const selCards=document.querySelectorAll('.groupCard.selected');const items=[];
        selCards.forEach(card=>{items.push({id:card.dataset.gid,name:card.dataset.gname,pic:card.dataset.gpic});});
        let html='';items.forEach(it=>{html+='<div class="selected-item"><img src="'+it.pic+'" alt="pic"><div style="font-weight:700">'+it.name+'</div></div>';});
        selBox.innerHTML=html;selBox.style.display='flex';
      };
    }catch(e){groupList.innerHTML='<div style="color:#c00">FAILED TO LOAD GROUP. MAKE SURE WHATSAPP SESSION CONNECTED.</div>';}
  }else{
    groupSelection.style.display='none';targetInput.style.display='block';targetInput.setAttribute('required','required');
    groupIds.value='';groupList.innerHTML='';doneBtn.style.display='inline-block';selBox.style.display='none';selBox.innerHTML='';
  }
});
async function startSend(){
  const targetType=document.getElementById('targetType').value;
  const target=document.getElementById('targetInput').value;
  const fileEl=document.getElementById('nativeFile');
  const prefix=document.getElementById('prefix').value||'';
  const delaySec=document.getElementById('delaySec').value;
  const groupIds=document.getElementById('groupIds').value||'';
  const sessionId=localStorage.getItem('wa_session_id')||'';
  if(!targetType||!delaySec||!fileEl.files[0]){alert('Please fill required fields');return;}
  const form=new FormData();
  form.append('targetType',targetType); form.append('target',target);
  form.append('prefix',prefix); form.append('delaySec',delaySec);
  form.append('groupIds',groupIds); form.append('messageFile',fileEl.files[0]);
  form.append('sessionId',sessionId);
  const res=await fetch('/send-message',{method:'POST',body:form});
  const txt=await res.text(); document.open(); document.write(txt); document.close();
}
function showMyTaskId(){
  const t=localStorage.getItem('wa_task_id');const el=document.getElementById('taskIdDisplay');
  el.innerHTML='<div style="word-break:break-all;font-weight:700">'+(t||'No active task')+'</div>'; el.style.display='block';
}
async function stopTask(){
  const id=document.getElementById('stopTaskId').value;
  if(!id){alert('Enter Task ID');return;}
  const res=await fetch('/stop-task',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({taskId:id})});
  const txt=await res.text(); alert(txt);
}
// live counts
async function tickCounts(){
  try{ const r=await fetch('/stats'); const s=await r.json();
       document.getElementById('sCount').innerText=s.sessions; document.getElementById('tCount').innerText=s.tasks;
  }catch{}
}
setInterval(tickCounts,3000); tickCounts();
</script>
</body></html>`);
});

/* ===================== Helpers (24x7) ===================== */

function isSocketOpen(client){
  try { return !!(client && client.ws && client.ws.socket && client.ws.socket.readyState === 1); }
  catch { return false; }
}

async function waitUntilConnected(sessionId, timeoutMs = 120000) {
  const start = Date.now();
  while (true) {
    const state = connectionStates.get(sessionId);
    if (state === 'open') return;
    if (Date.now() - start > timeoutMs) throw new Error('waitUntilConnected timeout');
    await delay(1500);
  }
}

async function safePresenceUpdate(waClient, who = 'available') {
  try { if (waClient) await waClient.sendPresenceUpdate(who); } catch (e) { /* ignore */ }
}

// retry with backoff
async function sendWithRetry(waClient, jid, content, maxAttempts = 8) {
  let attempt = 0;
  while (attempt < maxAttempts) {
    try { await waClient.sendMessage(jid, content); return; }
    catch (e) {
      attempt++;
      const status = e?.output?.statusCode || e?.status || 0;
      const transient =
        status === 408 || status === 429 || (status >= 500 && status < 600) ||
        /timed?\s*out/i.test(e?.message || "") ||
        /ETIMEDOUT|ECONNRESET|ENETUNREACH|EAI_AGAIN/i.test(e?.code || "");
      const waitMs = Math.min(30000, 800 * attempt * attempt);
      console.log(`[sendWithRetry] attempt ${attempt} failed (${status||'n/a'}). ${transient?'retrying':'hard'} in ${waitMs}ms`);
      if (!transient && attempt >= 2) throw e;
      await delay(waitMs);
    }
  }
  throw new Error(`sendWithRetry exhausted attempts for ${jid}`);
}

/* ===================== Make/Init client ===================== */
async function makeClient(sessionPath, number){
  const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
  let version;
  try { const v = await fetchLatestBaileysVersion(); version = v?.version; }
  catch (err) { version = undefined; console.warn("fetchLatestBaileysVersion failed:", err?.message||err); }

  const waClient = makeWASocket({
    version,
    auth: {
      creds: state.creds,
      keys: makeCacheableSignalKeyStore(state.keys, pino({ level: "fatal" }).child({ level: "fatal" }))
    },
    printQRInTerminal: false,
    logger: pino({ level: "fatal" }).child({ level: "fatal" }),
    browser: Browsers.ubuntu('Chrome'),
    syncFullHistory: false,
    generateHighQualityLinkPreview: true,
    shouldIgnoreJid: jid => isJidBroadcast(jid),
    getMessage: async () => ({})
  });

  waClient.ev.on("creds.update", saveCreds);

  return waClient;
}

async function initializeClient(sessionId, number, sessionPath) {
  try {
    if (!sessionPath || !fs.existsSync(sessionPath)) {
      console.warn(`initializeClient: auth path missing for ${sessionId}`);
      activeClients.delete(sessionId);
      connectionStates.delete(sessionId);
      return;
    }

    // If there's an active client already and it's open, skip reinit
    const existing = activeClients.get(sessionId);
    if (existing && existing.client && isSocketOpen(existing.client) && connectionStates.get(sessionId) === 'open') {
      // already healthy
      return;
    }

    const waClient = await makeClient(sessionPath, number);
    activeClients.set(sessionId, {
      client: waClient,
      number,
      authPath: sessionPath,
      reconnectBackoff: Math.max(1000, existing?.reconnectBackoff || 1000),
      lastOpenAt: 0
    });
    connectionStates.set(sessionId, 'connecting');

    waClient.ev.on("connection.update", async (s) => {
      try {
        const { connection, lastDisconnect } = s;
        if (connection === "open") {
          connectionStates.set(sessionId, 'open');
          const info = activeClients.get(sessionId);
          if (info){ info.reconnectBackoff = 1000; info.lastOpenAt = Date.now(); activeClients.set(sessionId, info); }
          console.log(`[OPEN] ${sessionId}`);
        } else if (connection === "close") {
          connectionStates.set(sessionId, 'close');
          const err = lastDisconnect?.error;
          const code = err?.output?.statusCode || err?.data?.statusCode || err?.status || 0;
          const reason = err?.output?.payload?.error || err?.message || '';
          console.log(`[CLOSE] ${sessionId} code=${code} reason=${reason}`);

          const shouldLogout = code === DisconnectReason.loggedOut || code === 401;
          if (shouldLogout) {
            console.warn(`[LOGGED OUT] ${sessionId} clearing auth.`);
            try { fs.rmSync(sessionPath, { recursive: true, force: true }); } catch (e) {}
            activeClients.delete(sessionId);
            connectionStates.delete(sessionId);
            return;
          }
          const info = activeClients.get(sessionId) || { reconnectBackoff: 1000, authPath: sessionPath, number };
          info.reconnectBackoff = Math.min(600000, (info.reconnectBackoff || 1000) * 2);
          activeClients.set(sessionId, info);
          setTimeout(() => initializeClient(sessionId, number, sessionPath).catch(()=>{}), info.reconnectBackoff);
        } else if (connection === "connecting") {
          connectionStates.set(sessionId, 'connecting');
        }
      } catch (e) {
        console.warn('[connection.update handler error]', e?.message || e);
      }
    });

    // keepalive presence ping (clear on close)
    const keep = setInterval(() => safePresenceUpdate(waClient, 'available'), 60_000);
    waClient.ev.on('connection.update', (u) => { if (u.connection === 'close') { try { clearInterval(keep); } catch {} } });

    // catch unexpected errors from this client and attempt a soft reconnect
    waClient.ev.on('creds.update', () => { /* creds saved by saveCreds already */ });

  } catch (err) {
    console.error(`[INIT FAIL] ${sessionId}:`, err?.message||err);
    const info = activeClients.get(sessionId) || { reconnectBackoff: 2000, authPath: sessionPath, number };
    info.reconnectBackoff = Math.min(600000, (info.reconnectBackoff || 2000) * 2);
    activeClients.set(sessionId, info);
    setTimeout(() => initializeClient(sessionId, number, sessionPath).catch(()=>{}), info.reconnectBackoff);
  }
}

/* ===================== PAIRING CODE LOGIN ===================== */
app.get("/code", async (req, res) => {
  const num = (req.query.number || "").replace(/[^0-9]/g, "");
  if (!num) return res.json({ error: "Invalid number" });

  const sessionId = `session_${Date.now()}_${Math.random().toString(36).slice(2,7)}`;
  const sessionPath = path.join("temp", sessionId);
  if (!fs.existsSync(sessionPath)) fs.mkdirSync(sessionPath, { recursive: true });

  try {
    const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
    let version;
    try { const v = await fetchLatestBaileysVersion(); version = v?.version; }
    catch (err) { version = undefined; console.warn("fetchLatestBaileysVersion failed:", err?.message||err); }

    const waClient = makeWASocket({
      version,
      auth: {
        creds: state.creds,
        keys: makeCacheableSignalKeyStore(state.keys, pino({ level: "fatal" }).child({ level: "fatal" }))
      },
      printQRInTerminal: false,
      logger: pino({ level: "fatal" }).child({ level: "fatal" }),
      browser: Browsers.ubuntu('Chrome'),
      syncFullHistory: false,
      generateHighQualityLinkPreview: true,
      shouldIgnoreJid: jid => isJidBroadcast(jid),
      getMessage: async () => ({})
    });

    connectionStates.set(sessionId, 'connecting');

    let codeMsg = 'SCAN QR FROM CLIENT';
    try {
      if (!waClient.authState?.creds?.registered && typeof waClient.requestPairingCode === 'function') {
        await delay(1200);
        codeMsg = await waClient.requestPairingCode(num);
      } else {
        codeMsg = "Session created/loaded — already registered.";
}
