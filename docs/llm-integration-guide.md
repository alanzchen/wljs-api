# Model Content Protocol for LLM-Notebook Integration

This document defines a standardized protocol for Large Language Models (LLMs) to interact with WLJS computational notebooks. It provides structured patterns, workflows, and best practices specifically designed for AI agents.

## Protocol Overview

The Model Content Protocol (MCP) enables LLMs to:

1. **Execute computational tasks** through notebook interfaces
2. **Manage computational state** across multiple interactions
3. **Generate and manipulate** dynamic content
4. **Provide interactive assistance** for computational workflows
5. **Handle complex multi-step** mathematical and scientific computations

## Core Protocol Patterns

### Pattern 1: State-Aware Execution

LLMs should maintain awareness of computational state across interactions:

```python
class LLMNotebookAgent:
    def __init__(self):
        self.session_state = {
            "kernel_hash": None,
            "notebook_id": None,
            "variables": {},
            "last_results": [],
            "execution_context": {}
        }
    
    async def initialize_session(self):
        """Initialize a new computational session."""
        
        # Step 1: Verify API readiness
        ready = await self.api_call("/api/ready/")
        if not ready.get("ReadyQ"):
            raise Exception("Computational backend not ready")
        
        # Step 2: Select optimal kernel
        kernels = await self.api_call("/api/kernels/list/")
        optimal_kernel = self.select_optimal_kernel(kernels)
        self.session_state["kernel_hash"] = optimal_kernel["Hash"]
        
        # Step 3: Create dedicated notebook (optional)
        if self.requires_notebook():
            notebook_uuid = await self.api_call("/api/notebook/create/")
            await asyncio.sleep(1)  # Allow creation to complete
            self.session_state["notebook_id"] = await self.api_call(
                "/api/notebook/create/pull/", {"Id": notebook_uuid}
            )
        
        return self.session_state
    
    def select_optimal_kernel(self, kernels):
        """Select the best kernel for computational tasks."""
        # Prioritize kernels that are both ready and have container ready
        ready_kernels = [
            k for k in kernels 
            if k.get("ReadyQ") and k.get("ContainerReadyQ")
        ]
        
        if not ready_kernels:
            raise Exception("No computational kernels available")
        
        # Select kernel with best performance characteristics
        return max(ready_kernels, key=lambda k: (
            k.get("ReadyQ", 0),
            k.get("ContainerReadyQ", 0),
            -len(k.get("Hash", ""))  # Prefer newer kernels (shorter hashes)
        ))
```

### Pattern 2: Intelligent Code Generation

LLMs should generate contextually appropriate Wolfram Language code:

```python
class CodeGenerator:
    def __init__(self, session_state):
        self.state = session_state
        self.language_patterns = self.load_language_patterns()
    
    def generate_code(self, user_intent, context=None):
        """Generate Wolfram Language code based on user intent."""
        
        # Analyze intent and extract requirements
        intent_analysis = self.analyze_intent(user_intent)
        
        # Consider current computational context
        available_vars = list(self.state["variables"].keys())
        previous_results = self.state["last_results"]
        
        # Generate appropriate code
        if intent_analysis["type"] == "mathematical_computation":
            return self.generate_math_code(intent_analysis, available_vars)
        elif intent_analysis["type"] == "data_visualization":
            return self.generate_plot_code(intent_analysis, available_vars)
        elif intent_analysis["type"] == "data_analysis":
            return self.generate_analysis_code(intent_analysis, available_vars)
        else:
            return self.generate_general_code(intent_analysis, available_vars)
    
    def generate_math_code(self, intent, variables):
        """Generate mathematical computation code."""
        if intent["operation"] == "solve_equation":
            equation = intent["equation"]
            variable = intent.get("variable", "x")
            return f"Solve[{equation}, {variable}]"
        
        elif intent["operation"] == "differentiate":
            expr = intent["expression"]
            var = intent.get("variable", "x")
            return f"D[{expr}, {var}]"
        
        elif intent["operation"] == "integrate":
            expr = intent["expression"]
            var = intent.get("variable", "x")
            bounds = intent.get("bounds")
            if bounds:
                return f"Integrate[{expr}, {{{var}, {bounds[0]}, {bounds[1]}}}]"
            else:
                return f"Integrate[{expr}, {var}]"
    
    def generate_plot_code(self, intent, variables):
        """Generate visualization code."""
        if intent["plot_type"] == "function_plot":
            func = intent["function"]
            domain = intent.get("domain", "{x, -5, 5}")
            options = intent.get("options", "")
            return f"Plot[{func}, {domain}{', ' + options if options else ''}]"
        
        elif intent["plot_type"] == "data_plot":
            data_var = intent["data_variable"]
            if data_var in variables:
                return f"ListPlot[{data_var}]"
            else:
                return f"(* Error: Variable {data_var} not defined *)"
```

### Pattern 3: Result Interpretation

LLMs should intelligently interpret and explain computational results:

```python
class ResultInterpreter:
    def __init__(self):
        self.result_patterns = self.load_result_patterns()
    
    async def interpret_results(self, execution_result, original_intent):
        """Interpret computational results for human understanding."""
        
        results = []
        
        for result_item in execution_result:
            interpretation = {
                "raw_data": result_item.get("Data"),
                "display_type": result_item.get("Display"),
                "result_type": result_item.get("Type"),
                "interpretation": None,
                "explanation": None,
                "follow_up_suggestions": []
            }
            
            # Interpret based on display type
            if result_item.get("Display") == "graphics":
                interpretation["interpretation"] = self.interpret_graphics(result_item)
            elif result_item.get("Display") == "codemirror":
                interpretation["interpretation"] = self.interpret_text_output(result_item)
            elif result_item.get("Display") == "markdown":
                interpretation["interpretation"] = self.interpret_markdown(result_item)
            
            # Generate explanation
            interpretation["explanation"] = self.generate_explanation(
                interpretation, original_intent
            )
            
            # Suggest follow-up actions
            interpretation["follow_up_suggestions"] = self.suggest_follow_ups(
                interpretation, original_intent
            )
            
            results.append(interpretation)
        
        return results
    
    def interpret_graphics(self, result_item):
        """Interpret graphical output."""
        return {
            "type": "visualization",
            "description": "Generated a graphical plot",
            "can_display": True,
            "interactive": False
        }
    
    def interpret_text_output(self, result_item):
        """Interpret textual computational output."""
        data = result_item.get("Data", "")
        
        # Detect mathematical expressions
        if any(math_indicator in data for math_indicator in ["==", "->", "{"]):
            return {
                "type": "mathematical_result",
                "description": "Mathematical expression or solution",
                "symbolic": True
            }
        
        # Detect numerical results
        try:
            float(data.strip())
            return {
                "type": "numerical_result",
                "description": "Numerical computation result",
                "value": float(data.strip())
            }
        except:
            pass
        
        return {
            "type": "general_output",
            "description": "General computational output",
            "content": data
        }
```

### Pattern 4: Error Recovery and Adaptation

LLMs should handle errors gracefully and adapt their approach:

```python
class ErrorHandler:
    def __init__(self, session_state):
        self.state = session_state
        self.error_patterns = self.load_error_patterns()
        self.recovery_strategies = self.load_recovery_strategies()
    
    async def handle_execution_error(self, error_info, original_code, intent):
        """Handle execution errors with intelligent recovery."""
        
        error_analysis = self.analyze_error(error_info, original_code)
        
        # Determine recovery strategy
        strategy = self.select_recovery_strategy(error_analysis, intent)
        
        if strategy == "syntax_correction":
            return await self.attempt_syntax_correction(original_code, error_analysis)
        elif strategy == "alternative_approach":
            return await self.generate_alternative_approach(intent, error_analysis)
        elif strategy == "kernel_restart":
            return await self.restart_and_retry(original_code, intent)
        elif strategy == "user_guidance":
            return self.provide_user_guidance(error_analysis, intent)
    
    def analyze_error(self, error_info, code):
        """Analyze error to determine cause and potential fixes."""
        
        error_patterns = {
            "syntax_error": ["Syntax::", "::syntax", "unexpected"],
            "undefined_symbol": ["Symbol", "is not defined", "::sym"],
            "type_mismatch": ["::argtype", "type mismatch", "expected"],
            "computational_limit": ["::memlim", "::timelim", "aborted"],
            "mathematical_error": ["::nonnum", "::indet", "division by zero"]
        }
        
        error_type = "unknown"
        error_details = str(error_info).lower()
        
        for pattern_name, patterns in error_patterns.items():
            if any(pattern in error_details for pattern in patterns):
                error_type = pattern_name
                break
        
        return {
            "type": error_type,
            "raw_error": error_info,
            "code": code,
            "suggested_fixes": self.get_suggested_fixes(error_type, code)
        }
    
    async def attempt_syntax_correction(self, original_code, error_analysis):
        """Attempt to automatically correct syntax errors."""
        
        fixes = error_analysis["suggested_fixes"]
        
        for fix in fixes:
            try:
                corrected_code = self.apply_fix(original_code, fix)
                
                # Test the corrected code
                result = await self.execute_code_safely(corrected_code)
                
                if result["success"]:
                    return {
                        "success": True,
                        "corrected_code": corrected_code,
                        "result": result["data"],
                        "fix_applied": fix["description"]
                    }
            except:
                continue
        
        return {"success": False, "attempted_fixes": fixes}
```

### Pattern 5: Multi-Step Workflow Management

LLMs should handle complex multi-step computational workflows:

```python
class WorkflowManager:
    def __init__(self, session_state):
        self.state = session_state
        self.workflow_history = []
        self.checkpoints = {}
    
    async def execute_workflow(self, workflow_description):
        """Execute a complex multi-step workflow."""
        
        # Parse workflow into steps
        steps = self.parse_workflow(workflow_description)
        
        workflow_id = self.generate_workflow_id()
        workflow_state = {
            "id": workflow_id,
            "steps": steps,
            "current_step": 0,
            "results": [],
            "variables_created": [],
            "checkpoints": {}
        }
        
        try:
            for i, step in enumerate(steps):
                workflow_state["current_step"] = i
                
                # Create checkpoint before significant steps
                if step.get("create_checkpoint"):
                    await self.create_checkpoint(workflow_id, f"step_{i}")
                
                # Execute step
                step_result = await self.execute_step(step, workflow_state)
                workflow_state["results"].append(step_result)
                
                # Update variables tracking
                if step_result.get("variables_created"):
                    workflow_state["variables_created"].extend(
                        step_result["variables_created"]
                    )
                
                # Check for step dependencies
                if not self.verify_step_success(step_result, step):
                    raise WorkflowError(f"Step {i} failed: {step_result.get('error')}")
        
        except WorkflowError as e:
            # Attempt recovery
            recovery_result = await self.attempt_workflow_recovery(
                workflow_state, e
            )
            if recovery_result["success"]:
                workflow_state = recovery_result["updated_state"]
            else:
                raise e
        
        self.workflow_history.append(workflow_state)
        return workflow_state
    
    def parse_workflow(self, description):
        """Parse natural language workflow description into executable steps."""
        
        # This would use NLP to understand the workflow
        # For example: "First calculate the derivative, then plot it, finally find the zeros"
        
        workflow_patterns = {
            "mathematical_analysis": [
                {"action": "define_function", "priority": 1},
                {"action": "analyze_properties", "priority": 2},
                {"action": "visualize", "priority": 3},
                {"action": "find_special_points", "priority": 4}
            ],
            "data_processing": [
                {"action": "load_data", "priority": 1},
                {"action": "clean_data", "priority": 2},
                {"action": "analyze_data", "priority": 3},
                {"action": "visualize_results", "priority": 4}
            ]
        }
        
        # Simplified parsing - in practice would use more sophisticated NLP
        if "derivative" in description and "plot" in description:
            return [
                {
                    "type": "computation",
                    "action": "calculate_derivative",
                    "create_checkpoint": True
                },
                {
                    "type": "visualization", 
                    "action": "create_plot",
                    "depends_on": ["derivative_result"]
                },
                {
                    "type": "analysis",
                    "action": "find_critical_points",
                    "depends_on": ["derivative_result"]
                }
            ]
        
        return []
```

## Protocol Implementation Guidelines

### 1. Session Management

```python
class LLMSessionManager:
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 hour
    
    async def create_session(self, user_id, session_config=None):
        """Create a new computational session for a user."""
        
        session = LLMNotebookAgent()
        await session.initialize_session()
        
        session_info = {
            "agent": session,
            "created_at": time.time(),
            "last_activity": time.time(),
            "user_id": user_id,
            "config": session_config or {}
        }
        
        session_id = self.generate_session_id()
        self.active_sessions[session_id] = session_info
        
        return session_id
    
    async def get_session(self, session_id):
        """Retrieve an active session."""
        if session_id not in self.active_sessions:
            raise SessionError("Session not found or expired")
        
        session_info = self.active_sessions[session_id]
        session_info["last_activity"] = time.time()
        
        return session_info["agent"]
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = [
            sid for sid, info in self.active_sessions.items()
            if current_time - info["last_activity"] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            await self.terminate_session(session_id)
```

### 2. Context Preservation

```python
class ContextManager:
    def __init__(self):
        self.context_stack = []
        self.variable_registry = {}
        self.computation_history = []
    
    def save_context(self, checkpoint_name):
        """Save current computational context."""
        context = {
            "name": checkpoint_name,
            "timestamp": time.time(),
            "variables": dict(self.variable_registry),
            "computation_history": list(self.computation_history),
            "kernel_state": self.capture_kernel_state()
        }
        
        self.context_stack.append(context)
        return len(self.context_stack) - 1
    
    async def restore_context(self, checkpoint_index):
        """Restore computational context from checkpoint."""
        if checkpoint_index >= len(self.context_stack):
            raise ContextError("Invalid checkpoint index")
        
        context = self.context_stack[checkpoint_index]
        
        # Restore variables
        await self.restore_variables(context["variables"])
        
        # Restore computation history
        self.computation_history = context["computation_history"]
        self.variable_registry = context["variables"]
        
        return context
```

### 3. Intelligent Caching

```python
class ComputationCache:
    def __init__(self):
        self.cache = {}
        self.cache_metrics = {}
    
    def generate_cache_key(self, code, context_vars):
        """Generate a cache key for computational results."""
        
        # Normalize code
        normalized_code = self.normalize_code(code)
        
        # Include relevant context variables
        relevant_vars = self.extract_relevant_variables(code, context_vars)
        
        # Create hash
        cache_data = {
            "code": normalized_code,
            "variables": relevant_vars
        }
        
        return hashlib.md5(
            json.dumps(cache_data, sort_keys=True).encode()
        ).hexdigest()
    
    async def get_cached_result(self, cache_key):
        """Retrieve cached computational result."""
        if cache_key in self.cache:
            self.cache_metrics[cache_key]["hits"] += 1
            self.cache_metrics[cache_key]["last_accessed"] = time.time()
            return self.cache[cache_key]
        return None
    
    def cache_result(self, cache_key, result, computation_time):
        """Cache a computational result."""
        self.cache[cache_key] = {
            "result": result,
            "cached_at": time.time(),
            "computation_time": computation_time
        }
        
        self.cache_metrics[cache_key] = {
            "hits": 0,
            "cached_at": time.time(),
            "last_accessed": time.time(),
            "computation_time": computation_time
        }
```

## Advanced Integration Patterns

### Pattern A: Collaborative Computing

For LLMs working with human users in real-time:

```python
class CollaborativeAgent:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.collaboration_state = {}
    
    async def suggest_next_steps(self, current_context, user_intent):
        """Suggest next computational steps based on context."""
        
        suggestions = []
        
        # Analyze current state
        variables = current_context.get("variables", {})
        last_results = current_context.get("last_results", [])
        
        # Generate contextual suggestions
        if self.has_function_definition(variables):
            suggestions.extend([
                "Analyze function properties (domain, range, continuity)",
                "Create visualization of the function",
                "Find critical points and extrema",
                "Calculate derivatives and integrals"
            ])
        
        if self.has_data_structure(variables):
            suggestions.extend([
                "Perform statistical analysis",
                "Create data visualizations",
                "Identify patterns and correlations",
                "Apply machine learning algorithms"
            ])
        
        return self.rank_suggestions(suggestions, user_intent)
```

### Pattern B: Learning and Adaptation

For LLMs that improve their computational assistance over time:

```python
class AdaptiveLearning:
    def __init__(self):
        self.interaction_history = []
        self.success_patterns = {}
        self.failure_patterns = {}
    
    def record_interaction(self, user_input, generated_code, result, user_feedback):
        """Record interaction for learning purposes."""
        
        interaction = {
            "timestamp": time.time(),
            "user_input": user_input,
            "generated_code": generated_code,
            "result": result,
            "user_feedback": user_feedback,
            "success": self.evaluate_success(result, user_feedback)
        }
        
        self.interaction_history.append(interaction)
        
        # Update patterns
        if interaction["success"]:
            self.update_success_patterns(interaction)
        else:
            self.update_failure_patterns(interaction)
    
    def improve_code_generation(self, current_intent):
        """Improve code generation based on learned patterns."""
        
        similar_successful = self.find_similar_successful_interactions(current_intent)
        similar_failed = self.find_similar_failed_interactions(current_intent)
        
        # Learn from successes and failures
        generation_hints = {
            "preferred_patterns": self.extract_patterns(similar_successful),
            "patterns_to_avoid": self.extract_patterns(similar_failed),
            "success_probability": self.calculate_success_probability(current_intent)
        }
        
        return generation_hints
```

## Protocol Standards and Conventions

### Request Format Standards

All LLM-generated API requests should follow these conventions:

```json
{
  "request_id": "unique_identifier",
  "session_context": {
    "session_id": "session_identifier",
    "user_id": "user_identifier",
    "timestamp": "iso_timestamp"
  },
  "computation_intent": {
    "type": "computation_type",
    "description": "natural_language_description",
    "priority": "high|medium|low",
    "dependencies": ["list_of_dependencies"]
  },
  "execution_parameters": {
    "timeout": 30,
    "retry_attempts": 3,
    "cache_enabled": true
  },
  "api_payload": {
    // Standard API request payload
  }
}
```

### Response Processing Standards

LLM agents should process responses according to these standards:

```python
class ResponseProcessor:
    def __init__(self):
        self.processing_rules = self.load_processing_rules()
    
    def process_api_response(self, response, request_context):
        """Process API response with standardized handling."""
        
        processed_response = {
            "request_id": request_context.get("request_id"),
            "status": "success" if response != "$Failed" else "error",
            "raw_response": response,
            "processed_data": None,
            "interpretation": None,
            "follow_up_actions": [],
            "user_message": None
        }
        
        if processed_response["status"] == "success":
            # Process successful response
            processed_response["processed_data"] = self.extract_data(response)
            processed_response["interpretation"] = self.interpret_response(
                response, request_context
            )
            processed_response["follow_up_actions"] = self.suggest_follow_ups(
                response, request_context
            )
            processed_response["user_message"] = self.generate_user_message(
                processed_response
            )
        else:
            # Handle error response
            processed_response["error_analysis"] = self.analyze_error(
                response, request_context
            )
            processed_response["recovery_suggestions"] = self.suggest_recovery(
                response, request_context
            )
            processed_response["user_message"] = self.generate_error_message(
                processed_response
            )
        
        return processed_response
```

This Model Content Protocol provides a comprehensive framework for LLMs to interact effectively with WLJS computational notebooks, enabling sophisticated AI-assisted computational workflows.