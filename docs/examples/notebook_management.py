"""
Notebook Management Example
==========================

This example demonstrates how to create and manage notebooks,
add cells, and work with notebook structure.
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

class NotebookManager:
    """Manager for notebook operations."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:20560"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.kernel_hash: Optional[str] = None
        self.notebook_id: Optional[str] = None
    
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
    
    def initialize(self):
        """Initialize kernel and create notebook."""
        
        # Check API readiness
        ready = self.post("/api/ready/")
        if not ready.get("ReadyQ"):
            raise Exception("API not ready")
        
        # Find ready kernel
        kernels = self.post("/api/kernels/list/")
        ready_kernel = None
        for kernel in kernels:
            if kernel.get("ReadyQ") and kernel.get("ContainerReadyQ"):
                ready_kernel = kernel
                break
        
        if not ready_kernel:
            raise Exception("No ready kernel available")
        
        self.kernel_hash = ready_kernel["Hash"]
        
        # Create notebook
        notebook_uuid = self.post("/api/notebook/create/")
        time.sleep(1)  # Wait for creation
        
        self.notebook_id = self.post("/api/notebook/create/pull/", {
            "Id": notebook_uuid
        })
        
        print(f"✅ Initialized with kernel {self.kernel_hash[:8]}... and notebook {self.notebook_id}")
    
    def list_notebooks(self) -> List[Dict]:
        """List all available notebooks."""
        return self.post("/api/notebook/list/")
    
    def add_cell(self, content: str, after_cell: str = None) -> str:
        """Add a new cell to the notebook."""
        payload = {
            "Notebook": self.notebook_id,
            "Data": content
        }
        
        if after_cell:
            payload["After"] = after_cell
        
        result = self.post("/api/notebook/cells/add/", payload)
        return result
    
    def get_cells(self) -> List[Dict]:
        """Get all cells in the notebook."""
        return self.post("/api/notebook/cells/list/", {
            "Notebook": self.notebook_id
        })
    
    def get_cell_content(self, cell_id: str) -> str:
        """Get content of a specific cell."""
        return self.post("/api/notebook/cells/get/", {
            "Cell": cell_id
        })
    
    def set_cell_content(self, cell_id: str, content: str) -> str:
        """Set content of a specific cell."""
        return self.post("/api/notebook/cells/set/", {
            "Cell": cell_id,
            "Data": content
        })
    
    def evaluate_cell(self, cell_id: str) -> str:
        """Evaluate a specific cell."""
        return self.post("/api/notebook/cells/evaluate/", {
            "Cell": cell_id
        })
    
    def delete_cell(self, cell_id: str) -> str:
        """Delete a specific cell."""
        return self.post("/api/notebook/cells/delete/", {
            "Cell": cell_id
        })
    
    def get_focused_cell(self) -> Dict:
        """Get the currently focused cell."""
        return self.post("/api/notebook/cells/focused/", {
            "Notebook": self.notebook_id
        })


def demonstrate_notebook_workflow():
    """Demonstrate a complete notebook workflow."""
    
    print("📔 Notebook Management Example")
    print("=" * 50)
    
    # Create manager and initialize
    manager = NotebookManager()
    
    print("\n1. Initializing notebook session...")
    manager.initialize()
    
    # List existing notebooks
    print("\n2. Listing existing notebooks...")
    notebooks = manager.list_notebooks()
    print(f"   Found {len(notebooks)} notebook(s)")
    for nb in notebooks:
        print(f"   - ID: {nb['Id']}, Open: {nb['Opened']}")
    
    # Add some cells
    print("\n3. Adding cells to notebook...")
    
    cell_contents = [
        "# Mathematical Computations",
        "x = 5",
        "y = x^2",
        "result = Solve[x^2 - 9 == 0, x]",
        "Plot[x^2, {x, -5, 5}]"
    ]
    
    cell_ids = []
    for i, content in enumerate(cell_contents):
        print(f"   Adding cell {i+1}: {content}")
        response = manager.add_cell(content)
        print(f"   Response: {response}")
        
        # Get updated cell list to find the new cell
        cells = manager.get_cells()
        if cells:
            cell_ids.append(cells[-1]["Id"])  # Last cell added
    
    # Display notebook structure
    print("\n4. Current notebook structure...")
    cells = manager.get_cells()
    for i, cell in enumerate(cells):
        print(f"   Cell {i+1}:")
        print(f"     ID: {cell['Id']}")
        print(f"     Type: {cell['Type']}")
        print(f"     State: {cell['State']}")
        print(f"     Display: {cell['Display']}")
        
        # Get cell content
        try:
            content = manager.get_cell_content(cell["Id"])
            # Truncate long content
            if len(content) > 80:
                content = content[:80] + "..."
            print(f"     Content: {content}")
        except Exception as e:
            print(f"     Content: Error reading - {e}")
    
    # Evaluate some cells
    print("\n5. Evaluating cells...")
    input_cells = [cell for cell in cells if cell["Type"] == "Input"]
    
    for cell in input_cells[:3]:  # Evaluate first 3 input cells
        try:
            print(f"   Evaluating cell {cell['Id'][:8]}...")
            result = manager.evaluate_cell(cell["Id"])
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error evaluating cell: {e}")
    
    # Get focused cell
    print("\n6. Getting focused cell...")
    try:
        focused = manager.get_focused_cell()
        print(f"   Focused cell: {focused['Id'][:8]}... ({focused['Type']})")
    except Exception as e:
        print(f"   Error getting focused cell: {e}")
    
    # Modify a cell
    if input_cells:
        print("\n7. Modifying a cell...")
        cell_to_modify = input_cells[1]  # Second input cell
        new_content = "modified_value = 42"
        
        try:
            result = manager.set_cell_content(cell_to_modify["Id"], new_content)
            print(f"   Modified cell {cell_to_modify['Id'][:8]}...")
            print(f"   Result: {result}")
            
            # Verify change
            updated_content = manager.get_cell_content(cell_to_modify["Id"])
            print(f"   New content: {updated_content}")
        except Exception as e:
            print(f"   Error modifying cell: {e}")
    
    print("\n🎉 Notebook workflow demonstration complete!")


def demonstrate_collaborative_editing():
    """Demonstrate collaborative editing patterns."""
    
    print("\n" + "=" * 50)
    print("👥 Collaborative Editing Pattern")
    print("=" * 50)
    
    manager = NotebookManager()
    manager.initialize()
    
    # Simulate collaborative workflow
    print("\n1. User A adds initial computation...")
    manager.add_cell("data = {1, 4, 9, 16, 25}")
    
    print("2. User B adds analysis...")
    manager.add_cell("mean_value = Mean[data]")
    
    print("3. User C adds visualization...")
    manager.add_cell("ListPlot[data, PlotStyle -> Red]")
    
    print("4. User A adds refinement...")
    manager.add_cell("fitted = Fit[data, {1, x, x^2}, x]")
    
    # Show final state
    cells = manager.get_cells()
    print(f"\n📊 Final notebook has {len(cells)} cells")
    
    for i, cell in enumerate(cells):
        if cell["Type"] == "Input":
            content = manager.get_cell_content(cell["Id"])
            print(f"   {i+1}. {content}")


if __name__ == "__main__":
    demonstrate_notebook_workflow()
    demonstrate_collaborative_editing()