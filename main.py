import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Test as TestSchema, Attempt as AttemptSchema, Submission as SubmissionSchema

app = FastAPI(title="CodeAssess API", version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root_redirect():
    # Redirect root to the landing page for a better first impression
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


# Temporary Landing Page served from backend while frontend is rebuilt
@app.get("/landing", response_class=HTMLResponse)
def landing_page():
    return """
    <!doctype html>
    <html lang='en'>
      <head>
        <meta charset='utf-8'/>
        <meta name='viewport' content='width=device-width, initial-scale=1'/>
        <title>Flames Assess — Modern Coding Assessments</title>
        <style>
          :root { --bg: #0b0b10; --fg: #e2e8f0; --muted:#94a3b8; --brand:#7c3aed; --brand2:#06b6d4; }
          * { box-sizing: border-box }
          body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, Helvetica, Arial; color: var(--fg); background: radial-gradient(1200px 600px at 20% -10%, rgba(124,58,237,0.25), transparent), radial-gradient(1000px 500px at 120% 10%, rgba(6,182,212,0.2), transparent), var(--bg); }
          .container { max-width: 1120px; margin: 0 auto; padding: 24px }
          header { display:flex; align-items:center; justify-content:space-between; padding: 12px 0 }
          .logo { display:flex; align-items:center; gap:10px; font-weight:700; letter-spacing:.3px }
          .logo-badge{ width:34px;height:34px;border-radius:10px;background: linear-gradient(135deg, var(--brand), var(--brand2)); display:grid; place-items:center; color:white; font-weight:800 }
          nav { display:flex; gap: 18px; color: var(--muted) }
          nav a { text-decoration:none; color: inherit }
          .hero{ display:grid; grid-template-columns: 1.1fr .9fr; gap: 32px; align-items:center; padding: 48px 0 }
          h1 { font-size: clamp(36px, 6vw, 64px); line-height:1.02; margin: 0 0 14px }
          .gradient { background: linear-gradient(135deg, #fff, #e9d5ff 35%, #99f6e4 75%); -webkit-background-clip: text; background-clip:text; color: transparent }
          .kicker { color: var(--muted); font-weight:600; letter-spacing:.2em; text-transform:uppercase; font-size:12px }
          .subtitle{ color: var(--muted); max-width: 58ch; font-size: 18px }
          .cta{ display:flex; gap:12px; margin-top:22px }
          .btn{ padding:12px 16px; border-radius:10px; border:1px solid rgba(148,163,184,.2); color:#0b0b10; background:white; font-weight:700 }
          .btn.sec{ background: transparent; color: var(--fg) }
          .badge{ display:inline-flex; gap:8px; align-items:center; padding:6px 10px; background: rgba(124,58,237,.12); color:#e9d5ff; border: 1px solid rgba(124,58,237,.25); border-radius:999px; font-size:12px; font-weight:700 }
          .cardgrid{ display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin: 48px 0 0 }
          .card{ padding:18px; border:1px solid rgba(148,163,184,.2); border-radius:14px; background: rgba(255,255,255,.02) }
          .card h3{ margin:0 0 6px; font-size:18px }
          .card p{ margin:0; color: var(--muted) }
          footer{ padding: 48px 0; color: var(--muted); font-size:14px }
          @media (max-width: 900px){ .hero{ grid-template-columns: 1fr } .cardgrid{ grid-template-columns: 1fr } }
          .glow{ position: fixed; inset: -20% -10% auto auto; width: 40vw; height: 40vw; background: radial-gradient(circle at 30% 30%, rgba(124,58,237,.35), transparent 60%); filter: blur(40px); pointer-events:none; }
        </style>
      </head>
      <body>
        <div class="glow"></div>
        <div class="container">
          <header>
            <div class="logo">
              <div class="logo-badge">FA</div>
              Flames Assess
            </div>
            <nav>
              <a href="#features">Features</a>
              <a href="/app">Mini App</a>
              <a href="#contact">Contact</a>
            </nav>
          </header>

          <section class="hero">
            <div>
              <div class="kicker">Gen‑Z ready</div>
              <h1>
                A vibey coding assessment platform for teams, colleges and admins
                <span class="gradient">— fast, fair, and fun.</span>
              </h1>
              <p class="subtitle">Create beautiful, robust coding tests in minutes. Invite candidates, proctor securely, and get AI‑assisted insights that actually help you decide faster.</p>
              <div class="cta">
                <a class="btn" href="/health">Check API Health</a>
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

          <footer>
            © <span id="yr"></span> Flames Assess — All rights reserved.
          </footer>
        </div>
        <script>document.getElementById('yr').textContent = new Date().getFullYear()</script>
      </body>
    </html>
    """


# Minimal in-backend SPA to unblock preview while frontend is unavailable
@app.get("/app", response_class=HTMLResponse)
def mini_app():
    return """
    <!doctype html>
    <html lang='en'>
    <head>
        <meta charset='utf-8'/>
        <meta name='viewport' content='width=device-width, initial-scale=1'/>
        <title>Flames Assess — Mini App</title>
        <style>
            :root { --bg: #0b0b10; --fg: #e2e8f0; --muted:#94a3b8; --brand:#7c3aed; --brand2:#06b6d4; }
            body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, Helvetica, Arial; color: var(--fg); background: #0b0b10; }
            .wrap { max-width: 1040px; margin: 0 auto; padding: 24px }
            h1 { font-size: 28px; margin: 10px 0 22px }
            .row { display:flex; gap: 16px; align-items:flex-end; flex-wrap: wrap }
            input, textarea { background: rgba(255,255,255,.06); border:1px solid rgba(148,163,184,.25); color: var(--fg); border-radius: 10px; padding: 10px 12px; width: 280px }
            textarea { width: 420px; height: 90px }
            label { display:block; font-size:12px; color: var(--muted); margin: 0 0 6px }
            button { padding: 10px 14px; border-radius: 10px; background: linear-gradient(135deg, var(--brand), var(--brand2)); color: white; border: none; font-weight: 700; cursor: pointer }
            table { width: 100%; border-collapse: collapse; margin-top: 18px }
            th, td { border-bottom: 1px solid rgba(148,163,184,.2); text-align:left; padding: 10px }
            .muted { color: var(--muted) }
            .pill { display:inline-block; padding: 3px 8px; font-size: 12px; border-radius: 999px; background: rgba(124,58,237,.15); border:1px solid rgba(124,58,237,.35) }
            .topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom: 12px }
            a { color: #99f6e4; text-decoration: none }
        </style>
    </head>
    <body>
        <div class='wrap'>
            <div class='topbar'>
                <div><strong>Flames Assess</strong> <span class='muted'>— Mini App</span></div>
                <div><a href='/landing'>Landing</a> · <a href='/health'>Health</a> · <a href='/schema'>Schema</a></div>
            </div>

            <h1>Tests</h1>
            <div class='row'>
                <div>
                    <label>Title</label>
                    <input id='title' placeholder='e.g., Frontend Basics' />
                </div>
                <div>
                    <label>Difficulty</label>
                    <input id='difficulty' placeholder='easy | medium | hard' />
                </div>
                <div>
                    <label>Tags (comma separated)</label>
                    <input id='tags' placeholder='react, js, css' />
                </div>
            </div>
            <div style='margin-top:12px' class='row'>
                <div>
                    <label>Description</label>
                    <textarea id='desc' placeholder='Short description'></textarea>
                </div>
                <div>
                    <button id='createBtn'>Create Test</button>
                </div>
            </div>

            <div id='status' class='muted' style='margin:12px 0'>Ready.</div>

            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Difficulty</th>
                        <th>Tags</th>
                        <th>ID</th>
                    </tr>
                </thead>
                <tbody id='tbody'>
                    <tr><td colspan='4' class='muted'>Loading…</td></tr>
                </tbody>
            </table>
        </div>

        <script>
            const tbody = document.getElementById('tbody');
            const statusEl = document.getElementById('status');

            function setStatus(msg){ statusEl.textContent = msg; }

            async function fetchTests(){
                try{
                    setStatus('Fetching tests…');
                    const res = await fetch('/api/tests');
                    const data = await res.json();
                    renderRows(Array.isArray(data) ? data : []);
                    setStatus('Fetched ' + (Array.isArray(data) ? data.length : 0) + ' test(s).');
                }catch(e){
                    setStatus('Failed to fetch tests: ' + e.message);
                    tbody.innerHTML = "<tr><td colspan='4' class='muted'>Could not load tests</td></tr>";
                }
            }

            function renderRows(rows){
                if(!rows.length){
                    tbody.innerHTML = "<tr><td colspan='4' class='muted'>No tests yet — create one above.</td></tr>";
                    return;
                }
                tbody.innerHTML = rows.map(r => `
                    <tr>
                        <td>${r.title || '-'}</td>
                        <td><span class='pill'>${r.difficulty || '-'}</span></td>
                        <td>${Array.isArray(r.tags) ? r.tags.join(', ') : '-'}</td>
                        <td class='muted'>${r.id || r._id || '-'}</td>
                    </tr>
                `).join('');
            }

            async function createTest(){
                const title = document.getElementById('title').value.trim();
                const difficulty = document.getElementById('difficulty').value.trim() || 'easy';
                const tags = document.getElementById('tags').value.split(',').map(s => s.trim()).filter(Boolean);
                const description = document.getElementById('desc').value.trim();

                if(!title){
                    setStatus('Please enter a title.');
                    return;
                }

                const payload = {
                    title,
                    description,
                    difficulty,
                    tags,
                    questions: [],
                    created_by: 'demo@flames.assess',
                };
                try{
                    setStatus('Creating test…');
                    const res = await fetch('/api/tests', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
                    const data = await res.json();
                    if(res.ok){
                        setStatus('Created test ' + (data.id || '')); 
                        document.getElementById('title').value = '';
                        document.getElementById('difficulty').value = '';
                        document.getElementById('tags').value = '';
                        document.getElementById('desc').value = '';
                        fetchTests();
                    }else{
                        setStatus('Error: ' + (data.detail || JSON.stringify(data)));
                    }
                }catch(e){
                    setStatus('Failed to create test: ' + e.message);
                }
            }

            document.getElementById('createBtn').addEventListener('click', createTest);
            fetchTests();
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
