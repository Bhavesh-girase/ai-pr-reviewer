import os
import sys
import inspect
import asyncio

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

import test_github_integration as t_gh
import test_reviews as t_rev
import test_pull_requests as t_pr
import test_insights as t_ins
import test_repository_sync as t_sync
import test_webhooks as t_wh
import test_legacy_routes_removal as t_legacy
import test_audit5_hardening as t_audit5
import test_audit6_fixes as t_audit6
import test_audit7_l1_fix as t_audit7
import test_audit8_l1_fix as t_audit8
import test_audit11_fixes as t_audit11
import test_audit12_fixes as t_audit12

test_modules = [
    ("GitHub Integration", t_gh),
    ("Reviews", t_rev),
    ("Pull Requests", t_pr),
    ("Insights", t_ins),
    ("Repository Sync", t_sync),
    ("Webhooks", t_wh),
    ("Legacy Routes Removal", t_legacy),
    ("Audit 5 Hardening", t_audit5),
    ("Audit 6 Fixes", t_audit6),
    ("Audit 7 L-1 Fix", t_audit7),
    ("Audit 8 L-1 Fix", t_audit8),
    ("Audit 11 Fixes", t_audit11),
    ("Audit 12 Fixes", t_audit12),
]

def run_module_tests(mod_name, mod):
    print(f"\n--- Running {mod_name} Tests ---")
    fixtures = {}
    for name, obj in inspect.getmembers(mod):
        if hasattr(obj, "_pytestfixturefunction") or getattr(obj, "__name__", "").startswith("mock_") or getattr(obj, "__name__", "").startswith("sample_"):
            raw_fn = getattr(obj, "__wrapped__", obj)
            if callable(raw_fn):
                try:
                    fixtures[name] = raw_fn()
                except Exception:
                    pass

    total = 0
    passed = 0
    failed = 0

    for name, obj in inspect.getmembers(mod):
        if name.startswith("test_") and callable(obj):
            total += 1
            raw_fn = getattr(obj, "__wrapped__", obj)
            sig = inspect.signature(raw_fn)
            kwargs = {}
            for param in sig.parameters.values():
                if param.name in fixtures:
                    kwargs[param.name] = fixtures[param.name]
                elif param.name == "tmp_path":
                    import tempfile
                    from pathlib import Path
                    kwargs["tmp_path"] = Path(tempfile.mkdtemp())
                elif hasattr(mod, param.name):
                    f_obj = getattr(mod, param.name)
                    f_raw = getattr(f_obj, "__wrapped__", f_obj)
                    if callable(f_raw):
                        kwargs[param.name] = f_raw()

            try:
                if inspect.iscoroutinefunction(raw_fn):
                    asyncio.run(raw_fn(**kwargs))
                else:
                    raw_fn(**kwargs)
                print(f"  PASSED: {name}")
                passed += 1
            except Exception as e:
                print(f"  FAILED: {name} -> {e}")
                import traceback
                traceback.print_exc()
                failed += 1

    return total, passed, failed

if __name__ == "__main__":
    grand_total = 0
    grand_passed = 0
    grand_failed = 0

    for mod_name, mod in test_modules:
        total, passed, failed = run_module_tests(mod_name, mod)
        grand_total += total
        grand_passed += passed
        grand_failed += failed

    print("\n" + "="*50)
    print(f"SUMMARY: Total={grand_total}, Passed={grand_passed}, Failed={grand_failed}")
    print("="*50)
    if grand_failed > 0:
        sys.exit(1)
