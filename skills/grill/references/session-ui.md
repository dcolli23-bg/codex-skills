# Grill session UI

For decisions better answered in a browser, write a compact session JSON to `$CODEX_HOME/grill/sessions/<task>.json`:

```json
{"title":"Decision pass","status":"open","questions":[{"id":"scope","question":"What must be decided?","recommendation":"Concrete default.","tradeoff":"Strongest competing preference.","decision":null,"answer":""}]}
```

Start `scripts/serve_grill.py SESSION --port 8771`, give the user the local URL, and remain available. Each question offers `use`, `clarify`, or `reject`; only clarification and rejection require text. Answers autosave. Submission locks the page until the user revokes it.

When the user says they are done, read the session file. Stop the server after reading the completed session. Do not ask the user to copy responses into chat.
