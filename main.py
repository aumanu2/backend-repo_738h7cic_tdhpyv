import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Test as TestSchema, Attempt as AttemptSchema, Submission as SubmissionSchema

app = FastAPI(title="CodeAssess API", version="0.1.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root_redirect():
    # Keep default route sending users to the designed landing page
    return RedirectResponse(url="/landing", status_code=307)


@app.get("/health")
def read_root():
    return {"message": "CodeAssess Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Utility to convert ObjectId to string

def _doc(d):
    if not d:
        return d
    d = dict(d)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


# Basic CRUD for Tests

@app.post("/api/tests", response_model=dict)
def create_test(test: TestSchema):
    try:
        inserted_id = create_document("test", test)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tests", response_model=List[dict])
def list_tests(limit: Optional[int] = 50):
    try:
        docs = get_documents("test", limit=limit)
        return [_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tests/{test_id}", response_model=dict)
def get_test(test_id: str):
    try:
        if not ObjectId.is_valid(test_id):
            raise HTTPException(status_code=400, detail="Invalid test id")
        doc = db["test"].find_one({"_id": ObjectId(test_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Test not found")
        return _doc(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Attempts lifecycle

@app.post("/api/attempts", response_model=dict)
def start_attempt(attempt: AttemptSchema):
    try:
        inserted_id = create_document("attempt", attempt)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/attempts", response_model=List[dict])
def list_attempts(test_id: Optional[str] = None, user_email: Optional[str] = None):
    try:
        filter_q = {}
        if test_id:
            filter_q["test_id"] = test_id
        if user_email:
            filter_q["user_email"] = user_email
        docs = get_documents("attempt", filter_q)
        return [_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Submissions

@app.post("/api/submissions", response_model=dict)
def add_submission(sub: SubmissionSchema):
    try:
        inserted_id = create_document("submission", sub)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/submissions", response_model=List[dict])
def list_submissions(attempt_id: Optional[str] = None):
    try:
        filter_q = {"attempt_id": attempt_id} if attempt_id else {}
        docs = get_documents("submission", filter_q)
        return [_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple schema exposure for the built-in DB viewer

@app.get("/schema")
def get_schema():
    return {
        "collections": [
            "user",
            "test",
            "attempt",
            "submission",
        ]
    }


# Landing Page — redesigned with a modern, Gen‑Z vibe
@app.get("/landing", response_class=HTMLResponse)
def landing_page():
    return """
    <!doctype html>
    <html lang='en'>
      <head>
        <meta charset='utf-8'/>
        <meta name='viewport' content='width=device-width, initial-scale=1'/>
        <title>Flames Assess — Modern Coding Assessments</title>
        <link rel='preconnect' href='https://fonts.googleapis.com'>
        <link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
        <link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap' rel='stylesheet'>
        <style>
          :root { --bg: #0b0b10; --fg: #e2e8f0; --muted:#94a3b8; --ink:#0b0b10; --brand:#7c3aed; --brand2:#06b6d4; --brand3:#22d3ee; --panel: rgba(255,255,255,.04); --border: rgba(148,163,184,.16); }
          * { box-sizing: border-box }
          html, body { height: 100% }
          body { margin:0; font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; color: var(--fg); background: radial-gradient(1200px 600px at 20% -10%, rgba(124,58,237,0.28), transparent), radial-gradient(1000px 500px at 120% 20%, rgba(6,182,212,0.24), transparent), var(--bg); }
          .container { max-width: 1200px; margin: 0 auto; padding: 24px }
          header { position: sticky; top: 0; backdrop-filter: saturate(1.2) blur(8px); background: linear-gradient(180deg, rgba(11,11,16,.72), rgba(11,11,16,.15)); border-bottom:1px solid var(--border); z-index: 20 }
          .nav { display:flex; align-items:center; justify-content:space-between; gap: 16px; padding: 12px 0 }
          .logo { display:flex; align-items:center; gap:10px; font-weight:800; letter-spacing:.3px }
          .logo-badge{ width:36px;height:36px;border-radius:12px;background: conic-gradient(from 210deg at 50% 50%, var(--brand), var(--brand2), var(--brand3), var(--brand)); display:grid; place-items:center; color:white; font-weight:900; border:1px solid rgba(255,255,255,.25); box-shadow: 0 8px 30px rgba(124,58,237,.25) }
          nav { display:flex; gap: 18px; color: var(--muted) }
          nav a { text-decoration:none; color: inherit; padding: 8px 10px; border-radius: 10px }
          nav a:hover { background: rgba(255,255,255,.06); color: #fff }
          .hero{ display:grid; grid-template-columns: 1.05fr .95fr; gap: 36px; align-items:center; padding: 56px 0 }
          h1 { font-size: clamp(40px, 6.5vw, 70px); line-height:1.02; margin: 0 0 14px; letter-spacing:-.02em }
          .gradient { background: linear-gradient(135deg, #fff, #e9d5ff 35%, #99f6e4 80%); -webkit-background-clip: text; background-clip:text; color: transparent; text-shadow: 0 12px 40px rgba(153,246,228,.12) }
          .kicker { color: var(--muted); font-weight:700; letter-spacing:.22em; text-transform:uppercase; font-size:11px }
          .subtitle{ color: var(--muted); max-width: 60ch; font-size: 18px }
          .cta{ display:flex; gap:12px; margin-top:24px; flex-wrap: wrap }
          .btn{ padding:12px 16px; border-radius:12px; border:1px solid rgba(148,163,184,.2); color:var(--ink); background:white; font-weight:800; box-shadow: 0 10px 24px rgba(124,58,237,.18) }
          .btn.sec{ background: transparent; color: var(--fg); border-color: rgba(148,163,184,.28) }
          .btn:hover{ transform: translateY(-1px); transition: .2s ease; }
          .badge{ display:inline-flex; gap:8px; align-items:center; padding:6px 10px; background: rgba(124,58,237,.12); color:#e9d5ff; border: 1px solid rgba(124,58,237,.25); border-radius:999px; font-size:12px; font-weight:800 }
          .cardgrid{ display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin: 48px 0 0 }
          .card{ padding:20px; border:1px solid var(--border); border-radius:16px; background: var(--panel); transition: .2s ease; min-height: 120px }
          .card:hover{ transform: translateY(-3px); background: linear-gradient(180deg, rgba(124,58,237,.10), rgba(255,255,255,.02)); box-shadow: 0 12px 30px rgba(124,58,237,.18) }
          .card h3{ margin:0 0 6px; font-size:18px }
          .card p{ margin:0; color: var(--muted) }
          .split { display:grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 30px }
          .stat { padding: 16px; border:1px solid var(--border); border-radius: 16px; background: var(--panel); text-align:center }
          .stat .num { font-size: 28px; font-weight: 900; letter-spacing: -.02em }
          footer{ padding: 48px 0; color: var(--muted); font-size:14px }
          @media (max-width: 980px){ .hero{ grid-template-columns: 1fr } .cardgrid{ grid-template-columns: 1fr } .split{ grid-template-columns: 1fr } }
          .glow{ position: fixed; inset: -10% -10% auto auto; width: 50vw; height: 50vw; background: radial-gradient(circle at 30% 30%, rgba(124,58,237,.35), transparent 60%); filter: blur(50px); pointer-events:none; }
          .glow2{ position: fixed; inset: auto auto -20% -20%; width: 45vw; height: 45vw; background: radial-gradient(circle at 70% 70%, rgba(6,182,212,.35), transparent 60%); filter: blur(50px); pointer-events:none; }
        </style>
      </head>
      <body>
        <div class="glow"></div>
        <div class="glow2"></div>
        <header>
          <div class="container nav">
            <div class="logo">
              <div class="logo-badge">FA</div>
              Flames Assess
            </div>
            <nav>
              <a href="#features">Features</a>
              <a href="/app">Try the App</a>
              <a href="#pricing">Pricing</a>
              <a href="#contact">Contact</a>
            </nav>
          </div>
        </header>

        <div class="container">
          <section class="hero">
            <div>
              <div class="kicker">Gen‑Z ready</div>
              <h1>
                A vibey coding assessment platform for teams, colleges and admins
                <span class="gradient">— fast, fair, and fun.</span>
              </h1>
              <p class="subtitle">Create beautiful, robust coding tests in minutes. Invite candidates, proctor securely, and get AI‑assisted insights that actually help you decide faster.</p>
              <div class="cta">
                <a class="btn" href="/app">Launch App</a>
                <a class="btn sec" href="/health">Check API Health</a>
                <a class="btn sec" href="/schema">View Schema</a>
              </div>
              <div style="margin-top:14px" class="badge">Live preview powered by FastAPI</div>
            </div>
            <div>
              <div class="cardgrid">
                <div class="card"><h3>Drag‑n‑Drop Builder</h3><p>Compose tests with questions, code cells, files, and cases.</p></div>
                <div class="card"><h3>Secure Proctoring</h3><p>Camera checks, tab‑switch detection, and audit trails.</p></div>
                <div class="card"><h3>AI Scoring</h3><p>Automatic grading with explainability and plagiarism checks.</p></div>
                <div class="card"><h3>Role‑based Access</h3><p>Companies, colleges, admins with granular permissions.</p></div>
                <div class="card"><h3>Analytics</h3><p>Completion funnels, difficulty, time‑to‑hire metrics.</p></div>
                <div class="card"><h3>Developer‑first</h3><p>REST API, webhooks, and export to CSV.</p></div>
              </div>
            </div>
          </section>

          <section id="features" class="split">
            <div class="stat"><div class="num">10x</div><div class="muted">faster to create tests</div></div>
            <div class="stat"><div class="num">98%</div><div class="muted">cheating attempts flagged</div></div>
          </section>

          <section id="contact" style="margin-top: 32px">
            <div class="card" style="padding: 18px">
              <h3 style="margin:0 0 8px">Need something custom?</h3>
              <p class="muted" style="margin:0 0 12px">We ship custom question types, proctoring rules, and integrations.</p>
              <a class="btn" href="mailto:hello@flames.assess">Contact Us</a>
            </div>
          </section>

          <footer>
            © <span id="yr"></span> Flames Assess — All rights reserved.
          </footer>
        </div>
        <script>document.getElementById('yr').textContent = new Date().getFullYear()</script>
      </body>
    </html>
    """


# Rich in-backend SPA — redesigned UI, same endpoints
@app.get("/app", response_class=HTMLResponse)
def mini_app():
    return """
    <!doctype html>
    <html lang='en'>
    <head>
        <meta charset='utf-8'/>
        <meta name='viewport' content='width=device-width, initial-scale=1'/>
        <title>Flames Assess — App</title>
        <link rel='preconnect' href='https://fonts.googleapis.com'>
        <link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
        <link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap' rel='stylesheet'>
        <style>
            :root { --bg: #0b0b10; --fg: #e2e8f0; --muted:#94a3b8; --brand:#7c3aed; --brand2:#06b6d4; --panel: rgba(255,255,255,.03); --panel2: rgba(255,255,255,.05); --border: rgba(148,163,184,.2) }
            * { box-sizing: border-box }
            body { margin:0; font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; color: var(--fg); background: radial-gradient(1100px 520px at -20% -20%, rgba(124,58,237,.26), transparent), radial-gradient(1100px 520px at 120% 0%, rgba(6,182,212,.22), transparent), var(--bg); }
            .shell { display:grid; grid-template-columns: 240px 1fr; min-height: 100vh }
            aside { border-right:1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.03)); padding: 16px; position: sticky; top:0; height: 100vh }
            .brand { display:flex; gap:10px; align-items:center; font-weight:900; letter-spacing:.2px; margin-bottom: 10px }
            .badge { width:30px; height:30px; border-radius:10px; background: linear-gradient(135deg, var(--brand), var(--brand2)); display:grid; place-items:center; font-size:12px; box-shadow: 0 10px 20px rgba(124,58,237,.25) }
            .nav { display:flex; flex-direction: column; gap: 8px; margin-top: 8px }
            .nav button { text-align:left; width: 100%; padding: 10px 12px; border-radius: 10px; border:1px solid var(--border); background: var(--panel); color: var(--fg); font-weight: 700; cursor: pointer }
            .nav button.active { background: linear-gradient(180deg, rgba(124,58,237,.18), transparent); border-color: rgba(124,58,237,.35) }
            main { padding: 22px }
            .toolbar { display:flex; align-items:center; justify-content:space-between; margin-bottom: 12px }
            .panel { border:1px solid var(--border); border-radius: 14px; padding: 16px; background: var(--panel) }
            .row { display:flex; gap: 16px; align-items:flex-start; flex-wrap: wrap }
            input, textarea, select { background: rgba(255,255,255,.06); border:1px solid var(--border); color: var(--fg); border-radius: 10px; padding: 10px 12px; width: 280px }
            textarea { width: 480px; height: 140px }
            label { display:block; font-size:12px; color: var(--muted); margin: 0 0 6px }
            button.btn { padding: 10px 14px; border-radius: 10px; background: linear-gradient(135deg, var(--brand), var(--brand2)); color: white; border: none; font-weight: 800; cursor: pointer }
            table { width: 100%; border-collapse: collapse; margin-top: 12px }
            th, td { border-bottom: 1px solid var(--border); text-align:left; padding: 10px; vertical-align: top }
            .muted { color: var(--muted) }
            .pill { display:inline-block; padding: 3px 8px; font-size: 12px; border-radius: 999px; background: rgba(124,58,237,.15); border:1px solid rgba(124,58,237,.35) }
            a { color: #99f6e4; text-decoration: none }
            code, pre { background: rgba(255,255,255,.06); border:1px solid var(--border); border-radius: 8px; padding: 8px; display:block; white-space: pre-wrap; }
            .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 16px }
            @media (max-width: 1024px){ .shell { grid-template-columns: 1fr } aside { position: static; height:auto } .grid { grid-template-columns: 1fr } textarea { width: 100% } }
            .toast { position: fixed; right: 16px; bottom: 16px; background: var(--panel2); border:1px solid var(--border); padding: 12px 14px; border-radius: 12px; box-shadow: 0 12px 30px rgba(0,0,0,.35); display:none }
            .skeleton { height: 12px; background: linear-gradient(90deg, rgba(255,255,255,.06), rgba(255,255,255,.12), rgba(255,255,255,.06)); background-size: 200% 100%; animation: shimmer 1.2s infinite }
            @keyframes shimmer { 0%{ background-position: 200% 0 } 100% { background-position: -200% 0 } }
        </style>
    </head>
    <body>
        <div class='shell'>
            <aside>
                <div class='brand'><div class='badge'>FA</div> Flames Assess</div>
                <div class='nav'>
                    <button class='nav-btn active' data-tab='tests'>Tests</button>
                    <button class='nav-btn' data-tab='create'>Create Test</button>
                    <button class='nav-btn' data-tab='take'>Take Test</button>
                    <button class='nav-btn' data-tab='attempts'>Attempts</button>
                    <a class='nav-btn' href='/landing' style='text-decoration:none; display:block; padding:10px 12px; border:1px solid var(--border); border-radius:10px; background:var(--panel); margin-top:8px'>← Back to Landing</a>
                </div>
            </aside>
            <main>
                <div class='toolbar'>
                    <div class='muted'>Flames Assess — Mini App</div>
                    <div><a href='/health'>Health</a> · <a href='/schema'>Schema</a></div>
                </div>
                <div id='view' class='panel'>
                    <div class='skeleton' style='width:60%'></div>
                    <div class='skeleton' style='width:40%; margin-top:8px'></div>
                </div>
            </main>
        </div>
        <div id='toast' class='toast'></div>

        <script>
            const API = '' // same origin
            const view = document.getElementById('view');
            const toast = document.getElementById('toast');

            function showToast(msg){
                toast.textContent = msg;
                toast.style.display = 'block';
                clearTimeout(window.__t);
                window.__t = setTimeout(()=> toast.style.display = 'none', 2000);
            }

            function route(tab){
                document.querySelectorAll('.nav-btn').forEach(el => el.classList.toggle('active', el.dataset.tab===tab))
                if(tab==='create') renderCreate();
                else if(tab==='take') renderTake();
                else if(tab==='attempts') renderAttempts();
                else renderTests();
            }
            document.querySelectorAll('.nav-btn').forEach(el=> el.addEventListener('click', ()=> route(el.dataset.tab)))

            async function fetchJSON(url, opts){
                const res = await fetch(url, opts);
                const data = await res.json().catch(()=> ({}));
                if(!res.ok) throw new Error(data.detail || JSON.stringify(data));
                return data;
            }

            // Tests list
            function renderTests(){
                view.innerHTML = `
                    <div>
                        <div style='display:flex; align-items:center; justify-content:space-between'>
                            <h2 style='margin:6px 0'>All Tests</h2>
                            <div><button class='btn' id='refreshBtn'>Refresh</button></div>
                        </div>
                        <table>
                            <thead><tr><th>Title</th><th>Difficulty</th><th>Tags</th><th>ID</th></tr></thead>
                            <tbody id='tbody'><tr><td colspan='4' class='muted'>Loading…</td></tr></tbody>
                        </table>
                    </div>`;
                document.getElementById('refreshBtn').addEventListener('click', loadTests);
                loadTests();
            }
            async function loadTests(){
                try{
                    const data = await fetchJSON(`${API}/api/tests`);
                    const tbody = document.getElementById('tbody');
                    if(!data.length){ tbody.innerHTML = "<tr><td colspan='4' class='muted'>No tests yet. Create one!</td></tr>"; showToast('No tests yet'); return; }
                    tbody.innerHTML = data.map(r => `
                        <tr>
                            <td>${r.title || '-'}</td>
                            <td><span class='pill'>${r.difficulty || '-'}</span></td>
                            <td>${Array.isArray(r.tags) ? r.tags.join(', ') : '-'}</td>
                            <td class='muted'>${r.id || '-'}</td>
                        </tr>`).join('');
                    showToast(`Fetched ${data.length} test(s)`);
                }catch(e){ showToast('Failed to fetch tests'); }
            }

            // Create test
            function renderCreate(){
                view.innerHTML = `
                    <div class='grid'>
                        <div>
                            <h2 style='margin:6px 0'>Create Test</h2>
                            <label>Title</label>
                            <input id='title' placeholder='e.g., Frontend Basics' />
                            <label style='margin-top:10px'>Difficulty</label>
                            <select id='difficulty'>
                                <option value='easy'>easy</option>
                                <option value='medium'>medium</option>
                                <option value='hard'>hard</option>
                            </select>
                            <label style='margin-top:10px'>Tags (comma separated)</label>
                            <input id='tags' placeholder='react, js, css' />
                            <label style='margin-top:10px'>Description</label>
                            <textarea id='desc' placeholder='Short description'></textarea>
                            <div style='margin-top:12px'><button class='btn' id='createBtn'>Create Test</button></div>
                        </div>
                        <div>
                            <h3 style='margin:6px 0'>Preview</h3>
                            <pre id='preview'></pre>
                        </div>
                    </div>`;
                const updatePreview = () => {
                    const payload = buildTestPayload();
                    document.getElementById('preview').textContent = JSON.stringify(payload, null, 2);
                }
                ['title','difficulty','tags','desc'].forEach(id=>{
                    const el = document.getElementById(id);
                    el.addEventListener('input', updatePreview);
                    el.addEventListener('change', updatePreview);
                })
                document.getElementById('createBtn').addEventListener('click', createTest);
                updatePreview();
            }
            function buildTestPayload(){
                const title = document.getElementById('title').value.trim();
                const difficulty = document.getElementById('difficulty').value.trim() || 'easy';
                const tags = document.getElementById('tags').value.split(',').map(s => s.trim()).filter(Boolean);
                const description = document.getElementById('desc').value.trim();
                return { title, description, difficulty, tags, questions: [], created_by: 'demo@flames.assess' };
            }
            async function createTest(){
                const payload = buildTestPayload();
                if(!payload.title){ showToast('Please enter a title'); return; }
                try{
                    const data = await fetchJSON(`${API}/api/tests`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
                    showToast('Created test ' + (data.id || ''));
                    route('tests');
                }catch(e){ showToast('Failed to create test'); }
            }

            // Take test
            function renderTake(){
                view.innerHTML = `
                    <div>
                        <h2 style='margin:6px 0'>Take Test</h2>
                        <div class='row'>
                            <div>
                                <label>Test ID</label>
                                <input id='take_test_id' placeholder='Paste test id' />
                            </div>
                            <div>
                                <label>Your Email</label>
                                <input id='take_email' placeholder='you@example.com' />
                            </div>
                            <div style='align-self:flex-end'>
                                <button class='btn' id='startBtn'>Start Attempt</button>
                            </div>
                        </div>
                        <div id='attemptBox' style='margin-top:16px; display:none'>
                            <div class='row'>
                                <div style='flex:1'>
                                    <label>Language</label>
                                    <select id='lang'>
                                        <option>python</option>
                                        <option>javascript</option>
                                        <option>cpp</option>
                                    </select>
                                    <label style='margin-top:10px'>Code</label>
                                    <textarea id='code' placeholder='Write your solution here…' style='width:100%; height:220px'></textarea>
                                </div>
                                <div style='width:360px'>
                                    <label>Notes</label>
                                    <textarea id='notes' placeholder='Optional notes for reviewers' style='width:100%; height:140px'></textarea>
                                    <div style='margin-top:12px'><button class='btn' id='submitBtn'>Submit Solution</button></div>
                                </div>
                            </div>
                        </div>
                    </div>`;
                document.getElementById('startBtn').addEventListener('click', startAttempt);
            }
            let currentAttempt = null;
            async function startAttempt(){
                const test_id = document.getElementById('take_test_id').value.trim();
                const user_email = document.getElementById('take_email').value.trim();
                if(!test_id || !user_email){ showToast('Enter test id and email'); return }
                try{
                    const payload = { test_id, user_email, status: 'started' };
                    const data = await fetchJSON(`${API}/api/attempts`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
                    currentAttempt = data.id;
                    document.getElementById('attemptBox').style.display = 'block';
                    showToast('Attempt started');
                }catch(e){ showToast('Failed to start attempt'); }
            }
            async function submitSolution(){
                if(!currentAttempt){ showToast('Start an attempt first'); return }
                const body = {
                    attempt_id: currentAttempt,
                    language: document.getElementById('lang').value,
                    code: document.getElementById('code').value,
                    notes: document.getElementById('notes').value,
                };
                try{
                    const data = await fetchJSON(`${API}/api/submissions`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
                    showToast('Submission saved');
                    document.getElementById('code').value = '';
                    document.getElementById('notes').value = '';
                }catch(e){ showToast('Failed to submit'); }
            }
            function wireSubmit(){
                const btn = document.getElementById('submitBtn');
                if(btn) btn.addEventListener('click', submitSolution);
            }
            const observer = new MutationObserver(wireSubmit);
            observer.observe(document.body, { childList:true, subtree:true });

            // Attempts
            function renderAttempts(){
                view.innerHTML = `
                    <div>
                        <div style='display:flex; align-items:center; justify-content:space-between'>
                            <h2 style='margin:6px 0'>Attempts</h2>
                            <div>
                                <input id='filter_email' placeholder='Filter by email' style='width:220px' />
                                <button class='btn' id='filterBtn'>Filter</button>
                            </div>
                        </div>
                        <table>
                            <thead><tr><th>Attempt ID</th><th>Test</th><th>User</th><th>Status</th></tr></thead>
                            <tbody id='tbodyA'><tr><td colspan='4' class='muted'>Loading…</td></tr></tbody>
                        </table>
                    </div>`;
                document.getElementById('filterBtn').addEventListener('click', loadAttempts);
                loadAttempts();
            }
            async function loadAttempts(){
                try{
                    const email = (document.getElementById('filter_email')?.value || '').trim();
                    const url = email ? `${API}/api/attempts?user_email=${encodeURIComponent(email)}` : `${API}/api/attempts`;
                    const data = await fetchJSON(url);
                    const tbody = document.getElementById('tbodyA');
                    if(!data.length){ tbody.innerHTML = "<tr><td colspan='4' class='muted'>No attempts yet.</td></tr>"; showToast('No attempts'); return; }
                    tbody.innerHTML = data.map(r => `
                        <tr>
                            <td class='muted'>${r.id || '-'}</td>
                            <td>${r.test_id || '-'}</td>
                            <td>${r.user_email || '-'}</td>
                            <td><span class='pill'>${r.status || '-'}</span></td>
                        </tr>`).join('');
                    showToast(`Fetched ${data.length} attempt(s)`);
                }catch(e){ showToast('Failed to fetch attempts'); }
            }

            // Default route
            route('tests');
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
