
<!--
  Run ID: e7586812-3531-4961-b8a7-9963cf879463
  Timestamp: 2026-06-21T04:38:08.943592
  Settings Module: config.settings.test
  Database: django.db.backends.sqlite3 / file:memorydb_default?mode=memory&cache=shared
  Git Tree Identifier: working_tree
  Source Evidence: workflow_transitions.json
-->
# State Propagation Audit

## System Propagation Rules
1. **User Identity Profile updates**: first_name and last_name updates instantly propagate to navbar displays.
2. **Lead Conversion**: Automatically creates Student object and maps relevant name, email, phone.
3. **Session Completion**: Prevents any new enrollments under that session.
