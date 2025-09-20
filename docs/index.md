# WLJS API Documentation Index

Welcome to the comprehensive documentation for the WLJS (Wolfram Language Jupyter-style) Notebook API. This collection provides everything you need to integrate with, develop for, and extend the WLJS computational notebook system.

## 📚 Documentation Overview

This documentation is specifically designed to help develop a **Model Content Protocol for Large Language Models** to interact with computational notebooks effectively.

### 🎯 Target Audiences

- **LLM Developers**: Building AI agents that can perform computational tasks
- **API Integrators**: Connecting external applications to WLJS
- **Web Developers**: Creating frontend interfaces for computational notebooks
- **Data Scientists**: Automating computational workflows
- **Researchers**: Building computational research tools

## 📖 Documentation Structure

### Core Documentation

| Document | Description | Target Audience |
|----------|-------------|-----------------|
| [**OpenAPI Specification**](openapi.yaml) | Complete API reference following OpenAPI 3.0 | All developers |
| [**Developer Guide**](README.md) | Comprehensive guide with workflows and examples | API integrators |
| [**LLM Integration Guide**](llm-integration-guide.md) | Model Content Protocol for AI agents | LLM developers |
| [**Testing Guide**](testing-guide.md) | Testing strategies and validation tools | QA engineers |

### Examples and Tutorials

| Example | Language | Description |
|---------|----------|-------------|
| [**Basic API Usage**](examples/basic_example.py) | Python | Fundamental API operations |
| [**Notebook Management**](examples/notebook_management.py) | Python | Complete notebook workflow |
| [**LLM Agent**](examples/llm_agent.py) | Python | AI agent implementation |
| [**Web Integration**](examples/web_integration.js) | JavaScript | Frontend integration |
| [**Interactive Demo**](examples/demo.html) | HTML/CSS/JS | Live web demonstration |

## 🚀 Quick Start

### 1. API Health Check

First, verify your WLJS server is running:

```bash
curl -X POST http://127.0.0.1:20560/api/ready/
# Expected: {"ReadyQ": true}
```

### 2. Basic Python Example

```python
import requests
import time

# Check API readiness
response = requests.post('http://127.0.0.1:20560/api/ready/')
print("API Ready:", response.json()['ReadyQ'])

# Get available kernels
kernels = requests.post('http://127.0.0.1:20560/api/kernels/list/').json()
ready_kernel = next(k for k in kernels if k["ReadyQ"] and k["ContainerReadyQ"])

# Execute code
transaction = requests.post('http://127.0.0.1:20560/api/transactions/create/', 
                          json={"Kernel": ready_kernel["Hash"], "Data": "2 + 2"})

# Get results
while True:
    result = requests.post('http://127.0.0.1:20560/api/transactions/get/',
                          json={"Hash": transaction.json()}).json()
    if result["State"] == "Idle":
        print("Result:", result["Result"])
        break
    time.sleep(0.3)
```

### 3. JavaScript Web Example

```javascript
const client = new WLJSWebClient('http://127.0.0.1:20560');
await client.initialize();
const result = await client.executeCode('Plot[Sin[x], {x, 0, 2*Pi}]');
console.log('Execution result:', result);
```

## 🧠 LLM Integration Patterns

### Core Pattern: State-Aware Execution

```python
class LLMNotebookAgent:
    def __init__(self):
        self.session_state = {
            "kernel_hash": None,
            "variables": {},
            "computation_history": []
        }
    
    async def process_request(self, user_intent):
        # 1. Analyze intent
        intent = self.analyze_intent(user_intent)
        
        # 2. Generate appropriate code
        code = self.generate_code(intent)
        
        # 3. Execute with context awareness
        result = await self.execute_code(code)
        
        # 4. Update state and provide explanation
        self.update_context(result)
        return self.explain_results(result, intent)
```

### Workflow Types

1. **Mathematical Computation**
   - Equation solving: `Solve[x^2 - 4 == 0, x]`
   - Calculus operations: `D[x^3, x]`, `Integrate[x^2, x]`
   - Numerical computation: `NIntegrate[Sin[x], {x, 0, Pi}]`

2. **Data Visualization**
   - Function plotting: `Plot[Sin[x], {x, 0, 2*Pi}]`
   - Data plotting: `ListPlot[data]`
   - 3D visualization: `Plot3D[x^2 + y^2, {x, -2, 2}, {y, -2, 2}]`

3. **Notebook Management**
   - Create notebooks and manage cells
   - Execute cells and track results
   - Handle collaborative editing

## 🔧 API Endpoints Overview

### Core Categories

| Category | Base Path | Description |
|----------|-----------|-------------|
| **Health** | `/api/ready/` | API status and readiness |
| **Kernels** | `/api/kernels/` | Computational backend management |
| **Transactions** | `/api/transactions/` | Asynchronous code execution |
| **Notebooks** | `/api/notebook/` | Notebook instance management |
| **Cells** | `/api/notebook/cells/` | Individual cell operations |
| **Extensions** | `/api/extensions/` | Frontend extension management |
| **Utilities** | `/api/alphaRequest/` | Additional services |

### Key Workflows

#### 1. Simple Code Execution
```
POST /api/kernels/list/ → Find ready kernel
POST /api/transactions/create/ → Submit code
POST /api/transactions/get/ → Poll for results
```

#### 2. Notebook-Based Development
```
POST /api/notebook/create/ → Create notebook
POST /api/notebook/create/pull/ → Get notebook ID
POST /api/notebook/cells/add/ → Add cells
POST /api/notebook/cells/evaluate/ → Execute cells
```

#### 3. Interactive Session
```
POST /api/ready/ → Verify connection
POST /api/kernels/list/ → Get available kernels
Multiple transaction cycles → Build computational state
```

## 📊 Response Formats

### Transaction Results
```json
{
  "Hash": "transaction_id",
  "State": "Idle|Evaluation|Error",
  "Result": [
    {
      "Data": "computational_result",
      "Display": "codemirror|graphics|markdown",
      "Type": "Output"
    }
  ]
}
```

### Kernel Information
```json
{
  "Hash": "kernel_id",
  "State": "Ready",
  "ReadyQ": true,
  "ContainerReadyQ": true,
  "Name": "WolframLanguage"
}
```

## 🔍 Error Handling

### Common Error Patterns

1. **API Not Ready**: Server starting up
   ```json
   {"ReadyQ": false}
   ```

2. **No Ready Kernels**: Backend unavailable
   ```json
   []  // Empty kernel list
   ```

3. **Execution Failure**: Code syntax errors
   ```json
   "$Failed"
   ```

4. **Transaction Errors**: Computation errors
   ```json
   {"State": "Error", "Result": []}
   ```

### Recovery Strategies

```python
async def robust_execute(code, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await execute_code(code)
        except Exception as e:
            if attempt == max_retries - 1:
                # Try kernel restart
                await restart_kernel()
                return await execute_code(code)
            await asyncio.sleep(1)
```

## 🎮 Interactive Examples

### Live Web Demo

Open [`examples/demo.html`](examples/demo.html) in your browser to try:

- **Interactive Notebook**: Create cells, write code, execute live
- **Math Evaluator**: Quick mathematical expression evaluation  
- **Real-time Results**: See computations as they happen

### Python Scripts

Run the example scripts to see different integration patterns:

```bash
# Basic API functionality
python docs/examples/basic_example.py

# Notebook management workflow
python docs/examples/notebook_management.py

# LLM agent demonstration
python docs/examples/llm_agent.py
```

## 🧪 Testing and Validation

### Automated Testing

```bash
# Run comprehensive API tests
python docs/examples/test_api.py

# Performance testing
python docs/examples/test_performance.py

# Load testing with curl
bash docs/examples/load_test.sh
```

### Manual Testing Checklist

- [ ] API responds to `/api/ready/`
- [ ] Kernels are available and ready
- [ ] Simple expressions execute correctly
- [ ] Complex computations work
- [ ] Notebook operations function
- [ ] Error handling is graceful

## 🌟 Best Practices

### For LLM Developers

1. **Context Awareness**: Track computational state across interactions
2. **Intent Analysis**: Parse natural language to computational operations
3. **Error Recovery**: Handle failures gracefully and suggest alternatives
4. **Result Interpretation**: Explain computational results clearly
5. **Session Management**: Maintain persistent computational sessions

### For API Integrators

1. **Connection Management**: Always check readiness before operations
2. **Resource Cleanup**: Clean up transactions and temporary objects
3. **Error Handling**: Implement robust retry and recovery mechanisms
4. **Performance**: Use appropriate polling intervals and caching
5. **Security**: Validate inputs and handle untrusted code safely

### For Web Developers

1. **Asynchronous Operations**: Handle long-running computations properly
2. **User Feedback**: Provide loading states and progress indicators
3. **Result Display**: Format mathematical output appropriately
4. **Responsive Design**: Support various screen sizes and devices
5. **Error UX**: Show meaningful error messages to users

## 🔗 Related Resources

- **WLJS Repository**: [Main project repository](https://github.com/JerryI/wljs-api)
- **Wolfram Language**: [Official documentation](https://reference.wolfram.com/)
- **OpenAPI Specification**: [OpenAPI 3.0 guide](https://swagger.io/specification/)
- **REST API Design**: [Best practices guide](https://restfulapi.net/)

## 📞 Support and Contributing

### Getting Help

1. Check the [testing guide](testing-guide.md) for validation steps
2. Review [common patterns](README.md#common-workflows) for your use case
3. Try the [interactive examples](examples/) to understand the API
4. Check server logs for detailed error information

### Contributing

1. Fork the repository
2. Create examples or documentation improvements
3. Test your changes thoroughly
4. Submit a pull request with clear description

---

## 📄 License

This documentation is part of the WLJS API project and follows the same licensing terms. See the main repository for details.

---

*This documentation is designed to enable sophisticated AI-assisted computational workflows through the WLJS API. Happy coding! 🚀*