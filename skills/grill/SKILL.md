---
name: grill
description: Run a concise decision pass before implementation. Use when the user says "grill" or "decision pass," or asks which unresolved decisions must be made to unblock work.
---

# Grill

Surface only material decisions the user needs to make before work can proceed.

1. Resolve facts from available code, documentation, and tests instead of asking the user.
2. Identify up to five choices that materially affect scope, contracts, UX, risk, or architecture. Do not inflate the count.
3. Order them from most to least likely to draw disagreement.
4. For each, provide a compact question, one concrete recommended default, and the strongest competing preference.
5. Use [references/session-ui.md](references/session-ui.md) when the user wants to answer through a browser.

Reserve the list for decisions the user owns. If nothing material remains, present the settled plan for approval. Continue refining until the user approves; approval ends the Grill session.
