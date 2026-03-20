# TODO Steps: Fix Web Admin Root Redirect to ADA V1
Status: [ ] Not started | [ ] In progress | [x] Pending execution | [ ] Done

## Steps
1. [x] Plan approved - Root `/` → AppV1, `/v2/*` → AppV2
2. [x] Edit `web-admin/frontend/src/main.jsx` - Swap routes ✅
3. [x] Rebuild frontend: `cd web-admin/frontend && npm run build` ✅ (vite build complete)
4. [x] Restart service: `docker compose restart chat_interface` ✅
5. [ ] Test: `open http://localhost:8080/` loads V1; `/v2/developer` loads V2
6. [ ] Complete task
