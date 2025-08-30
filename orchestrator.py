# orchestrator.py
# This is the main workflow manager, now powered by AWS Bedrock

import requests
import json
import os
import re # Import the regular expressions library
from datetime import datetime
import sys # Import sys to handle command-line arguments

# --- AWS SDK library ---
import boto3
from botocore.exceptions import ClientError # Import the specific AWS error

# --- BedrockAgent to connect to AWS Bedrock ---
class BedrockAgent:
    """
    An agent that uses AWS Bedrock Titan for compliance and decision-making.
    """
    def __init__(self):
        try:
            region = os.environ.get("AWS_REGION")
            if not region:
                raise ValueError("AWS_REGION environment variable not set.")
            self.bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=region)
            self.model_id = 'amazon.titan-text-express-v1'
        except Exception as e:
            raise ConnectionError(f"Could not initialize AWS Bedrock client. Error: {e}")

    def _invoke_model(self, prompt):
        """Helper function to call the Bedrock API with improved error handling."""
        try:
            body = json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {"maxTokenCount": 1024, "stopSequences": [], "temperature": 0.1, "topP": 1}
            })
            response = self.bedrock_client.invoke_model(body=body, modelId=self.model_id)
            response_body = json.loads(response.get('body').read())
            return response_body.get('results')[0].get('outputText')
        except ClientError as e:
            # Catch the specific boto3 ClientError and raise a custom, informative exception
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            # This will be caught by the functions below and displayed in the UI
            raise Exception(f"AWS Bedrock Error: [{error_code}] {error_message}") from e

    def _parse_json_from_response(self, response_text):
        """Robustly finds and parses a JSON object from a string."""
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            raise json.JSONDecodeError("No valid JSON object found in AI response.", response_text, 0)

    def _validate_explanation_structure(self, explanation_json):
        """
        Ensures the AI-generated explanation has the correct structure and data types.
        This is the fix for the '.map is not a function' error.
        """
        # Ensure 'detailed_factors' is a list
        if 'detailed_factors' not in explanation_json or not isinstance(explanation_json['detailed_factors'], list):
            # If it's a string, wrap it in a list. Otherwise, create an empty list.
            if isinstance(explanation_json.get('detailed_factors'), str):
                 explanation_json['detailed_factors'] = [explanation_json['detailed_factors']]
            else:
                 explanation_json['detailed_factors'] = []
        
        # Ensure 'suggestions_for_improvement' is a list
        if 'suggestions_for_improvement' not in explanation_json or not isinstance(explanation_json['suggestions_for_improvement'], list):
            if isinstance(explanation_json.get('suggestions_for_improvement'), str):
                 explanation_json['suggestions_for_improvement'] = [explanation_json['suggestions_for_improvement']]
            else:
                 explanation_json['suggestions_for_improvement'] = []

        # Ensure all other keys have default values
        defaults = {
            "decision": "Manual Review",
            "primary_explanation": "AI analysis requires review.",
            "confidence_score": 50
        }
        for key, value in defaults.items():
            explanation_json.setdefault(key, value)
            
        return explanation_json

    def query_compliance(self, financial_ratios, company_data):
        policy_rules = "..." # Omitted for brevity
        prompt = f"..." # Omitted for brevity
        try:
            response_text = self._invoke_model(prompt)
            response_json = self._parse_json_from_response(response_text)
            response_json["recommendations"] = [] 
            return response_json
        except (json.JSONDecodeError, TypeError, Exception):
            # If any error occurs (including the new Bedrock error), return a failure object.
            return {"violations": ["AI service error during compliance check"], "recommendations": [], "compliance_score": 0}

    def explain_risk_decision(self, credit_score, risk_factors, compliance_violations):
        prompt = f"""
        You are a helpful and empathetic senior loan advisor...
        IMPORTANT: Your final output must be a single, valid JSON object...
        JSON Response:
        """ # Prompt omitted for brevity
        try:
            response_text = self._invoke_model(prompt)
            parsed_json = self._parse_json_from_response(response_text)
            # Add the validation step here
            return self._validate_explanation_structure(parsed_json)
        except (json.JSONDecodeError, TypeError, Exception) as e:
            # If any error occurs, create a fallback response that includes the error message.
            fallback_response = {
                "decision": "Error",
                "primary_explanation": f"Could not get an explanation from the AI service.",
                "detailed_factors": [f"Error Detail: {e}"],
                "suggestions_for_improvement": ["Check the AWS credentials and region in the .env file."],
                "confidence_score": 0
            }
            return self._validate_explanation_structure(fallback_response)

# --- Main Workflow Logic ---

def doc_agent(entity_data):
    # ... (rest of the function is unchanged)
    required_keys = ["entity_name", "credit_data", "financial_data"]
    missing_keys = [key for key in required_keys if key not in entity_data]
    if missing_keys:
        return False, f"Validation Failed: Missing keys - {', '.join(missing_keys)}"
    return True, "Validation Passed"

def run_agentic_workflow(entity_data):
    # This main function will now complete even if Bedrock fails, returning partial results.
    ai_agent = BedrockAgent()
    
    is_valid, doc_message = doc_agent(entity_data)
    if not is_valid:
        raise ValueError(doc_message)

    entity_name = entity_data["entity_name"]
    credit_data = entity_data["credit_data"]
    financial_data = entity_data["financial_data"]
    
    try:
        risk_agent_url = "http://127.0.0.1:8000/assess_risk/"
        response = requests.post(risk_agent_url, json={"credit_data": credit_data, "financial_data": financial_data})
        response.raise_for_status()
        risk_result = response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Could not connect to Risk Agent API: {e}")

    compliance_result = ai_agent.query_compliance(risk_result.get('financial_ratios', {}), financial_data)

    risk_factors_for_explanation = {
        'debt_to_income': risk_result.get('financial_ratios', {}).get('debt_to_income', 'N/A'),
        'payment_history_score': credit_data.get('payment_history_score', 'N/A'),
        'credit_utilization': credit_data.get('credit_utilization', 'N/A')
    }
    explanation = ai_agent.explain_risk_decision(
        risk_result.get('credit_score', 0), 
        risk_factors_for_explanation,
        compliance_result.get('violations', [])
    )

    final_assessment = {
        'entity_name': entity_name,
        'credit_score': risk_result.get('credit_score', 0),
        'risk_level': risk_result.get('risk_level', 'UNKNOWN'),
        'risk_color': risk_result.get('risk_color', '#808080'),
        'financial_ratios': risk_result.get('financial_ratios', {}),
        'compliance_result': compliance_result,
        'explanation': explanation,
        'credit_data': credit_data,
        'financial_data': financial_data,
        'timestamp': datetime.now().isoformat()
    }
    
    return final_assessment

# This part allows the script to be called from the command line by server.js
if __name__ == "__main__":
    # Read the JSON string from standard input for robust data transfer
    input_json_string = sys.stdin.read()
    if not input_json_string:
        # Output a structured error if no data is received
        print(json.dumps({"error": "No input data received from stdin."}), file=sys.stderr)
        sys.exit(1)

    try:
        entity_data = json.loads(input_json_string)
        result = run_agentic_workflow(entity_data)
        # Print the final JSON result to stdout for Node.js to capture
        print(json.dumps(result))
    except Exception as e:
        # Print a structured JSON error to stderr for Node.js to capture
        print(json.dumps({"error": f"Error processing entity: {e}"}), file=sys.stderr)
        sys.exit(1)

