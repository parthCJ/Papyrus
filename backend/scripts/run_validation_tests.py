#!/usr/bin/env python3
"""
Run validation regression tests
Usage: python run_tests.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.test_validators import RegressionTester

if __name__ == "__main__":
    print("=" * 60)
    print("VALIDATION REGRESSION TEST SUITE")
    print("=" * 60)
    print()

    tester = RegressionTester()
    results = tester.run_all_tests()

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print()
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("✓ All regression tests PASSED!")
        print("  No known bugs have regressed.")
        sys.exit(0)
    else:
        print(f"✗ REGRESSION DETECTED: {failed} test(s) failed!")
        print("  Some validators are not catching known failures.")
        sys.exit(1)
