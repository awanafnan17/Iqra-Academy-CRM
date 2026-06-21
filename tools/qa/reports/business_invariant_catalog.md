
<!--
  Run ID: e7586812-3531-4961-b8a7-9963cf879463
  Timestamp: 2026-06-21T04:38:08.943592
  Settings Module: config.settings.test
  Database: django.db.backends.sqlite3 / file:memorydb_default?mode=memory&cache=shared
  Git Tree Identifier: working_tree
  Source Evidence: field_ledger.json
-->
# Business Invariant Catalog

- **Roll Prefix Uniqueness**: Checked on Session creation.
- **Passing Marks Bound**: Cannot exceed total marks on Exam creation.
- **Refund Upper Limit**: Cumulative refunds cannot exceed original Payment amount.
