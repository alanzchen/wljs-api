/**
 * JavaScript/Web Integration Example
 * =================================
 * 
 * This example demonstrates how to integrate the WLJS API
 * into web applications and frontend frameworks.
 */

class WLJSWebClient {
    constructor(baseUrl = 'http://127.0.0.1:20560') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.kernelHash = null;
        this.notebookId = null;
    }

    /**
     * Make a POST request to the API
     */
    async post(endpoint, payload = null) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (payload !== null) {
            options.body = JSON.stringify(payload);
        }

        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            throw new Error(`API request failed: ${error.message}`);
        }
    }

    /**
     * Initialize the client with a ready kernel
     */
    async initialize() {
        // Check API readiness
        const readyResponse = await this.post('/api/ready/');
        if (!readyResponse.ReadyQ) {
            throw new Error('API is not ready');
        }

        // Find a ready kernel
        const kernels = await this.post('/api/kernels/list/');
        const readyKernel = kernels.find(k => k.ReadyQ && k.ContainerReadyQ);
        
        if (!readyKernel) {
            throw new Error('No ready kernel available');
        }

        this.kernelHash = readyKernel.Hash;
        console.log(`🚀 Initialized with kernel: ${this.kernelHash.substring(0, 8)}...`);
        
        return this.kernelHash;
    }

    /**
     * Execute Wolfram Language code
     */
    async executeCode(code) {
        if (!this.kernelHash) {
            throw new Error('Client not initialized. Call initialize() first.');
        }

        // Create transaction
        const transactionHash = await this.post('/api/transactions/create/', {
            Kernel: this.kernelHash,
            Data: code
        });

        // Poll for results
        while (true) {
            const result = await this.post('/api/transactions/get/', {
                Hash: transactionHash
            });

            if (result.State === 'Idle') {
                return result.Result;
            } else if (result.State === 'Error') {
                throw new Error('Code execution failed');
            }

            // Wait before polling again
            await new Promise(resolve => setTimeout(resolve, 300));
        }
    }

    /**
     * Create a new notebook
     */
    async createNotebook() {
        const uuid = await this.post('/api/notebook/create/');
        
        // Wait for creation to complete
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        this.notebookId = await this.post('/api/notebook/create/pull/', {
            Id: uuid
        });

        console.log(`📔 Created notebook: ${this.notebookId}`);
        return this.notebookId;
    }

    /**
     * Add a cell to the current notebook
     */
    async addCell(content, afterCell = null) {
        if (!this.notebookId) {
            throw new Error('No notebook created. Call createNotebook() first.');
        }

        const payload = {
            Notebook: this.notebookId,
            Data: content
        };

        if (afterCell) {
            payload.After = afterCell;
        }

        return await this.post('/api/notebook/cells/add/', payload);
    }

    /**
     * Get all cells in the current notebook
     */
    async getCells() {
        if (!this.notebookId) {
            throw new Error('No notebook created. Call createNotebook() first.');
        }

        return await this.post('/api/notebook/cells/list/', {
            Notebook: this.notebookId
        });
    }

    /**
     * Evaluate a specific cell
     */
    async evaluateCell(cellId) {
        return await this.post('/api/notebook/cells/evaluate/', {
            Cell: cellId
        });
    }
}

/**
 * Interactive Web Interface Manager
 */
class InteractiveNotebook {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.client = new WLJSWebClient();
        this.cells = [];
        
        this.setupInterface();
    }

    setupInterface() {
        this.container.innerHTML = `
            <div class="notebook-container">
                <div class="notebook-header">
                    <h2>🧮 Interactive WLJS Notebook</h2>
                    <div class="controls">
                        <button id="init-btn" class="btn btn-primary">Initialize</button>
                        <button id="add-cell-btn" class="btn btn-secondary" disabled>Add Cell</button>
                        <button id="evaluate-all-btn" class="btn btn-success" disabled>Evaluate All</button>
                    </div>
                    <div id="status" class="status">Ready to initialize...</div>
                </div>
                <div id="cells-container" class="cells-container"></div>
            </div>
        `;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Initialize button
        document.getElementById('init-btn').addEventListener('click', () => {
            this.initialize();
        });

        // Add cell button
        document.getElementById('add-cell-btn').addEventListener('click', () => {
            this.addNewCell();
        });

        // Evaluate all button
        document.getElementById('evaluate-all-btn').addEventListener('click', () => {
            this.evaluateAllCells();
        });
    }

    async initialize() {
        const statusEl = document.getElementById('status');
        const initBtn = document.getElementById('init-btn');
        
        try {
            statusEl.textContent = 'Initializing...';
            initBtn.disabled = true;

            await this.client.initialize();
            await this.client.createNotebook();

            statusEl.textContent = 'Ready! You can now add and evaluate cells.';
            document.getElementById('add-cell-btn').disabled = false;
            document.getElementById('evaluate-all-btn').disabled = false;
            
            // Add a sample cell
            this.addNewCell('2 + 2');
            
        } catch (error) {
            statusEl.textContent = `Error: ${error.message}`;
            console.error('Initialization failed:', error);
        } finally {
            initBtn.disabled = false;
        }
    }

    addNewCell(initialContent = '') {
        const cellId = `cell-${Date.now()}`;
        const cellHtml = `
            <div class="cell" id="${cellId}">
                <div class="cell-header">
                    <span class="cell-type">Input</span>
                    <div class="cell-controls">
                        <button class="btn btn-sm evaluate-btn" onclick="notebook.evaluateCell('${cellId}')">
                            ▶️ Run
                        </button>
                        <button class="btn btn-sm delete-btn" onclick="notebook.deleteCell('${cellId}')">
                            🗑️
                        </button>
                    </div>
                </div>
                <textarea class="cell-input" placeholder="Enter Wolfram Language code...">${initialContent}</textarea>
                <div class="cell-output" style="display: none;"></div>
            </div>
        `;

        document.getElementById('cells-container').insertAdjacentHTML('beforeend', cellHtml);
        
        // Focus on the new cell
        const textarea = document.querySelector(`#${cellId} .cell-input`);
        textarea.focus();
        
        // Add keyboard shortcuts
        textarea.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.evaluateCell(cellId);
            }
        });

        this.cells.push(cellId);
    }

    async evaluateCell(cellId) {
        const cellEl = document.getElementById(cellId);
        const inputEl = cellEl.querySelector('.cell-input');
        const outputEl = cellEl.querySelector('.cell-output');
        const evaluateBtn = cellEl.querySelector('.evaluate-btn');

        const code = inputEl.value.trim();
        if (!code) return;

        try {
            evaluateBtn.disabled = true;
            evaluateBtn.textContent = '⏳ Running...';
            outputEl.style.display = 'none';

            // Execute the code
            const results = await this.client.executeCode(code);

            // Display results
            this.displayResults(outputEl, results);
            outputEl.style.display = 'block';

        } catch (error) {
            outputEl.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
            outputEl.style.display = 'block';
        } finally {
            evaluateBtn.disabled = false;
            evaluateBtn.textContent = '▶️ Run';
        }
    }

    displayResults(outputEl, results) {
        if (!results || results.length === 0) {
            outputEl.innerHTML = '<div class="no-output">No output</div>';
            return;
        }

        let html = '';
        for (const result of results) {
            const data = result.Data || '';
            const display = result.Display || '';
            const type = result.Type || '';

            if (display === 'graphics') {
                html += `<div class="result graphics">📊 Graphics output generated</div>`;
            } else if (type === 'Output') {
                // Format the output nicely
                const formattedData = this.formatOutput(data);
                html += `<div class="result output">${formattedData}</div>`;
            }
        }

        outputEl.innerHTML = html;
    }

    formatOutput(data) {
        // Basic formatting for mathematical output
        if (typeof data !== 'string') {
            data = String(data);
        }

        // Handle special mathematical symbols and formatting
        return data
            .replace(/\*/g, '×')
            .replace(/Pi/g, 'π')
            .replace(/Infinity/g, '∞')
            .replace(/\^/g, '<sup>') + (data.includes('^') ? '</sup>' : '');
    }

    deleteCell(cellId) {
        const cellEl = document.getElementById(cellId);
        if (cellEl) {
            cellEl.remove();
            this.cells = this.cells.filter(id => id !== cellId);
        }
    }

    async evaluateAllCells() {
        const statusEl = document.getElementById('status');
        statusEl.textContent = 'Evaluating all cells...';

        for (const cellId of this.cells) {
            await this.evaluateCell(cellId);
            // Small delay between evaluations
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        statusEl.textContent = 'All cells evaluated!';
    }
}

/**
 * Mathematical Expression Evaluator Widget
 */
class MathEvaluator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.client = new WLJSWebClient();
        this.setupWidget();
    }

    setupWidget() {
        this.container.innerHTML = `
            <div class="math-evaluator">
                <h3>🔢 Quick Math Evaluator</h3>
                <div class="input-group">
                    <input type="text" id="math-input" placeholder="Enter mathematical expression..." 
                           class="form-control">
                    <button id="evaluate-btn" class="btn btn-primary">Evaluate</button>
                </div>
                <div id="math-result" class="result-area"></div>
                <div class="examples">
                    <p><strong>Examples:</strong></p>
                    <div class="example-buttons">
                        <button class="example-btn" data-expr="D[x^3 + 2*x^2 + x, x]">Derivative</button>
                        <button class="example-btn" data-expr="Integrate[x^2, x]">Integral</button>
                        <button class="example-btn" data-expr="Solve[x^2 - 4 == 0, x]">Solve Equation</button>
                        <button class="example-btn" data-expr="Plot[Sin[x], {x, 0, 2*Pi}]">Plot Function</button>
                    </div>
                </div>
            </div>
        `;

        this.setupEventListeners();
        this.initialize();
    }

    setupEventListeners() {
        const input = document.getElementById('math-input');
        const button = document.getElementById('evaluate-btn');

        button.addEventListener('click', () => this.evaluate());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.evaluate();
            }
        });

        // Example buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                input.value = btn.dataset.expr;
                this.evaluate();
            });
        });
    }

    async initialize() {
        try {
            await this.client.initialize();
            document.getElementById('evaluate-btn').disabled = false;
        } catch (error) {
            document.getElementById('math-result').innerHTML = 
                `<div class="error">Failed to initialize: ${error.message}</div>`;
        }
    }

    async evaluate() {
        const input = document.getElementById('math-input');
        const result = document.getElementById('math-result');
        const button = document.getElementById('evaluate-btn');

        const expression = input.value.trim();
        if (!expression) return;

        try {
            button.disabled = true;
            button.textContent = 'Evaluating...';
            result.innerHTML = '<div class="loading">⏳ Computing...</div>';

            const results = await this.client.executeCode(expression);

            if (results && results.length > 0) {
                let html = '';
                for (const res of results) {
                    if (res.Display === 'graphics') {
                        html += '<div class="graphics-result">📊 Graphics generated</div>';
                    } else {
                        html += `<div class="math-result">${res.Data}</div>`;
                    }
                }
                result.innerHTML = html;
            } else {
                result.innerHTML = '<div class="no-result">No result</div>';
            }

        } catch (error) {
            result.innerHTML = `<div class="error">❌ ${error.message}</div>`;
        } finally {
            button.disabled = false;
            button.textContent = 'Evaluate';
        }
    }
}

// Global instances for demo
let notebook, mathEvaluator;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if containers exist before initializing
    if (document.getElementById('notebook-container')) {
        notebook = new InteractiveNotebook('notebook-container');
    }
    
    if (document.getElementById('math-evaluator-container')) {
        mathEvaluator = new MathEvaluator('math-evaluator-container');
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WLJSWebClient, InteractiveNotebook, MathEvaluator };
}