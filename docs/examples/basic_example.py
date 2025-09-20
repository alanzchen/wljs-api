"""
Basic WLJS API Example
=====================

This example demonstrates the fundamental workflow for connecting to
the WLJS API and executing Wolfram Language code.

Prerequisites:
- WLJS server running on http://127.0.0.1:20560
- Python 3.7+ with requests library
"""

import requests
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional

class WLJSClient:
    """Basic client for WLJS API interactions."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:20560"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.kernel_hash: Optional[str] = None
    
    def post(self, endpoint: str, payload: Dict = None) -> Any:
        """Make a POST request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        if payload is None:
            response = self.session.post(url)
        else:
            response = self.session.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code}")
        
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text
    
    def check_ready(self) -> bool:
        """Check if the API is ready."""
        try:
            result = self.post("/api/ready/")
            return result.get("ReadyQ", False)
        except:
            return False
    
    def get_kernels(self) -> List[Dict]:
        """Get list of available kernels."""
        return self.post("/api/kernels/list/")
    
    def find_ready_kernel(self) -> Optional[str]:
        """Find a ready kernel and return its hash."""
        kernels = self.get_kernels()
        
        for kernel in kernels:
            if kernel.get("ReadyQ") and kernel.get("ContainerReadyQ"):
                self.kernel_hash = kernel["Hash"]
                return kernel["Hash"]
        
        return None
    
    def execute_code(self, code: str, kernel_hash: str = None) -> List[Dict]:
        """Execute Wolfram Language code and return results."""
        
        if kernel_hash is None:
            kernel_hash = self.kernel_hash
        
        if kernel_hash is None:
            raise Exception("No kernel available")
        
        # Create transaction
        payload = {
            "Kernel": kernel_hash,
            "Data": code
        }
        transaction_hash = self.post("/api/transactions/create/", payload)
        
        # Poll for results
        while True:
            result = self.post("/api/transactions/get/", {"Hash": transaction_hash})
            
            if result["State"] == "Idle":
                return result["Result"]
            elif result["State"] == "Error":
                raise Exception("Code execution failed")
            
            time.sleep(0.3)  # Wait before polling again


def main():
    """Main example function."""
    
    print("🚀 WLJS API Basic Example")
    print("=" * 40)
    
    # Create client
    client = WLJSClient()
    
    # Step 1: Check API readiness
    print("1. Checking API readiness...")
    if not client.check_ready():
        print("❌ API is not ready. Make sure WLJS server is running.")
        return
    print("✅ API is ready!")
    
    # Step 2: Find a ready kernel
    print("\n2. Finding available kernel...")
    kernel_hash = client.find_ready_kernel()
    if not kernel_hash:
        print("❌ No ready kernel found.")
        return
    print(f"✅ Using kernel: {kernel_hash[:8]}...")
    
    # Step 3: Execute some basic computations
    print("\n3. Executing computations...")
    
    examples = [
        "2 + 2",
        "Solve[x^2 - 4 == 0, x]",
        "D[x^3 + 2*x^2 + x, x]",
        "Integrate[x^2, x]",
        "Plot[Sin[x], {x, 0, 2*Pi}]"
    ]
    
    for i, code in enumerate(examples, 1):
        print(f"\n   Example {i}: {code}")
        try:
            results = client.execute_code(code)
            
            for result in results:
                if result.get("Type") == "Output":
                    data = result.get("Data", "")
                    display = result.get("Display", "")
                    
                    if display == "graphics":
                        print(f"   📊 Generated plot/graphics")
                    else:
                        # Truncate long results
                        if len(data) > 100:
                            data = data[:100] + "..."
                        print(f"   📝 Result: {data}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎉 Example completed!")


if __name__ == "__main__":
    main()