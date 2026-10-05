from flask import Flask, jsonify, render_template_string, request, redirect
import threading
import io
from contextlib import redirect_stdout
from brain.memory import (
    initialize_memory,
    recall_opportunities,
    recall_evidence,
    update_opportunity_status,
)

app = Flask(__name__)

@app.get("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")

@app.get("/service-worker.js")
def service_worker():
    response = app.send_static_file("service-worker.js")
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


robot_state = {
    "status": "ready",
    "message": "Hello! I am your AI Opportunity Robot.",
    "running": False,
    "result": None,
}

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#07111f">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="/manifest.json">
<title>AI Opportunity Robot</title>

<style>
*{box-sizing:border-box}

body{
    margin:0;
    background:
        radial-gradient(circle at top,#123452 0,#07111f 45%,#040912 100%);
    color:#edfaff;
    font-family:Arial,sans-serif;
}

main{
    max-width:850px;
    margin:auto;
    padding:20px;
}

.header{
    text-align:center;
    margin-bottom:18px;
}

.header h1{
    margin:0;
    color:#62e7ff;
    font-size:27px;
    letter-spacing:1px;
}

.header p{
    color:#8da9ba;
    margin:8px 0 0;
}

.robot-wrap{
    display:flex;
    justify-content:center;
    margin:22px 0;
}

.robot{
    width:190px;
    text-align:center;
}

.antenna{
    width:5px;
    height:25px;
    background:#55ddff;
    margin:auto;
    position:relative;
}

.antenna:after{
    content:"";
    position:absolute;
    width:13px;
    height:13px;
    border-radius:50%;
    background:#55ddff;
    top:-8px;
    left:-4px;
    box-shadow:0 0 18px #55ddff;
}

.head{
    height:125px;
    background:linear-gradient(145deg,#e3f7ff,#718fa8);
    border:4px solid #55ddff;
    border-radius:40px 40px 30px 30px;
    box-shadow:0 0 28px #087fa5;
    animation:bob 3s infinite ease-in-out;
}

.eyes{
    display:flex;
    justify-content:center;
    gap:30px;
    margin-top:30px;
}

.eye{
    width:27px;
    height:34px;
    border-radius:50%;
    background:#45e9ff;
    box-shadow:0 0 18px #45e9ff;
    animation:blink 5s infinite;
}

.mouth{
    width:48px;
    height:12px;
    border-bottom:4px solid #173d5b;
    border-radius:50%;
    margin:17px auto;
}

.body{
    width:125px;
    height:105px;
    margin:auto;
    background:linear-gradient(145deg,#d5efff,#577a9b);
    border:4px solid #55ddff;
    border-radius:23px;
    box-shadow:0 0 20px #087fa5;
}

.core{
    width:42px;
    height:42px;
    background:#45e9ff;
    border-radius:50%;
    margin:27px auto;
    box-shadow:0 0 25px #45e9ff;
    animation:pulse 1.5s infinite;
}

.panel{
    background:rgba(16,34,55,.92);
    border:1px solid #244965;
    border-radius:18px;
    padding:18px;
    margin-top:18px;
    box-shadow:0 12px 35px rgba(0,0,0,.25);
}

.status-row{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:12px;
}

.status{
    color:#67f5bb;
    font-weight:bold;
}

.status.thinking{
    color:#ffd166;
}

button{
    width:100%;
    padding:15px;
    margin-top:10px;
    border:0;
    border-radius:11px;
    background:#36d5ef;
    color:#061522;
    font-weight:bold;
    font-size:16px;
}

button:disabled{
    opacity:.45;
}

.hidden{
    display:none;
}

.opportunity{
    border:1px solid #32647c;
    border-radius:15px;
    padding:17px;
    margin-top:15px;
    background:rgba(7,20,34,.7);
}

.badge{
    display:inline-block;
    padding:6px 10px;
    border-radius:20px;
    background:#123f50;
    color:#62e7ff;
    font-size:12px;
    font-weight:bold;
}

.score{
    font-size:34px;
    color:#67f5bb;
    font-weight:bold;
    margin:8px 0;
}

.section{
    margin-top:18px;
}

.section h3{
    color:#62e7ff;
    margin-bottom:7px;
}

.section p{
    color:#d7e8f0;
    line-height:1.55;
}

.metric-grid{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:10px;
    margin-top:12px;
}

.metric{
    background:#0b1c2c;
    border:1px solid #244965;
    border-radius:11px;
    padding:12px;
}

.metric small{
    display:block;
    color:#7f9aaa;
    margin-bottom:5px;
}

.metric strong{
    color:#edfaff;
}

.loading{
    color:#ffd166;
    line-height:1.6;
}

.raw{
    white-space:pre-wrap;
    overflow-wrap:anywhere;
    color:#a9c1ce;
    font-size:13px;
    line-height:1.5;
}

@keyframes bob{
    0%,100%{transform:translateY(0)}
    50%{transform:translateY(-5px)}
}

@keyframes blink{
    0%,45%,49%,100%{transform:scaleY(1)}
    47%{transform:scaleY(.12)}
}

@keyframes pulse{
    50%{opacity:.55;box-shadow:0 0 40px #45e9ff}
}

@media(max-width:520px){
    main{padding:14px}
    .metric-grid{grid-template-columns:1fr}
}
</style>
</head>

<body>
<main>

<div class="header">
    <h1>🤖 AI OPPORTUNITY ROBOT</h1>
    <p>Discover problems. Find opportunities. Build businesses.</p>
</div>

<div class="robot-wrap">
<div class="robot">
    <div class="antenna"></div>
    <div class="head">
        <div class="eyes">
            <div class="eye"></div>
            <div class="eye"></div>
        </div>
        <div class="mouth"></div>
    </div>
    <div class="body">
        <div class="core"></div>
    </div>
</div>
</div>

<section class="panel">
    <div class="status-row">
        <h2>Robot status</h2>
        <span id="status" class="status">Ready</span>
    </div>

    <p id="message">Hello! I am your AI Opportunity Robot.</p>

    <button id="start" onclick="runRobot()">🔎 Start Opportunity Discovery</button>
    <button onclick="loadStatus()">↻ Refresh Status</button>
    <button onclick="speakRobot()">🔊 Speak</button>
    <button onclick="stopSpeaking()">⏹️ Stop</button>
</section>

<section class="panel">
    <h2>🏆 Opportunity Discovery</h2>

    <div id="empty">
        <p>Your robot has not discovered an opportunity yet.</p>
        <p>Start a discovery run and the robot will research real-world problems.</p>
    </div>

    <div id="loading" class="hidden loading">
        🤖 The robot is researching real-world problems...<br>
        🔎 Looking for repeated problems...<br>
        🧠 Analyzing unmet needs...<br>
        💡 Finding possible opportunities...
    </div>

    <div id="opportunity" class="hidden"></div>
</section>

</main>

<script>
let lastSpokenResult = '';

function speakText(text){
    if(!("speechSynthesis" in window)){
        return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;

    window.speechSynthesis.speak(utterance);
}

function speakRobot(){
    const message = document.getElementById('message').textContent;
    const opportunity = document.getElementById('opportunity');

    let text = message;

    if(opportunity && !opportunity.classList.contains('hidden')){
        text += '. ' + opportunity.innerText;
    }

    speakText(text);
}

function stopSpeaking(){
    if("speechSynthesis" in window){
        window.speechSynthesis.cancel();
    }
}

async function loadStatus(){
    try{
        const response = await fetch('/api/status');
        const data = await response.json();

        const status = document.getElementById('status');
        const message = document.getElementById('message');
        const start = document.getElementById('start');

        status.textContent =
            data.status === 'finished' ? 'Complete' :
            data.status === 'researching' ? 'Thinking...' :
            data.status === 'error' ? 'Error' : 'Ready';

        status.className =
            data.running ? 'status thinking' : 'status';

        message.textContent = data.message;
        start.disabled = data.running;

        if(data.running){
            document.getElementById('empty').classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');
        }

        if(data.result && !data.running){
            document.getElementById('empty').classList.add('hidden');
            document.getElementById('loading').classList.add('hidden');
            renderOpportunity(data.result);

            if(data.result !== lastSpokenResult){
                lastSpokenResult = data.result;
                speakText(
                    'Research complete. ' +
                    document.getElementById('opportunity').innerText
                );
            }
        }
    }catch(error){
        document.getElementById('message').textContent =
            'Cannot connect to the robot.';
    }
}

function escapeHtml(value){
    return String(value || '')
        .replace(/&/g,'&amp;')
        .replace(/</g,'&lt;')
        .replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;')
        .replace(/'/g,'&#039;');
}

function extractValue(text,label,nextLabel){
    const start = text.indexOf(label);
    if(start === -1) return '';

    let value = text.slice(start + label.length);

    if(nextLabel){
        const end = value.indexOf(nextLabel);
        if(end !== -1) value = value.slice(0,end);
    }

    return value.trim();
}

function renderOpportunity(raw){
    const title = extractValue(raw,'Title:','Problem:');
    const problem = extractValue(raw,'Problem:','Customer:');
    const customer = extractValue(raw,'Customer:','Solution:');
    const solution = extractValue(raw,'Solution:','Revenue:');
    const revenue = extractValue(raw,'Revenue:','Confidence:');
    const confidence = extractValue(raw,'Confidence:','\\n\\nWHY IT RANKED FIRST');

    const evidenceMatch = raw.match(/(\\d+) research evidence signals/);
    const evidence = evidenceMatch ? evidenceMatch[1] : '—';

    const confidencePercent =
        confidence && !isNaN(parseFloat(confidence))
        ? Math.round(parseFloat(confidence) * 100)
        : '—';

    document.getElementById('opportunity').innerHTML = `
        <div class="opportunity">

            <span class="badge">TOP OPPORTUNITY</span>

            <h2>${escapeHtml(title || 'Opportunity discovered')}</h2>

            <div class="score">
                ${confidencePercent}${confidencePercent !== '—' ? '%' : ''}
            </div>

            <div class="metric-grid">
                <div class="metric">
                    <small>Confidence</small>
                    <strong>${confidencePercent}${confidencePercent !== '—' ? '%' : ''}</strong>
                </div>

                <div class="metric">
                    <small>Evidence signals</small>
                    <strong>${escapeHtml(evidence)}</strong>
                </div>
            </div>

            <div class="section">
                <h3>🔴 The Problem</h3>
                <p>${escapeHtml(problem)}</p>
            </div>

            <div class="section">
                <h3>👥 Who Needs It</h3>
                <p>${escapeHtml(customer)}</p>
            </div>

            <div class="section">
                <h3>💡 What Could Be Built</h3>
                <p>${escapeHtml(solution)}</p>
            </div>

            <div class="section">
                <h3>💰 How It Could Make Money</h3>
                <p>${escapeHtml(revenue)}</p>
            </div>

            <div class="section">
                <h3>🧪 Robot's Next Test</h3>
                <p>
                    The robot recommends validating the problem with real
                    people before committing serious resources.
                </p>
            </div>

            <button onclick="showEvidence()">📰 View Research Evidence</button>
            <a href="/history" style="display:inline-block;margin-top:10px;padding:10px 14px;border-radius:10px;background:#123047;color:#7dd3fc;text-decoration:none;">📚 View Opportunity History</a>

            <div id="evidence" class="section hidden">
                <h3>Research Evidence</h3>
                <div class="raw">${escapeHtml(raw)}</div>
            </div>

        </div>
    `;
    document.getElementById('opportunity').classList.remove('hidden');
}

function showEvidence(){
    document.getElementById('evidence').classList.toggle('hidden');
}

async function runRobot(){
    document.getElementById('start').disabled = true;

    try{
        await fetch('/api/run',{method:'POST'});
        await loadStatus();
    }catch(error){
        document.getElementById('message').textContent =
            'Could not start research.';
    }
}

setInterval(loadStatus,3000);
loadStatus();
</script>

<script>
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/service-worker.js");
    });
}
</script>

</body>
</html>
"""

def run_research():
    try:
        from brain.robot import run_robot

        output = io.StringIO()

        with redirect_stdout(output):
            run_robot()

        robot_state["result"] = output.getvalue()
        robot_state["status"] = "finished"
        robot_state["message"] = "Research complete. The opportunity has been analyzed."

    except Exception as exc:
        robot_state["status"] = "error"
        robot_state["message"] = str(exc)

    finally:
        robot_state["running"] = False


@app.get("/")
def home():
    return render_template_string(HTML)


@app.get("/api/status")
def status():
    return jsonify(robot_state)


@app.post("/opportunity/<int:opportunity_id>/validate")
def validate_opportunity(opportunity_id):
    initialize_memory()

    opportunities = recall_opportunities()

    opportunity = next(
        (item for item in opportunities if item[0] == opportunity_id),
        None,
    )

    if opportunity is None:
        return "Opportunity not found", 404

    status = request.form.get("status", "").strip()
    notes = request.form.get("notes", "").strip()

    try:
        update_opportunity_status(opportunity_id, status, notes)
    except ValueError:
        return "Invalid validation status", 400

    return redirect(f"/opportunity/{opportunity_id}")


@app.get("/opportunity/<int:opportunity_id>")
def opportunity_detail(opportunity_id):
    initialize_memory()
    opportunities = recall_opportunities()

    opportunity = next(
        (item for item in opportunities if item[0] == opportunity_id),
        None,
    )

    if opportunity is None:
        return "Opportunity not found", 404

    (
        opportunity_id,
        title,
        problem,
        solution,
        target_customer,
        revenue_potential,
        confidence,
        status,
        notes,
        created_at,
    ) = opportunity

    evidence = recall_evidence(opportunity_id)

    evidence_cards = ""

    for index, item in enumerate(evidence, start=1):
        query, evidence_title, link, description, published = item

        evidence_cards += f"""
        <div style="background:#0d1b2a;border:1px solid #23435f;border-radius:14px;padding:18px;margin-bottom:14px">
            <h3 style="margin-top:0">{index}. {evidence_title}</h3>
            <p><strong>Query:</strong> {query}</p>
            <p><strong>Published:</strong> {published}</p>
            <p>{description}</p>
            <p><a href="{link}" target="_blank" rel="noopener noreferrer">Open source →</a></p>
        </div>
        """

    if not evidence_cards:
        evidence_cards = """
        <div style="background:#0d1b2a;border:1px solid #23435f;border-radius:14px;padding:18px">
            No research evidence has been saved for this opportunity.
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <style>
            body {{
                margin:0;
                background:#040912;
                color:#edfaff;
                font-family:Arial,sans-serif;
            }}
            main {{
                max-width:850px;
                margin:auto;
                padding:20px;
            }}
            a {{
                color:#7dd3fc;
                text-decoration:none;
            }}
            .card {{
                background:#0d1b2a;
                border:1px solid #23435f;
                border-radius:14px;
                padding:18px;
                margin-bottom:14px;
            }}
        </style>
    </head>
    <body>
        <main>
            <p><a href="/history">← Back to Opportunity History</a></p>
            <h1>{title}</h1>

            <div class="card">
                <p><strong>Problem:</strong> {problem}</p>
                <p><strong>Customer:</strong> {target_customer}</p>
                <p><strong>Solution:</strong> {solution}</p>
                <p><strong>Revenue:</strong> {revenue_potential}</p>
                <p><strong>Confidence:</strong> {confidence:.0%}</p>
                <p><strong>Status:</strong> {status}</p>
                <p><strong>Created:</strong> {created_at}</p>
                <p><strong>Notes:</strong> {notes}</p>
            </div>

            <div class="card">
                <h2>🔎 Validation</h2>
                <p>Update the validation stage and record what you learned.</p>

                <form method="post" action="/opportunity/{opportunity_id}/validate">
                    <label for="status"><strong>Status</strong></label>
                    <select
                        id="status"
                        name="status"
                        style="display:block;width:100%;margin:8px 0 14px;padding:10px;border-radius:8px;background:#07111d;color:#edfaff;border:1px solid #23435f;"
                    >
                        <option value="new" {"selected" if status == "new" else ""}>New</option>
                        <option value="validating" {"selected" if status == "validating" else ""}>Validating</option>
                        <option value="validated" {"selected" if status == "validated" else ""}>Validated</option>
                        <option value="rejected" {"selected" if status == "rejected" else ""}>Rejected</option>
                    </select>

                    <label for="notes"><strong>Validation notes</strong></label>
                    <textarea
                        id="notes"
                        name="notes"
                        rows="5"
                        placeholder="Record interviews, tests, customer feedback, pricing evidence, or reasons for rejection..."
                        style="display:block;width:100%;box-sizing:border-box;margin:8px 0 14px;padding:10px;border-radius:8px;background:#07111d;color:#edfaff;border:1px solid #23435f;"
                    >{notes}</textarea>

                    <button
                        type="submit"
                        style="padding:11px 16px;border:0;border-radius:9px;background:#123047;color:#7dd3fc;cursor:pointer;"
                    >
                        Save Validation
                    </button>
                </form>
            </div>

            <h2>📰 Research Evidence</h2>
            {evidence_cards}
        </main>
    </body>
    </html>
    """


@app.get("/history")
def history():
    initialize_memory()
    opportunities = recall_opportunities()

    rows = []
    for item in opportunities:
        (
            opportunity_id,
            title,
            problem,
            solution,
            target_customer,
            revenue_potential,
            confidence,
            status,
            notes,
            created_at,
        ) = item

        evidence = recall_evidence(opportunity_id)

        rows.append({
            "id": opportunity_id,
            "title": title,
            "problem": problem,
            "solution": solution,
            "target_customer": target_customer,
            "revenue_potential": revenue_potential,
            "confidence": confidence,
            "status": status,
            "notes": notes,
            "created_at": created_at,
            "evidence_count": len(evidence),
        })

    cards = ""

    for item in rows:
        cards += f"""
        <div style="background:#0d1b2a;border:1px solid #23435f;border-radius:14px;padding:18px;margin-bottom:14px">
            <h2 style="margin-top:0"><a href="/opportunity/{item["id"]}">{item["title"]}</a></h2>
            <p><strong>Problem:</strong> {item["problem"]}</p>
            <p><strong>Customer:</strong> {item["target_customer"]}</p>
            <p><strong>Solution:</strong> {item["solution"]}</p>
            <p><strong>Revenue:</strong> {item["revenue_potential"]}</p>
            <p><strong>Confidence:</strong> {item["confidence"]:.0%}</p>
            <p><strong>Evidence:</strong> {item["evidence_count"]} signals</p>
            <p><strong>Created:</strong> {item["created_at"]}</p>
            <p><a href="/opportunity/{item["id"]}">View full opportunity →</a></p>
        </div>
        """

    if not cards:
        cards = """
        <div style="background:#0d1b2a;border:1px solid #23435f;border-radius:14px;padding:18px">
            No saved opportunities yet. Run an opportunity discovery first.
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Opportunity History</title>
        <style>
            body {{
                margin:0;
                background:#040912;
                color:#edfaff;
                font-family:Arial,sans-serif;
            }}
            main {{
                max-width:850px;
                margin:auto;
                padding:20px;
            }}
            a {{
                color:#7dd3fc;
                text-decoration:none;
            }}
        </style>
    </head>
    <body>
        <main>
            <p><a href="/">← Back to Robot</a></p>
            <h1>📚 Opportunity History</h1>
            <p>Saved discoveries from the robot's memory.</p>
            {cards}
        </main>
    </body>
    </html>
    """

@app.post("/api/run")
def start_robot():
    if not robot_state["running"]:
        robot_state["running"] = True
        robot_state["status"] = "researching"
        robot_state["message"] = "The robot is researching opportunities."

        threading.Thread(
            target=run_research,
            daemon=True
        ).start()

    return jsonify({"message": robot_state["message"]})


if __name__ == "__main__":
    import os

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
