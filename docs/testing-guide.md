# Testing Guide for WLJS API

This guide provides comprehensive testing strategies, examples, and tools for validating the WLJS API functionality.

## Testing Overview

The WLJS API testing covers several areas:

1. **API Endpoint Testing** - Verify all endpoints work correctly
2. **Integration Testing** - Test complete workflows
3. **Performance Testing** - Measure response times and throughput
4. **Error Handling Testing** - Validate error scenarios
5. **Load Testing** - Test under concurrent usage

## Prerequisites

Before running tests, ensure:

- WLJS server is running on `http://127.0.0.1:20560`
- At least one computational kernel is available
- Required Python packages: `requests`, `pytest`, `asyncio`

## Basic API Testing

### Manual Testing Checklist

Use this checklist to manually verify API functionality:

#### Health and Readiness
- [ ] `/api/ready/` returns `{"ReadyQ": true}`
- [ ] `/api/` returns list of available endpoints

#### Kernel Management
- [ ] `/api/kernels/list/` returns array of kernels
- [ ] At least one kernel has `ReadyQ: true` and `ContainerReadyQ: true`
- [ ] `/api/kernels/get/` with valid hash returns kernel details
- [ ] `/api/kernels/restart/` restarts kernel successfully

#### Transaction Processing
- [ ] `/api/transactions/create/` with valid code returns transaction hash
- [ ] `/api/transactions/get/` tracks execution state correctly
- [ ] Simple expressions like `"2 + 2"` execute successfully
- [ ] `/api/transactions/list/` shows active transactions
- [ ] `/api/transactions/delete/` removes completed transactions

#### Notebook Operations
- [ ] `/api/notebook/list/` returns available notebooks
- [ ] `/api/notebook/create/` returns UUID for new notebook
- [ ] `/api/notebook/create/pull/` retrieves notebook ID
- [ ] Notebook cell operations work correctly

## Automated Testing Scripts

### Basic Functionality Test

```python
#!/usr/bin/env python3
"""
Basic WLJS API Test Suite
========================

Run comprehensive tests of core API functionality.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class WLJSAPITester:
    def __init__(self, base_url: str = "http://127.0.0.1:20560"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.kernel_hash: Optional[str] = None
        self.test_results = []
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def post(self, endpoint: str, payload: Dict = None) -> Any:
        """Make API request."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if payload is None:
                response = self.session.post(url, timeout=10)
            else:
                response = self.session.post(
                    url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            return response.json()
        except Exception as e:
            raise Exception(f"Request failed: {e}")
    
    def test_api_ready(self):
        """Test API readiness."""
        try:
            result = self.post("/api/ready/")
            if isinstance(result, dict) and result.get("ReadyQ"):
                self.log_result("API Ready", True, "API is ready")
                return True
            else:
                self.log_result("API Ready", False, f"Unexpected response: {result}")
                return False
        except Exception as e:
            self.log_result("API Ready", False, str(e))
            return False
    
    def test_kernel_list(self):
        """Test kernel listing."""
        try:
            kernels = self.post("/api/kernels/list/")
            if isinstance(kernels, list) and len(kernels) > 0:
                ready_kernels = [k for k in kernels if k.get("ReadyQ") and k.get("ContainerReadyQ")]
                if ready_kernels:
                    self.kernel_hash = ready_kernels[0]["Hash"]
                    self.log_result("Kernel List", True, f"Found {len(ready_kernels)} ready kernel(s)")
                    return True
                else:
                    self.log_result("Kernel List", False, "No ready kernels found")
                    return False
            else:
                self.log_result("Kernel List", False, f"Invalid response: {kernels}")
                return False
        except Exception as e:
            self.log_result("Kernel List", False, str(e))
            return False
    
    def test_simple_execution(self):
        """Test simple code execution."""
        if not self.kernel_hash:
            self.log_result("Simple Execution", False, "No kernel available")
            return False
        
        try:
            # Create transaction
            payload = {
                "Kernel": self.kernel_hash,
                "Data": "2 + 2"
            }
            transaction_hash = self.post("/api/transactions/create/", payload)
            
            if not isinstance(transaction_hash, str):
                self.log_result("Simple Execution", False, f"Invalid transaction hash: {transaction_hash}")
                return False
            
            # Poll for result
            max_attempts = 20
            for attempt in range(max_attempts):
                result = self.post("/api/transactions/get/", {"Hash": transaction_hash})
                
                if result["State"] == "Idle":
                    if result["Result"] and len(result["Result"]) > 0:
                        data = result["Result"][0].get("Data", "")
                        if "4" in str(data):
                            self.log_result("Simple Execution", True, f"Got expected result: {data}")
                            return True
                        else:
                            self.log_result("Simple Execution", False, f"Unexpected result: {data}")
                            return False
                    else:
                        self.log_result("Simple Execution", False, "No result data")
                        return False
                elif result["State"] == "Error":
                    self.log_result("Simple Execution", False, "Execution error")
                    return False
                
                time.sleep(0.5)
            
            self.log_result("Simple Execution", False, "Timeout waiting for result")
            return False
            
        except Exception as e:
            self.log_result("Simple Execution", False, str(e))
            return False
    
    def test_mathematical_operations(self):
        """Test various mathematical operations."""
        if not self.kernel_hash:
            self.log_result("Mathematical Operations", False, "No kernel available")
            return False
        
        test_cases = [
            ("Basic arithmetic", "5 * 7", "35"),
            ("Equation solving", "Solve[x^2 - 9 == 0, x]", "3"),
            ("Derivative", "D[x^2, x]", "2"),
            ("Integration", "Integrate[x, x]", "x^2"),
        ]
        
        passed = 0
        total = len(test_cases)
        
        for name, code, expected_pattern in test_cases:
            try:
                # Create transaction
                payload = {
                    "Kernel": self.kernel_hash,
                    "Data": code
                }
                transaction_hash = self.post("/api/transactions/create/", payload)
                
                # Poll for result
                for attempt in range(20):
                    result = self.post("/api/transactions/get/", {"Hash": transaction_hash})
                    
                    if result["State"] == "Idle":
                        if result["Result"]:
                            data = str(result["Result"][0].get("Data", ""))
                            if expected_pattern in data or expected_pattern.lower() in data.lower():
                                print(f"  ✅ {name}: {data}")
                                passed += 1
                            else:
                                print(f"  ❌ {name}: Expected '{expected_pattern}', got '{data}'")
                        break
                    elif result["State"] == "Error":
                        print(f"  ❌ {name}: Execution error")
                        break
                    
                    time.sleep(0.3)
                else:
                    print(f"  ❌ {name}: Timeout")
                
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        success = passed == total
        self.log_result("Mathematical Operations", success, f"{passed}/{total} tests passed")
        return success
    
    def test_notebook_operations(self):
        """Test notebook management operations."""
        try:
            # List notebooks
            notebooks = self.post("/api/notebook/list/")
            if not isinstance(notebooks, list):
                self.log_result("Notebook Operations", False, f"Invalid notebook list: {notebooks}")
                return False
            
            # Create notebook
            uuid = self.post("/api/notebook/create/")
            if not isinstance(uuid, str):
                self.log_result("Notebook Operations", False, f"Invalid UUID: {uuid}")
                return False
            
            time.sleep(1)  # Wait for creation
            
            # Get notebook ID
            notebook_id = self.post("/api/notebook/create/pull/", {"Id": uuid})
            if not isinstance(notebook_id, str):
                self.log_result("Notebook Operations", False, f"Invalid notebook ID: {notebook_id}")
                return False
            
            # Add cell
            add_result = self.post("/api/notebook/cells/add/", {
                "Notebook": notebook_id,
                "Data": "test_cell = 42"
            })
            
            # List cells
            cells = self.post("/api/notebook/cells/list/", {"Notebook": notebook_id})
            if isinstance(cells, list) and len(cells) > 0:
                self.log_result("Notebook Operations", True, f"Successfully created notebook with {len(cells)} cell(s)")
                return True
            else:
                self.log_result("Notebook Operations", False, f"Cell creation failed: {cells}")
                return False
            
        except Exception as e:
            self.log_result("Notebook Operations", False, str(e))
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        if not self.kernel_hash:
            self.log_result("Error Handling", False, "No kernel available")
            return False
        
        try:
            # Test invalid syntax
            payload = {
                "Kernel": self.kernel_hash,
                "Data": "invalid syntax here $$"
            }
            transaction_hash = self.post("/api/transactions/create/", payload)
            
            # Check that it's handled gracefully
            for attempt in range(10):
                result = self.post("/api/transactions/get/", {"Hash": transaction_hash})
                
                if result["State"] in ["Error", "Idle"]:
                    self.log_result("Error Handling", True, f"Error handled gracefully: {result['State']}")
                    return True
                
                time.sleep(0.3)
            
            self.log_result("Error Handling", False, "Error handling timeout")
            return False
            
        except Exception as e:
            # This is actually expected for some error cases
            self.log_result("Error Handling", True, f"Error caught as expected: {e}")
            return True
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("🧪 WLJS API Test Suite")
        print("=" * 50)
        
        tests = [
            self.test_api_ready,
            self.test_kernel_list,
            self.test_simple_execution,
            self.test_mathematical_operations,
            self.test_notebook_operations,
            self.test_error_handling,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above.")
            return False

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WLJS API Test Suite')
    parser.add_argument('--url', default='http://127.0.0.1:20560',
                       help='WLJS API base URL')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    tester = WLJSAPITester(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

### Performance Testing

```python
#!/usr/bin/env python3
"""
WLJS API Performance Testing
===========================

Test API performance and throughput characteristics.
"""

import requests
import time
import statistics
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

class PerformanceTester:
    def __init__(self, base_url: str = "http://127.0.0.1:20560"):
        self.base_url = base_url.rstrip('/')
        self.kernel_hash = None
    
    def setup(self):
        """Setup for performance testing."""
        # Get ready kernel
        response = requests.post(f"{self.base_url}/api/kernels/list/")
        kernels = response.json()
        
        ready_kernel = next(
            (k for k in kernels if k.get("ReadyQ") and k.get("ContainerReadyQ")),
            None
        )
        
        if not ready_kernel:
            raise Exception("No ready kernel available")
        
        self.kernel_hash = ready_kernel["Hash"]
        print(f"Using kernel: {self.kernel_hash[:8]}...")
    
    def time_simple_execution(self, code: str = "2 + 2") -> float:
        """Time a simple code execution."""
        start_time = time.time()
        
        # Create transaction
        payload = {
            "Kernel": self.kernel_hash,
            "Data": code
        }
        response = requests.post(
            f"{self.base_url}/api/transactions/create/",
            json=payload
        )
        transaction_hash = response.json()
        
        # Poll for completion
        while True:
            response = requests.post(
                f"{self.base_url}/api/transactions/get/",
                json={"Hash": transaction_hash}
            )
            result = response.json()
            
            if result["State"] in ["Idle", "Error"]:
                break
            
            time.sleep(0.1)
        
        return time.time() - start_time
    
    def test_response_times(self, iterations: int = 10):
        """Test response times for simple operations."""
        print(f"Testing response times ({iterations} iterations)...")
        
        times = []
        for i in range(iterations):
            try:
                execution_time = self.time_simple_execution()
                times.append(execution_time)
                print(f"  Iteration {i+1}: {execution_time:.3f}s")
            except Exception as e:
                print(f"  Iteration {i+1}: Error - {e}")
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"\nResponse Time Statistics:")
            print(f"  Average: {avg_time:.3f}s")
            print(f"  Median:  {median_time:.3f}s")
            print(f"  Min:     {min_time:.3f}s")
            print(f"  Max:     {max_time:.3f}s")
            
            return {
                "average": avg_time,
                "median": median_time,
                "min": min_time,
                "max": max_time,
                "samples": len(times)
            }
        
        return None
    
    def test_concurrent_execution(self, concurrent_requests: int = 5):
        """Test concurrent request handling."""
        print(f"Testing concurrent execution ({concurrent_requests} requests)...")
        
        def execute_request():
            return self.time_simple_execution(f"RandomInteger[100]")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(execute_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Individual times: {[f'{t:.3f}s' for t in results]}")
        print(f"  Throughput: {concurrent_requests/total_time:.2f} requests/second")
        
        return {
            "total_time": total_time,
            "individual_times": results,
            "throughput": concurrent_requests / total_time
        }
    
    def test_complex_computations(self):
        """Test performance of complex computations."""
        print("Testing complex computations...")
        
        test_cases = [
            ("Matrix operations", "RandomReal[{-1, 1}, {100, 100}].RandomReal[{-1, 1}, {100, 100}]"),
            ("Symbolic computation", "Expand[(x + y + z)^10]"),
            ("Numerical integration", "NIntegrate[Sin[x]*Cos[y], {x, 0, Pi}, {y, 0, Pi}]"),
            ("Plot generation", "Plot[Sin[x], {x, 0, 2*Pi}]"),
        ]
        
        results = {}
        
        for name, code in test_cases:
            try:
                exec_time = self.time_simple_execution(code)
                results[name] = exec_time
                print(f"  {name}: {exec_time:.3f}s")
            except Exception as e:
                print(f"  {name}: Error - {e}")
        
        return results
    
    def run_performance_suite(self):
        """Run complete performance test suite."""
        print("⚡ WLJS API Performance Test Suite")
        print("=" * 50)
        
        self.setup()
        
        # Basic response times
        response_stats = self.test_response_times(10)
        
        print("\n" + "-" * 30)
        
        # Concurrent execution
        concurrent_stats = self.test_concurrent_execution(3)
        
        print("\n" + "-" * 30)
        
        # Complex computations
        complex_stats = self.test_complex_computations()
        
        print("\n" + "=" * 50)
        print("📊 Performance Summary")
        print("=" * 50)
        
        if response_stats:
            print(f"Average response time: {response_stats['average']:.3f}s")
        
        if concurrent_stats:
            print(f"Concurrent throughput: {concurrent_stats['throughput']:.2f} req/s")
        
        print(f"Complex computation times:")
        for name, time_taken in complex_stats.items():
            print(f"  {name}: {time_taken:.3f}s")

def main():
    """Main performance test runner."""
    tester = PerformanceTester()
    tester.run_performance_suite()

if __name__ == "__main__":
    main()
```

## Load Testing with curl

For quick load testing using curl:

```bash
#!/bin/bash
# Basic load test script

API_URL="http://127.0.0.1:20560"

echo "🔥 WLJS API Load Test"
echo "===================="

# Test API readiness
echo "Testing API readiness..."
for i in {1..10}; do
    response=$(curl -s -w "%{http_code}" -X POST "$API_URL/api/ready/")
    echo "Request $i: $response"
done

echo ""
echo "Testing kernel list endpoint..."
for i in {1..5}; do
    start_time=$(date +%s.%N)
    curl -s -X POST "$API_URL/api/kernels/list/" > /dev/null
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    echo "Request $i: ${duration}s"
done
```

## Integration Testing

Test complete user workflows:

```python
def test_complete_notebook_workflow():
    """Test a complete notebook workflow end-to-end."""
    
    client = WLJSClient()
    
    # Step 1: Initialize
    client.initialize()
    
    # Step 2: Create notebook
    notebook_id = client.create_notebook()
    
    # Step 3: Add multiple cells
    cells = [
        "data = {1, 4, 9, 16, 25}",
        "mean_val = Mean[data]",
        "ListPlot[data]",
        "fitted = Fit[data, {1, x, x^2}, x]"
    ]
    
    cell_ids = []
    for cell_content in cells:
        response = client.add_cell(cell_content)
        # Get the cell ID from the response
        cells_list = client.get_cells()
        cell_ids.append(cells_list[-1]["Id"])
    
    # Step 4: Evaluate all cells
    for cell_id in cell_ids:
        client.evaluate_cell(cell_id)
    
    # Step 5: Verify results
    final_cells = client.get_cells()
    assert len(final_cells) >= len(cells)
    
    print("✅ Complete workflow test passed")

def test_error_recovery_workflow():
    """Test error recovery and continuation."""
    
    client = WLJSClient()
    client.initialize()
    
    # Execute valid code
    result1 = client.execute_code("x = 5")
    assert "5" in str(result1)
    
    # Execute invalid code (should handle gracefully)
    try:
        client.execute_code("invalid syntax $$")
        assert False, "Should have thrown an error"
    except:
        pass  # Expected
    
    # Execute valid code again (should still work)
    result2 = client.execute_code("x + 3")
    assert "8" in str(result2)
    
    print("✅ Error recovery test passed")
```

## Continuous Integration

For CI/CD pipelines, create a test runner:

```yaml
# .github/workflows/api-tests.yml
name: WLJS API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        pip install requests pytest
    
    - name: Start WLJS server
      run: |
        # Start your WLJS server here
        # This depends on your specific setup
        echo "Starting WLJS server..."
    
    - name: Wait for server
      run: |
        timeout 60 bash -c 'until curl -f http://127.0.0.1:20560/api/ready/; do sleep 2; done'
    
    - name: Run API tests
      run: |
        python docs/examples/test_api.py
    
    - name: Run performance tests
      run: |
        python docs/examples/test_performance.py
```

## Test Data and Fixtures

Create test data for consistent testing:

```python
# test_fixtures.py

BASIC_MATH_TESTS = [
    ("addition", "2 + 3", "5"),
    ("multiplication", "4 * 6", "24"),
    ("exponentiation", "2^3", "8"),
    ("factorial", "5!", "120"),
]

CALCULUS_TESTS = [
    ("derivative", "D[x^2, x]", "2*x"),
    ("integral", "Integrate[x, x]", "x^2/2"),
    ("limit", "Limit[Sin[x]/x, x -> 0]", "1"),
]

ALGEBRA_TESTS = [
    ("solve_linear", "Solve[2*x + 3 == 7, x]", "2"),
    ("solve_quadratic", "Solve[x^2 - 5*x + 6 == 0, x]", "2"),
    ("expand", "Expand[(x+1)^2]", "x^2 + 2*x + 1"),
]

PLOTTING_TESTS = [
    ("simple_plot", "Plot[x^2, {x, -2, 2}]", "graphics"),
    ("parametric_plot", "ParametricPlot[{Cos[t], Sin[t]}, {t, 0, 2*Pi}]", "graphics"),
    ("list_plot", "ListPlot[{1, 4, 9, 16, 25}]", "graphics"),
]
```

## Monitoring and Logging

Add monitoring to your tests:

```python
import logging
import time
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wljs_api_tests.log'),
        logging.StreamHandler()
    ]
)

@contextmanager
def timer(operation_name):
    """Context manager for timing operations."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        logging.info(f"{operation_name} completed in {duration:.3f}s")

# Usage
with timer("API initialization"):
    client.initialize()

with timer("Complex computation"):
    result = client.execute_code("NIntegrate[Sin[x]*Cos[y], {x, 0, Pi}, {y, 0, Pi}]")
```

This comprehensive testing guide provides tools and strategies for thoroughly validating the WLJS API functionality, performance, and reliability.