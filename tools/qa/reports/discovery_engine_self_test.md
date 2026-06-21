# QA Discovery Engine Self-Test (Canary Run)

**Run ID**: e7586812-3531-4961-b8a7-9963cf879463  
**Timestamp**: 2026-06-21T04:38:08.943592  
**Settings Module**: `config.settings.test`  
**Database**: `django.db.backends.sqlite3` / `file:memorydb_default?mode=memory&cache=shared`  

## Canary Detection Matrix

| Canary Scenario | Defect Layer | Status | Expected Classification |
|-----------------|--------------|--------|-------------------------|
| abandoned_commit_false | view | ✅ DETECTED | `abandoned_commit_false` |
| abandoned_commit_control | view | ✅ DETECTED | `abandoned_commit_control` |
| mismatched_input_name | form | ✅ DETECTED | `mismatched_input_name` |
| matched_name_control | form | ✅ DETECTED | `matched_name_control` |
| missing_save_call | view | ✅ DETECTED | `missing_save_call` |
| missing_save_control | view | ✅ DETECTED | `missing_save_control` |
| missing_save_m2m | view | ✅ DETECTED | `missing_save_m2m` |
| missing_m2m_control | view | ✅ DETECTED | `missing_m2m_control` |
| missing_update_instance | view | ✅ DETECTED | `missing_update_instance` |
| missing_instance_control | view | ✅ DETECTED | `missing_instance_control` |
| omitted_update_fields | model | ✅ DETECTED | `omitted_update_fields` |
| omitted_fields_control | model | ✅ DETECTED | `omitted_fields_control` |
| overwriting_signal | signal | ✅ DETECTED | `overwriting_signal` |
| overwriting_signal_control | signal | ✅ DETECTED | `overwriting_signal_control` |

## Instrumentation Validation

- Checked matched name controls: **✅ Verified**
- Checked normal commit save: **✅ Verified**
- Instrumentation side-effect audit: **✅ 100% No Side-Effects Passed**

**Engine trust status**: **PASSED**