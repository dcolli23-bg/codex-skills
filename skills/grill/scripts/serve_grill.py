#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Grill</title><style>
:root{color-scheme:dark;font:14px system-ui;background:#141414;color:#eee}*{box-sizing:border-box}body{margin:0;padding:20px}main{max-width:780px;margin:auto}
header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px}h1{font-size:18px;margin:0}.status{color:#888;font-size:12px}.grid{display:grid;gap:10px}
.card{border:1px solid #333;background:#1b1b1b;padding:14px}.number{color:#777;font-size:11px;letter-spacing:.08em;text-transform:uppercase}.question{font-size:16px;font-weight:650;margin:5px 0 12px}
.label{color:#888;font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin-top:9px}.text{margin-top:3px;line-height:1.45}.tradeoff{color:#aaa}
.actions{display:flex;flex-wrap:wrap;gap:7px;margin-top:13px}.choice,.submit,.revoke{border:1px solid #555;background:#252525;color:#bbb;padding:7px 10px;cursor:pointer}.choice:hover,.submit:hover,.revoke:hover{border-color:#888;background:#303030;color:#eee}.choice.selected{border-color:#8cb99a;color:#b9e4c5;background:#203026}.choice.reject.selected{border-color:#b98181;color:#efb5b5;background:#332222}.choice:active,.submit:active,.revoke:active{transform:translateY(1px)}
textarea{width:100%;min-height:62px;margin-top:9px;padding:9px;border:1px solid #444;background:#151515;color:#eee;font:inherit;resize:vertical}textarea:focus{outline:2px solid #8ebfe0;outline-offset:1px}.footer{display:flex;justify-content:flex-end;align-items:center;gap:10px;margin-top:14px}.submit{font-weight:650}.submitted{color:#9bd0aa;font-weight:650}.revoke{color:#aaa}.locked .choice,.locked textarea{pointer-events:none;opacity:.58}
</style></head><body><main><header><h1 id="title">Grill</h1><span class="status" id="status"></span></header><div class="grid" id="questions"></div><div class="footer" id="footer"></div></main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let session,timer;
async function save(){document.querySelector('#status').textContent='Saving…';const r=await fetch('/api/session',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(session)});if(!r.ok)throw Error(await r.text());document.querySelector('#status').textContent=session.status==='complete'?'Submitted':'Saved'}
function schedule(){clearTimeout(timer);timer=setTimeout(()=>save().catch(e=>document.querySelector('#status').textContent=e.message),250)}
function choose(index,decision){session.questions[index].decision=decision;if(decision==='use')session.questions[index].answer='';render();schedule()}
function render(){const locked=session.status==='complete';document.querySelector('#title').textContent=session.title||'Grill';document.querySelector('#status').textContent=locked?'Submitted':'Ready';document.querySelector('#questions').classList.toggle('locked',locked);document.querySelector('#questions').innerHTML=session.questions.map((q,i)=>`<section class="card"><div class="number">Decision ${i+1}</div><div class="question">${esc(q.question)}</div><div class="label">Recommendation</div><div class="text">${esc(q.recommendation)}</div><div class="label">Why you may disagree</div><div class="text tradeoff">${esc(q.tradeoff)}</div><div class="actions"><button class="choice ${q.decision==='use'?'selected':''}" type="button" onclick="choose(${i},'use')">Accept</button><button class="choice ${q.decision==='clarify'?'selected':''}" type="button" onclick="choose(${i},'clarify')">Clarify</button><button class="choice reject ${q.decision==='reject'?'selected':''}" type="button" onclick="choose(${i},'reject')">Reject</button></div>${q.decision==='clarify'||q.decision==='reject'?`<textarea data-index="${i}" placeholder="${q.decision==='clarify'?'Clarification…':'Preferred decision…'}">${esc(q.answer||'')}</textarea>`:''}</section>`).join('');document.querySelectorAll('textarea').forEach(area=>area.oninput=()=>{session.questions[Number(area.dataset.index)].answer=area.value;schedule()});document.querySelector('#footer').innerHTML=locked?'<span class="submitted">Submitted</span><button class="revoke" type="button" id="revoke">Revoke submission</button>':'<button class="submit" type="button" id="submit">Submit</button>';if(locked)document.querySelector('#revoke').onclick=async()=>{session.status='open';await save();render()};else document.querySelector('#submit').onclick=async()=>{session.status='complete';await save();render()}}
fetch('/api/session',{cache:'no-store'}).then(r=>r.json()).then(x=>{session=x;render()});
</script></body></html>"""


def validate_session(data: object) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        raise ValueError("session must contain a questions list")
    clean = {
        "title": str(data.get("title", "Grill")),
        "status": str(data.get("status", "open")),
        "questions": [],
    }
    if clean["status"] not in {"open", "complete"}:
        raise ValueError("status must be open or complete")
    for index, item in enumerate(data["questions"]):
        if not isinstance(item, dict) or not item.get("question"):
            raise ValueError(f"question {index + 1} is invalid")
        decision = item.get("decision")
        if decision is None:
            if item.get("use_recommendation"):
                decision = "use"
            elif item.get("answer"):
                decision = "clarify"
        if decision not in {None, "use", "clarify", "reject"}:
            raise ValueError(f"question {index + 1} has an invalid decision")
        clean["questions"].append(
            {
                "id": str(item.get("id", index + 1)),
                "question": str(item["question"]),
                "recommendation": str(item.get("recommendation", "")),
                "tradeoff": str(item.get("tradeoff", "")),
                "decision": decision,
                "answer": "" if decision == "use" else str(item.get("answer", "")),
            }
        )
    return clean


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def handler(path: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_get(self):
            if self.path == "/api/session":
                body = json.dumps(
                    validate_session(json.loads(path.read_text(encoding="utf-8")))
                ).encode()
                kind = "application/json"
            elif self.path in {"/", "/index.html"}:
                body = PAGE.encode()
                kind = "text/html; charset=utf-8"
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_post(self):
            if self.path != "/api/session":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                data = validate_session(json.loads(self.rfile.read(size)))
                atomic_write(path, data)
                body = b"ok"
                self.send_response(HTTPStatus.OK)
            except Exception as exc:
                body = str(exc).encode()
                self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *_args):
            return

        do_GET = do_get
        do_POST = do_post

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve a file-backed Grill decision session"
    )
    parser.add_argument("session", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8771)
    args = parser.parse_args()
    validate_session(json.loads(args.session.read_text(encoding="utf-8")))
    server = ThreadingHTTPServer(
        (args.host, args.port), handler(args.session.resolve())
    )
    print(f"http://{args.host}:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
