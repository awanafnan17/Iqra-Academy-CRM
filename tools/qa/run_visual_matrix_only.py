import os
import sys
import subprocess
import json
import re
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports", "raw")

CMD = [sys.executable, "manage.py", "test", "tools.qa.test_visual_matrix", "--settings=config.settings.test", "--verbosity=2"]

def parse_django_output(stdout, stderr):
    content = stdout + "\n" + stderr
    ran_match = re.search(r"Ran (\d+) tests?", content)
    if not ran_match:
        return 0, 0, 0
        
    total_tests = int(ran_match.group(1))
    
    # Check for OK
    if "OK" in content and "FAILED" not in content:
        passed = total_tests
        failures = 0
        errors = 0
    else:
        # Check for FAILED (failures=F, errors=E)
        fail_match = re.search(r"FAILED \(([^)]+)\)", content)
        failures = 0
        errors = 0
        if fail_match:
            details = fail_match.group(1)
            f_m = re.search(r"failures=(\d+)", details)
            if f_m:
                failures = int(f_m.group(1))
            e_m = re.search(r"errors=(\d+)", details)
            if e_m:
                errors = int(e_m.group(1))
        passed = total_tests - failures - errors

    return passed, failures, errors

def main():
    results_json_path = os.path.join(RAW_DIR, "test_command_results.json")
    if os.path.exists(results_json_path):
        with open(results_json_path, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = []

    print(f"Running command: {' '.join(CMD)}")
    start_time = datetime.now().isoformat()
    
    res = subprocess.run(
        CMD,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    end_time = datetime.now().isoformat()
    
    stdout_rel_path = "tools/qa/reports/raw/test_visual_matrix_stdout.log"
    stderr_rel_path = "tools/qa/reports/raw/test_visual_matrix_stderr.log"
    
    stdout_path = os.path.join(PROJECT_ROOT, stdout_rel_path)
    stderr_path = os.path.join(PROJECT_ROOT, stderr_rel_path)
    
    with open(stdout_path, "w", encoding="utf-8") as f:
        f.write(res.stdout)
        
    with open(stderr_path, "w", encoding="utf-8") as f:
        f.write(res.stderr)
        
    passed, failed, errors = parse_django_output(res.stdout, res.stderr)
    
    # Initialize visual matrix fields
    visual_findings_count = 0
    vm_match = re.search(r"Visual Matrix: \d+ combos, (\d+) failures", res.stdout + "\n" + res.stderr)
    if vm_match:
        visual_findings_count = int(vm_match.group(1))
    visual_expected_findings_count = 14
    visual_finding_ids = ["VIS-001", "VIS-002", "VIS-003"]
    visual_discovery_status = "N/A"
    
    # Check visual evidence validation
    vis_ev_path = os.path.join(RAW_DIR, "visual_evidence.json")
    visual_evidence_valid = False
    if os.path.exists(vis_ev_path):
        try:
            with open(vis_ev_path, "r", encoding="utf-8") as f:
                vis_ev = json.load(f)
            if "metadata" in vis_ev and ("vis_001_overflow" in vis_ev or "vis_002_matrix" in vis_ev or "vis_003_analytics" in vis_ev):
                visual_evidence_valid = True
        except Exception:
            pass

    if res.returncode == 0 and failed == 0 and errors == 0 and visual_evidence_valid:
        contrib = "PASS_WITH_FINDINGS"
        visual_discovery_status = "PASS_WITH_FINDINGS"
    else:
        contrib = "FAIL"
        visual_discovery_status = "FAIL"
        
    new_entry = {
        "command": " ".join(CMD),
        "start_time": start_time,
        "end_time": end_time,
        "exit_code": res.returncode,
        "stdout_path": stdout_rel_path,
        "stderr_path": stderr_rel_path,
        "parsed_pass_count": passed,
        "parsed_fail_count": failed,
        "parsed_error_count": errors,
        "visual_findings_count": visual_findings_count,
        "visual_expected_findings_count": visual_expected_findings_count,
        "visual_finding_ids": visual_finding_ids,
        "visual_discovery_status": visual_discovery_status,
        "final_status_contribution": contrib
    }
    
    # Update entry in results
    updated = False
    for i, r in enumerate(results):
        if "test_visual_matrix" in r.get("command", ""):
            results[i] = new_entry
            updated = True
            break
            
    if not updated:
        results.append(new_entry)
        
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Wrote test command results to {results_json_path}")
    print(f"Result: exit_code={res.returncode}, passed={passed}, failed={failed}, errors={errors}, contrib={contrib}\n")
    
    # Run generate_all_reports.py
    print("Running generate_all_reports.py...")
    gen_res = subprocess.run(
        [sys.executable, "tools/qa/generate_all_reports.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    print(gen_res.stdout)
    if gen_res.stderr:
        print("GENERATE REPORTS STDERR:", gen_res.stderr)

if __name__ == "__main__":
    main()
