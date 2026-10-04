from flask import Flask, jsonify, render_template_string
import threading
import time

app = Flask(__name__)

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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Opportunity Robot</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#07111f;color:#eaf7ff;font-family:Arial,sans-serif}
main{max-width:760px;margin:auto;padding:20px}
h1{text-align:center;color:#62e7ff;font-size:25px}
.robot{width:230px;margin:25px auto;text-align:center}
.antenna{width:5px;height:28px;background:#55ddff;margin:auto;position:relative}
.antenna:after{content:"";position:absolute;width:14px;height:14px;border-radius:50%;background:#55ddff;top:-9px;left:-4px;box-shadow:0 0 18px #55ddff}
.head{height:145px;background:linear-gradient(145deg,#d8f5ff,#7799b8);border:5px solid #55ddff;border-radius:45px 45px 35px 35px;box-shadow:0 0 28px #087fa5;animation:bob 3s infinite ease-in-out}
.eyes{display:flex;justify-content:center;gap:35px;margin-top:34px}
.eye{width:31px;height:38px;border-radius:50%;background:#45e9ff;box-shadow:0 0 18px #45e9ff;animation:blink 5s infinite}
.mouth{width:55px;height:13px;border-bottom:5px solid #173d5b;border-radius:50%;margin:20px auto}
.neck{width:35px;height:22px;background:#668ca7;margin:auto}
.body{width:145px;height:120px;margin:auto;background:linear-gradient(145deg,#d5efff,#577a9b);border:4px solid #55ddff;border-radius:25px;position:relative;box-shadow:0 0 20px #087fa5}
.core{width:48px;height:48px;background:#45e9ff;border-radius:50%;margin:30px auto;box-shadow:0 0 25px #45e9ff;animation:pulse 1.5s infinite}
.arm{position:absolute;width:25px;height:80px;background:#9fc4dc;border:3px solid #55ddff;border-radius:18px;top:15px}
.arm.left{left:-33px;transform-origin:top;animation:wave 2s infinite ease-in-out}
.arm.right{right:-33px}
.legs{display:flex;justify-content:center;gap:24px}
.leg{width:38px;height:68px;background:#829eb6;border:3px solid #55ddff;border-radius:12px}
.feet{display:flex;justify-content:center;gap:14px}
.foot{width:58px;height:20px;background:#5c7e9b;border:2px solid #55ddff;border-radius:12px}
.panel{background:#102237;border:1px solid #244965;border-radius:16px;padding:18px;margin-top:20px}
.status{color:#67f5bb;font-weight:bold}
button{width:100%;padding:15px;margin-top:10px;border:0;border-radius:10px;background:#36d5ef;color:#061522;font-weight:bold;font-size:16px}
button:disabled{opacity:.5}
.result{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.5}
@keyframes bob{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-5px) rotate(2deg)}}
@keyframes blink{0%,45%,49%,100%{transform:scaleY(1)}47%{transform:scaleY(.12)}}
@keyframes pulse{50%{opacity:.55;box-shadow:0 0 40px #45e9ff}}
@keyframes wave{0%,100%{transform:rotate(8deg)}50%{transform:rotate(-22deg)}}
</style>
</head>
<body>
<main>
<h1>AI OPPORTUNITY ROBOT</h1>
<div class="robot">
<div class="antenna"></div>
<div class="head"><div class="eyes"><div class="eye"></div><div class="eye"></div></div><div class="mouth"></div></div>
<div class="neck"></div>
<div class="body"><div class="arm left"></div><div class="arm right"></div><div class="core"></div></div>
<div class="legs"><div class="leg"></div><div class="leg"></div></div>
<div class="feet"><div class="foot"></div><div class="foot"></div></div>
</div>
<section class="panel">
<h2>Robot status</h2>
<p id="status" class="status">Ready</p>
<p id="message">Hello! I am your AI Opportunity Robot.</p>
<button id="start" onclick="runRobot()">Start Research</button>
<button onclick="loadStatus()">Refresh Status</button>
</section>
<section class="panel">
<h2>Discovery results</h2>
<div id="result" class="result">Your discoveries will appear here.</div>
</section>
</main>
<script>
async function loadStatus(){
 try{
  const r=await fetch('/api/status');
  const d=await r.json();
  document.getElementById('status').textContent=d.status;
  document.getElementById('message').textContent=d.message;
  if(d.result)document.getElementById('result').textContent=d.result;
  document.getElementById('start').disabled=d.running;
 }catch(e){document.getElementById('message').textContent='Cannot connect to robot.'}
}
async function runRobot(){
 document.getElementById('start').disabled=true;
 document.getElementById('status').textContent='Thinking...';
 document.getElementById('message').textContent='Searching for opportunities. Please wait.';
 document.getElementById('result').textContent='Research is running...';
 try{
  const r=await fetch('/api/run',{method:'POST'});
  const d=await r.json();
  document.getElementById('message').textContent=d.message;
 }catch(e){document.getElementById('message').textContent='Could not start research.'}
 await loadStatus();
}
setInterval(loadStatus,3000);
loadStatus();
</script>
</body>
</html>
"""

def run_research():
    try:
        from brain.robot import run_robot
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        with redirect_stdout(output):
            run_robot()

        robot_state["result"] = output.getvalue()
        robot_state["status"] = "finished"
        robot_state["message"] = "Research complete. Here are the results."
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

@app.post("/api/run")
def start_robot():
    if not robot_state["running"]:
        robot_state["running"] = True
        robot_state["status"] = "researching"
        robot_state["message"] = "The robot is researching opportunities."
        threading.Thread(target=run_research, daemon=True).start()
    return jsonify({"message": robot_state["message"]})

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
