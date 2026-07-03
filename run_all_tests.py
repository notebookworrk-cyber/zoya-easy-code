import subprocess
import sys
import time

TEST_FILES = [
    "test_web_framework.py",
    "test_desktop_framework.py",
    "test_scientific.py",
    "test_ai_platform.py",
    "test_cloud_platform.py",
    "test_ide_platform.py",
    "test_data_science.py",
    "test_mobile_framework.py",
    "test_security_module.py",
    "test_devops_module.py",
    "test_marketplace_visual_export.py",
    "test_enterprise_robotics.py",
]

def main():
    total = 0
    passed = 0
    failed = 0
    start = time.time()

    for file in TEST_FILES:
        result = subprocess.run(
            [sys.executable, file],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().split("\n")
        last_line = lines[-1] if lines else ""

        if result.returncode == 0:
            passed += 1
            print(f"  PASS  {file}  ({last_line})")
        else:
            failed += 1
            print(f"  FAIL  {file}")
            print(result.stderr.strip()[:500])

    elapsed = time.time() - start
    print()
    print(f"  {'='*50}")
    print(f"  Results: {passed + failed} suites | {passed} passed, {failed} failed | {elapsed:.1f}s")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
