# HANDOFF

## Completed (Stage 1: fix Start button)
- Cause: in `web.py`, `extractSection()` (inside the `HTML = """..."""` string) used `'\n'`.
  Python turned that into a real line break inside a JS string, which is a SyntaxError.
  The whole `<script>` block failed to load, so `runRobot()` never existed and the
  "Start Opportunity Discovery" button did nothing.
- Fix: changed both `'\n'` to `'\\n'` (lines ~689 and ~692). Nothing else was changed.
- Verified: served JS passes `node --check`; `/`, `/api/status` return 200.

## Next steps
1. Run `python web.py`, open the page, click the button, confirm status goes to "Thinking...".
2. Needs internet: `brain/research.py` pulls Google News RSS. With no network the run
   ends as "Complete" but with an empty result (not changed, per "fix only the button").
3. Hard-refresh once (or clear the site data) so the service worker serves the new page.
