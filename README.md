# WLJS API

🧮 **Comprehensive Web API for Wolfram Language Jupyter-style Notebooks**

[![API Documentation](https://img.shields.io/badge/docs-comprehensive-brightgreen)](docs/)
[![OpenAPI 3.0](https://img.shields.io/badge/OpenAPI-3.0-blue)](docs/openapi.yaml)
[![Examples](https://img.shields.io/badge/examples-Python%20%7C%20JavaScript-orange)](docs/examples/)
[![LLM Ready](https://img.shields.io/badge/LLM-Integration%20Ready-purple)](docs/llm-integration-guide.md)

This API enables external programs and **Large Language Models** to interact with computational notebooks programmatically, providing a robust protocol for AI-assisted mathematical and scientific computing.

## 🎯 Key Features

- **🔌 RESTful API** - Clean, well-documented endpoints following OpenAPI 3.0
- **🤖 LLM Integration** - Specialized patterns for AI agent development  
- **📊 Notebook Management** - Create, modify, and execute computational notebooks
- **⚡ Asynchronous Execution** - Handle long-running computations efficiently
- **🌐 Web Ready** - CORS-enabled for frontend integration
- **🔍 Comprehensive Testing** - Full test suites and validation tools

## 📚 Complete Documentation

### 📖 **[View Complete Documentation →](docs/)**

Our comprehensive documentation includes:

| Document | Description |
|----------|-------------|
| [**📋 Documentation Index**](docs/index.md) | Complete overview and navigation |
| [**🔧 Developer Guide**](docs/README.md) | Workflows, patterns, and best practices |
| [**🤖 LLM Integration Guide**](docs/llm-integration-guide.md) | Model Content Protocol for AI agents |
| [**📝 OpenAPI Specification**](docs/openapi.yaml) | Complete API reference |
| [**🧪 Testing Guide**](docs/testing-guide.md) | Validation and testing strategies |

### 💡 **[Interactive Examples →](docs/examples/)**

| Example | Language | Use Case |
|---------|----------|----------|
| [**Basic Usage**](docs/examples/basic_example.py) | Python | Fundamental operations |
| [**Notebook Management**](docs/examples/notebook_management.py) | Python | Complete workflows |
| [**LLM Agent**](docs/examples/llm_agent.py) | Python | AI agent implementation |
| [**Web Integration**](docs/examples/web_integration.js) | JavaScript | Frontend development |
| [**Live Demo**](docs/examples/demo.html) | HTML/CSS/JS | Interactive demonstration |

## 🚀 Quick Start

### 1. Check API Status

```bash
curl -X POST http://127.0.0.1:20560/api/ready/
# Response: {"ReadyQ": true}
```

### 2. Execute Wolfram Language Code

```python
import requests
import time

# Get available kernels
kernels = requests.post('http://127.0.0.1:20560/api/kernels/list/').json()
kernel = next(k for k in kernels if k["ReadyQ"] and k["ContainerReadyQ"])

# Execute code
transaction = requests.post('http://127.0.0.1:20560/api/transactions/create/', 
                          json={"Kernel": kernel["Hash"], "Data": "Solve[x^2-4==0,x]"})

# Get results
while True:
    result = requests.post('http://127.0.0.1:20560/api/transactions/get/',
                          json={"Hash": transaction.json()}).json()
    if result["State"] == "Idle":
        print("Solution:", result["Result"])
        break
    time.sleep(0.3)
```

### 3. Try the Interactive Demo

Open [`docs/examples/demo.html`](docs/examples/demo.html) in your browser for a live demonstration of:
- Interactive notebook creation
- Real-time code execution  
- Mathematical computation examples
- Visualization generation

## 🤖 LLM Integration Highlights

### Core Pattern for AI Agents

```python
class LLMNotebookAgent:
    async def process_request(self, user_intent):
        # 1. Analyze computational intent
        intent = self.analyze_intent(user_intent)
        
        # 2. Generate appropriate Wolfram Language code
        code = self.generate_code(intent)
        
        # 3. Execute with context awareness
        result = await self.execute_code(code)
        
        # 4. Interpret and explain results
        return self.explain_results(result, intent)
```

### Supported Workflow Types

- **📐 Mathematical Computation**: Equations, calculus, algebra
- **📊 Data Visualization**: Plots, charts, 3D graphics  
- **📝 Notebook Management**: Cell operations, state tracking
- **🔄 Interactive Sessions**: Multi-step computational workflows
- **⚡ Error Recovery**: Graceful handling and adaptation

## 🏗️ Architecture

The API provides several categories of endpoints:

```
/api/
├── ready/              # Health checks
├── kernels/            # Computational backend management
├── transactions/       # Asynchronous code execution
├── notebook/           # Notebook instance management  
│   └── cells/         # Individual cell operations
├── frontendobjects/    # Dynamic content management
├── extensions/         # Frontend extension management
└── alphaRequest/       # Wolfram Alpha integration
```

## 🧪 Testing

### Run the Test Suite

```bash
# Basic functionality tests
python docs/examples/basic_example.py

# Comprehensive API validation  
python docs/testing-guide.py

# Performance benchmarks
python docs/examples/test_performance.py
```

### Validation Checklist

- [x] API health check responds correctly
- [x] Kernels are available and ready
- [x] Basic mathematical operations work
- [x] Complex computations execute properly
- [x] Notebook operations function correctly
- [x] Error handling is graceful and informative

## 📊 API Endpoints Overview

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/api/ready/` | POST | Check API readiness |
| `/api/kernels/list/` | POST | List available computational kernels |
| `/api/transactions/create/` | POST | Submit code for execution |
| `/api/transactions/get/` | POST | Retrieve execution results |
| `/api/notebook/create/` | POST | Create new notebook |
| `/api/notebook/cells/add/` | POST | Add cell to notebook |
| `/api/notebook/cells/evaluate/` | POST | Execute specific cell |

**[→ View Complete API Reference](docs/openapi.yaml)**

## 🌟 Use Cases

### For LLM Developers
- Build AI agents that can perform mathematical computations
- Create conversational interfaces for scientific computing
- Develop automated research and analysis tools
- Enable natural language to computation workflows

### For Application Developers  
- Integrate computational capabilities into web applications
- Build collaborative notebook environments
- Create educational tools and interactive tutorials
- Develop data analysis and visualization platforms

### For Researchers
- Automate computational research workflows
- Build reproducible analysis pipelines  
- Create custom computational environments
- Develop domain-specific computational tools

## 🔧 Prerequisites

- **WLJS Server**: Running on `http://127.0.0.1:20560` (default)
- **Wolfram Language Kernel**: Available and ready for computation
- **Modern Environment**: Python 3.7+ or modern JavaScript runtime
- **Network Access**: HTTP/HTTPS connectivity to the API server

## 📈 Performance

The API is designed for:
- **Low Latency**: Sub-second response times for simple operations
- **High Throughput**: Concurrent request handling
- **Scalability**: Multiple kernel support for parallel computation
- **Reliability**: Robust error handling and recovery mechanisms

## 🤝 Contributing

We welcome contributions! Please:

1. **Read the Documentation**: Understand the API design and patterns
2. **Check Examples**: Review existing integration patterns  
3. **Test Thoroughly**: Use our comprehensive testing guide
4. **Submit PRs**: Clear descriptions and focused changes

## 📄 License

This project follows the same licensing as the main WLJS project. See the repository for details.

## 🔗 Related Projects

- **[WLJS Main Project](https://github.com/JerryI/wljs-api)** - Core notebook environment
- **[Wolfram Language](https://www.wolfram.com/language/)** - Computational language
- **[OpenAPI Specification](https://swagger.io/specification/)** - API documentation standard

---

**🚀 Ready to build computational AI agents? [Start with our LLM Integration Guide →](docs/llm-integration-guide.md)**