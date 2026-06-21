
<!--
  Run ID: e7586812-3531-4961-b8a7-9963cf879463
  Timestamp: 2026-06-21T04:38:08.943592
  Settings Module: config.settings.test
  Database: django.db.backends.sqlite3 / file:memorydb_default?mode=memory&cache=shared
  Git Tree Identifier: working_tree
  Source Evidence: detector_canaries.json, visual_evidence.json
-->
# Behavioral Defect Report — Iqra Academy CRM

## Discovery Summary
| Metric | Count |
|--------|-------|
| Total recomputed fields | 428 |
| Mutation-tested passed | 47 |
| Confirmed failed | 34 |
| Invalid fixture | 8 |
| Explicitly untestable | 1 |
| Excluded with reason | 338 |
| Requires business decision | 0 |
| **Discovery Status** | **DISCOVERY_COMPLETE** |

## Confirmed Visual Findings (Repair Batch Excluded)
- **VIS-001**: Login Page layout overflow caused by absolute positioning overlay elements.
- **VIS-002**: Permission Matrix submit button position pushed far below screen.
- **VIS-003**: charts.js console error 'Failed to fetch' analytics endpoint during redirect/logout.
