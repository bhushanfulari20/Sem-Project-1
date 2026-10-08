import subprocess
import sys
import time
import urllib.request
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def run_step(step_name, command_args, cwd=ROOT_DIR):
    print("\n" + "=" * 70)
    print(f"RUNNING: {step_name}")
    print("=" * 70)
    res = subprocess.run([sys.executable] + command_args if command_args[0].endswith(".py") else command_args, cwd=cwd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)
    if res.returncode != 0:
        print(f"[FAIL] {step_name} FAILED with return code {res.returncode}")
        return False
    print(f"[PASS] {step_name} PASSED successfully!")
    return True

def main():
    print("======================================================================")
    print("             SAFECART COMPLETE FULL-SYSTEM VERIFICATION")
    print("======================================================================")

    steps = [
        ("1. Database & CSV Integrity Validation", ["Database/test_database.py"], ROOT_DIR),
        ("2. Database.py Standard Test", ["Database/database.py"], ROOT_DIR),
        ("3. Rules Intent Detection Test", ["Backend/test_rules.py"], ROOT_DIR),
        ("4. Worker Agent 11-Point Verification", ["Backend/test_worker.py"], ROOT_DIR),
        ("5. Auditor Agent 7-Case Verification", ["Backend/test_auditor.py"], ROOT_DIR),
        ("6. FastAPI Backend Route & Unit Verification", ["Backend/test_main.py"], ROOT_DIR),
    ]

    all_passed = True
    for name, cmd, cwd in steps:
        if not run_step(name, cmd, cwd):
            all_passed = False
            break

    if not all_passed:
        print("\n[FAIL] SYSTEM VERIFICATION FAILED AT EARLIER STEP.")
        sys.exit(1)

    # Step 7: Live FastAPI Server + End-to-End API Integration
    print("\n" + "=" * 70)
    print("RUNNING: 7. Live FastAPI Server + End-to-End API Integration")
    print("=" * 70)
    
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "Backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Wait up to 5 seconds for server to start
        started = False
        for _ in range(10):
            try:
                time.sleep(0.5)
                req = urllib.request.Request("http://127.0.0.1:8000/health")
                with urllib.request.urlopen(req, timeout=1) as res:
                    if res.status == 200:
                        started = True
                        break
            except Exception:
                pass

        if not started:
            print("[FAIL] Live FastAPI server failed to start on 127.0.0.1:8000")
            all_passed = False
        else:
            print("[INFO] Live FastAPI server is running on http://127.0.0.1:8000")
            e2e_res = subprocess.run([sys.executable, "test_e2e_integration.py"], cwd=ROOT_DIR, capture_output=True, text=True)
            print(e2e_res.stdout)
            if e2e_res.returncode != 0:
                print(e2e_res.stderr)
                all_passed = False
    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except Exception:
            server_process.kill()

    print("\n" + "=" * 70)
    print("RUNNING: 8. Frontend Production Build Verification")
    fe_dir = (ROOT_DIR / "frontend") if (ROOT_DIR / "frontend").is_dir() else (ROOT_DIR / "Frontend")
    fe_res = subprocess.run(["npm.cmd", "run", "build"], cwd=fe_dir, capture_output=True, text=True, shell=True)
    print(fe_res.stdout)
    if fe_res.stderr:
        print(fe_res.stderr)
    if fe_res.returncode != 0:
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] ALL PROJECT VERIFICATION CHECKS COMPLETED SUCCESSFULLY!")
        print("PROJECT VERIFIED.")
    else:
        print("[FAIL] PROJECT VERIFICATION FAILED.")
    print("=" * 70)

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
