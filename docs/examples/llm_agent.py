"""
LLM Agent Example
================

This example demonstrates how an LLM agent can interact with
the WLJS API to perform computational tasks autonomously.
"""

import requests
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class IntentType(Enum):
    MATHEMATICAL_COMPUTATION = "math_computation"
    DATA_VISUALIZATION = "data_visualization"
    EQUATION_SOLVING = "equation_solving"
    CALCULUS_OPERATION = "calculus_operation"
    GENERAL_COMPUTATION = "general_computation"

@dataclass
class ComputationIntent:
    intent_type: IntentType
    description: str
    parameters: Dict[str, Any]
    confidence: float

class LLMAgent:
    """
    An LLM agent that can understand natural language requests
    and execute them using the WLJS API.
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:20560"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.kernel_hash: Optional[str] = None
        self.context: Dict[str, Any] = {
            "variables": {},
            "last_results": [],
            "computation_history": []
        }
    
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
        """Initialize the agent with a ready kernel."""
        
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
        print(f"🤖 LLM Agent initialized with kernel {self.kernel_hash[:8]}...")
    
    def analyze_intent(self, user_input: str) -> ComputationIntent:
        """
        Analyze user input to determine computational intent.
        In a real LLM, this would use sophisticated NLP.
        """
        
        user_input_lower = user_input.lower()
        
        # Mathematical computation patterns
        if any(word in user_input_lower for word in ["calculate", "compute", "evaluate"]):
            if "derivative" in user_input_lower or "differentiate" in user_input_lower:
                return ComputationIntent(
                    IntentType.CALCULUS_OPERATION,
                    f"Calculate derivative: {user_input}",
                    {"operation": "derivative", "expression": self.extract_expression(user_input)},
                    0.9
                )
            elif "integral" in user_input_lower or "integrate" in user_input_lower:
                return ComputationIntent(
                    IntentType.CALCULUS_OPERATION,
                    f"Calculate integral: {user_input}",
                    {"operation": "integral", "expression": self.extract_expression(user_input)},
                    0.9
                )
            else:
                return ComputationIntent(
                    IntentType.MATHEMATICAL_COMPUTATION,
                    f"Mathematical computation: {user_input}",
                    {"expression": self.extract_expression(user_input)},
                    0.8
                )
        
        # Equation solving patterns
        elif any(word in user_input_lower for word in ["solve", "find solution", "equation"]):
            return ComputationIntent(
                IntentType.EQUATION_SOLVING,
                f"Solve equation: {user_input}",
                {"equation": self.extract_equation(user_input)},
                0.9
            )
        
        # Visualization patterns
        elif any(word in user_input_lower for word in ["plot", "graph", "visualize", "chart"]):
            return ComputationIntent(
                IntentType.DATA_VISUALIZATION,
                f"Create visualization: {user_input}",
                {"function": self.extract_function(user_input), "domain": self.extract_domain(user_input)},
                0.8
            )
        
        # General computation
        else:
            return ComputationIntent(
                IntentType.GENERAL_COMPUTATION,
                f"General computation: {user_input}",
                {"raw_input": user_input},
                0.6
            )
    
    def extract_expression(self, text: str) -> str:
        """Extract mathematical expression from text."""
        # Simple pattern matching - in real LLM would be more sophisticated
        
        # Look for expressions in common formats
        patterns = [
            r"of\s+([^.!?]+)",  # "derivative of x^2"
            r"(\w+[\^*+\-/\(\)\w\s]+)",  # Basic math expression
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                # Clean up the expression
                expr = expr.replace("squared", "^2")
                expr = expr.replace("cubed", "^3")
                return expr
        
        return "x^2"  # Default expression
    
    def extract_equation(self, text: str) -> str:
        """Extract equation from text."""
        # Look for equations with equals sign
        eq_pattern = r"([^=]+=[^=]+)"
        match = re.search(eq_pattern, text)
        if match:
            return match.group(1).strip()
        
        # Default equation
        return "x^2 - 4 == 0"
    
    def extract_function(self, text: str) -> str:
        """Extract function from text for plotting."""
        # Simple function extraction
        if "sin" in text.lower():
            return "Sin[x]"
        elif "cos" in text.lower():
            return "Cos[x]"
        elif "x^2" in text or "squared" in text.lower():
            return "x^2"
        elif "x^3" in text or "cubed" in text.lower():
            return "x^3"
        
        return "Sin[x]"  # Default function
    
    def extract_domain(self, text: str) -> str:
        """Extract domain for plotting."""
        # Look for domain specifications
        domain_pattern = r"from\s+(-?\d+(?:\.\d+)?)\s+to\s+(-?\d+(?:\.\d+)?)"
        match = re.search(domain_pattern, text, re.IGNORECASE)
        if match:
            start, end = match.groups()
            return f"{{x, {start}, {end}}}"
        
        return "{x, -5, 5}"  # Default domain
    
    def generate_code(self, intent: ComputationIntent) -> str:
        """Generate Wolfram Language code based on intent."""
        
        if intent.intent_type == IntentType.CALCULUS_OPERATION:
            if intent.parameters["operation"] == "derivative":
                expr = intent.parameters["expression"]
                return f"D[{expr}, x]"
            elif intent.parameters["operation"] == "integral":
                expr = intent.parameters["expression"]
                return f"Integrate[{expr}, x]"
        
        elif intent.intent_type == IntentType.EQUATION_SOLVING:
            equation = intent.parameters["equation"]
            return f"Solve[{equation}, x]"
        
        elif intent.intent_type == IntentType.DATA_VISUALIZATION:
            func = intent.parameters["function"]
            domain = intent.parameters["domain"]
            return f"Plot[{func}, {domain}]"
        
        elif intent.intent_type == IntentType.MATHEMATICAL_COMPUTATION:
            expr = intent.parameters["expression"]
            return expr
        
        else:
            # General computation - try to interpret directly
            raw_input = intent.parameters["raw_input"]
            # Basic cleanup for Wolfram Language
            code = raw_input.replace("**", "^")  # Python to WL power notation
            return code
    
    def execute_code(self, code: str) -> Tuple[bool, List[Dict], str]:
        """Execute code and return success status, results, and explanation."""
        
        try:
            # Create transaction
            payload = {
                "Kernel": self.kernel_hash,
                "Data": code
            }
            transaction_hash = self.post("/api/transactions/create/", payload)
            
            # Poll for results
            while True:
                result = self.post("/api/transactions/get/", {"Hash": transaction_hash})
                
                if result["State"] == "Idle":
                    # Update context
                    self.context["last_results"] = result["Result"]
                    self.context["computation_history"].append({
                        "code": code,
                        "results": result["Result"],
                        "timestamp": time.time()
                    })
                    
                    # Update variables (simple pattern matching)
                    if "=" in code and not any(op in code for op in ["==", "!=", "<=", ">="]):
                        var_name = code.split("=")[0].strip()
                        self.context["variables"][var_name] = "defined"
                    
                    explanation = self.explain_results(result["Result"], code)
                    return True, result["Result"], explanation
                
                elif result["State"] == "Error":
                    return False, [], f"Execution failed for code: {code}"
                
                time.sleep(0.3)
        
        except Exception as e:
            return False, [], f"Error executing code: {e}"
    
    def explain_results(self, results: List[Dict], original_code: str) -> str:
        """Generate human-friendly explanation of results."""
        
        if not results:
            return "No output was generated."
        
        explanations = []
        
        for result in results:
            result_type = result.get("Type", "")
            display_type = result.get("Display", "")
            data = result.get("Data", "")
            
            if display_type == "graphics":
                explanations.append("📊 Generated a graphical plot/visualization")
            elif result_type == "Output":
                if len(data) > 100:
                    explanations.append(f"📝 Computed result (truncated): {data[:100]}...")
                else:
                    explanations.append(f"📝 Computed result: {data}")
        
        if not explanations:
            return "Computation completed successfully."
        
        return " | ".join(explanations)
    
    def suggest_follow_ups(self, intent: ComputationIntent, results: List[Dict]) -> List[str]:
        """Suggest follow-up actions based on results."""
        
        suggestions = []
        
        if intent.intent_type == IntentType.CALCULUS_OPERATION:
            if intent.parameters["operation"] == "derivative":
                suggestions.extend([
                    "Find critical points by setting the derivative to zero",
                    "Plot the original function and its derivative",
                    "Calculate the second derivative for concavity analysis"
                ])
            elif intent.parameters["operation"] == "integral":
                suggestions.extend([
                    "Evaluate the integral over a specific interval",
                    "Plot the integrand function",
                    "Find the area under the curve"
                ])
        
        elif intent.intent_type == IntentType.EQUATION_SOLVING:
            suggestions.extend([
                "Verify the solutions by substitution",
                "Plot the equation to visualize the solutions",
                "Find numerical approximations if needed"
            ])
        
        elif intent.intent_type == IntentType.DATA_VISUALIZATION:
            suggestions.extend([
                "Modify the plot domain or styling",
                "Add more functions to compare",
                "Export the plot for use in documents"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process a complete user request."""
        
        print(f"\n🤖 Processing: '{user_input}'")
        
        # Step 1: Analyze intent
        intent = self.analyze_intent(user_input)
        print(f"   🎯 Intent: {intent.intent_type.value} (confidence: {intent.confidence:.2f})")
        
        # Step 2: Generate code
        code = self.generate_code(intent)
        print(f"   💻 Generated code: {code}")
        
        # Step 3: Execute code
        success, results, explanation = self.execute_code(code)
        
        if success:
            print(f"   ✅ {explanation}")
            
            # Step 4: Generate follow-up suggestions
            suggestions = self.suggest_follow_ups(intent, results)
            if suggestions:
                print("   💡 Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"      {i}. {suggestion}")
        else:
            print(f"   ❌ {explanation}")
        
        return {
            "user_input": user_input,
            "intent": intent,
            "generated_code": code,
            "success": success,
            "results": results,
            "explanation": explanation,
            "suggestions": suggestions if success else [],
            "context": dict(self.context)
        }


def demonstrate_llm_agent():
    """Demonstrate the LLM agent capabilities."""
    
    print("🧠 LLM Agent Demonstration")
    print("=" * 60)
    
    # Create and initialize agent
    agent = LLMAgent()
    agent.initialize()
    
    # Test various types of requests
    test_requests = [
        "Calculate the derivative of x^2 + 3x + 1",
        "Solve the equation x^2 - 9 = 0",
        "Plot sin(x) from 0 to 2*pi",
        "Integrate x^3 from 0 to 1",
        "Find the critical points of x^3 - 3x^2 + 2",
        "Visualize the function cos(x) + sin(2x)",
        "Compute 2^10 + 5!",
    ]
    
    results = []
    
    for request in test_requests:
        result = agent.process_request(request)
        results.append(result)
        time.sleep(1)  # Small delay between requests
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SESSION SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Total requests processed: {total}")
    print(f"Successful executions: {successful}")
    print(f"Success rate: {successful/total*100:.1f}%")
    
    print(f"\nVariables defined: {list(agent.context['variables'].keys())}")
    print(f"Computations in history: {len(agent.context['computation_history'])}")
    
    return results


def demonstrate_conversational_flow():
    """Demonstrate conversational computational workflow."""
    
    print("\n" + "=" * 60)
    print("💬 Conversational Workflow Demonstration")
    print("=" * 60)
    
    agent = LLMAgent()
    agent.initialize()
    
    # Simulate a conversational flow
    conversation = [
        "Let's work with the function f(x) = x^3 - 3x^2 + 2",
        "Now find its derivative",
        "Plot both the original function and its derivative",
        "Find where the derivative equals zero",
        "What are the critical points?"
    ]
    
    print("🗣️  Simulating conversational computational session...")
    
    for i, utterance in enumerate(conversation, 1):
        print(f"\n👤 User {i}: {utterance}")
        
        # Process with context awareness
        result = agent.process_request(utterance)
        
        # In a real conversation, the agent would maintain
        # better context and reference previous computations
    
    print("\n🎉 Conversational session complete!")


if __name__ == "__main__":
    results = demonstrate_llm_agent()
    demonstrate_conversational_flow()