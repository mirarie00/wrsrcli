# wrsrcli — Progress

Log entry at the start and end of each phase in `EXECUTION-PLAN.md`, per
`REPO-STRUCTURE.md`. An end-of-phase entry is written only once that
phase's "Verify" step has been run and passed.

|Date|Time|Note|
|---|---|---|
|2026-09-19|23:22|Phase 0 started.|
|2026-09-19|23:23|Phase 0 finished. Verify passed: `wrsrcli --help` lists all 10 subcommands. Total development time this phase: 00:01.|
|2026-09-19|23:23|Phase 1 started.|
|2026-09-19|23:24|Phase 1 finished. Verify passed: api store/inspect/remove cycle; `path --auto-detect` resolved game path via appmanifest installdir to `...\common\SovietRepublic`; `path --game` override and directory validation. D-002 recorded. Total development time this phase: 00:01.|
|2026-09-19|23:24|Phase 2 started.|
|2026-09-19|23:26|Phase 2 finished. Verify passed: `.acf` fields hand-checked against raw for item 3621284903; SPEC 2.2 sample 3779842468 reproduced field-for-field; all 20 `workshopconfig.ini` files parse with `$ITEM_ID` matching folder name. Total development time this phase: 00:02.|
|2026-09-19|23:26|Phase 3 blocked pending decisions on open item #3 (manifest.json location) and the item-without-workshopconfig.ini case. Awaiting input.|
|2026-09-19|23:40|Phase 3 started (unblocked; D-003, D-004, D-005 recorded and SPEC 2.2/4.1/6 updated).|
|2026-09-19|23:40|Phase 3 finished. Verify passed: `wrsrcli scan` wrote 21 entries to `%APPDATA%\wrsrcli\manifest.json`; item 3780739284's `date_updated`/`date_touched` hand-checked against raw `.acf`; item 3780813529 included with null fields plus warning per D-005. Total development time this phase: 00:00.|

|2026-09-19|23:41|Phase 4 started (D-006 recorded; SPEC 4.2 column list updated).|
|2026-09-19|23:44|Phase 4 finished. Verify passed: verbatim no-API message; save prompt incl. ENTER-to-Documents default; collision prompt both branches with `WRSR Assets YYYY-MM-DD HH-mm.html` timestamp; HTML has zero external references; search, type filter, text sort (asc/desc) and numeric date sort all exercised in a browser against the real 21-item dataset. Total development time this phase: 00:03.|
|2026-09-19|23:44|Phase 5 blocked: requires a Steam Web API key, which is not set. Awaiting input.|
|2026-09-19|23:45|Phase 5 started (code-only, by agreement; verification deferred until a key is available).|
|2026-09-19|23:47|Phase 5 **code complete, UNVERIFIED — phase NOT finished.** Both endpoints implemented, enrichment wired into `output-table`, D-007 recorded. Offline checks passed (8-column API render, author fallback, D-007 degradation, key absent from output, no-API regression). The live `GetPublishedFileDetails`/`GetPlayerSummaries` calls have never been executed — Phase 5's Verify step remains outstanding and requires a stored API key. Development time so far this phase: 00:02.|

|2026-09-19|23:48|Phase 6 started (D-008 recorded, closing open item #4; SPEC 3 and 6 updated).|
|2026-09-19|23:50|Phase 6 finished. Verify passed: verbatim prompt; only ENTER proceeds and a non-empty reply downloads nothing; `--path` without `--install` and bare `steamcmd` are usage errors; the default path short-circuits, leaving the existing install untouched. Installed to a throwaway path — 774,825 bytes downloaded, self-bootstrapped to client version 1788292693, then downloaded workshop item 3780739284 anonymously (712,541 bytes, matching the `.acf` size) with all 5 files SHA256-identical to the installed copy. Total development time this phase: 00:02.|

|2026-09-19|23:51|Phases 7 and 8 started together (D-009 closing open item #5, and D-010 for copy-overlap mechanics; SPEC 4.3, 5 and 6 updated).|
|2026-09-19|23:52|Phases 7 and 8 finished. Verify passed: 22 checks in a sandbox (APPDATA redirected, disposable game/workshop fixtures, real config and game folder never touched). Covered the conflict prompt, `*`/directory/file sources, `[GAME]` and `[WORKSHOP]/{id}/` destinations, removals of files and folders, absent targets warning without failing, backup-before-write for both actions, `restore` returning a destination's file byte-for-byte, `rollback` undoing both overwrites and removals, the multi-generation prompt with ENTER-cancel and re-prompt on bad input. Found and fixed a same-second run-stamp collision that would have let one generation overwrite another's backups. Total development time this phase: 00:01.|

Total development time across all phases: 00:12.
