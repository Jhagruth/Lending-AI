# risk_agent_api.py
# Final, consolidated version of the Python backend with robust error handling.

# --- Imports ---
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np
import sqlite3
from datetime import datetime
import pandas as pd
import joblib
import json
import os
import re
from botocore.exceptions import ClientError, ParamValidationError
from dotenv import load_dotenv

# --- Environment Loading ---
load_dotenv()

# --- Global Variables & Initialization ---
DB_NAME = "risk_assessments.db"
MODEL_FILE_NAME = "credit_model.joblib"
ml_model = None

# --- Pydantic Models for Data Validation ---
class CreditData(BaseModel):
    cibil_score: Optional[int] = Field(None, example=750)
    payment_history_score: float = Field(..., example=0.9)
    credit_utilization: float = Field(..., example=0.3)
    credit_history_months: int
    credit_types: int
    recent_inquiries: int

class FinancialData(BaseModel):
    annual_income: float
    total_debt: float
    current_assets: float
    current_liabilities: float
    total_assets: float
    total_equity: float
    net_income: float
    ebit: Optional[float] = None
    interest_expense: float
    inventory: Optional[float] = None

class EntityData(BaseModel):
    entity_name: str
    credit_data: CreditData
    financial_data: FinancialData

class BatchAssessmentRequest(BaseModel):
    entities: List[EntityData]

# --- Database Setup (Omitted for Brevity) ---
def init_db(): pass
def save_assessment(record_data): pass

# --- ML Model Functions (Omitted for Brevity) ---
def load_model():
    global ml_model
    try:
        ml_model = joblib.load(MODEL_FILE_NAME)
    except FileNotFoundError:
        print("Model file not found. API will use rule-based fallback.")
        ml_model = None

# --- Scoring & Logic Classes ---
class CreditScoringPipeline:
    def calculate_financial_ratios(self, financial_data: dict) -> dict:
        ratios = {}
        total_debt = financial_data.get('total_debt', 0)
        annual_income = financial_data.get('annual_income', 1)
        current_assets = financial_data.get('current_assets', 0)
        current_liabilities = financial_data.get('current_liabilities', 1)
        ratios['debt_to_income'] = total_debt / max(1, annual_income)
        ratios['current_ratio'] = current_assets / max(1, current_liabilities)
        return ratios

    def determine_risk_level(self, final_score: int) -> tuple[str, str]:
        if final_score >= 750: return "LOW", "#28a745"
        elif final_score >= 650: return "MEDIUM", "#ffc107"
        elif final_score >= 550: return "HIGH", "#fd7e14"
        else: return "VERY HIGH", "#dc3545"

    def run_scoring(self, credit_data: dict, financial_data: dict) -> dict:
        # FIX: Gracefully handle missing or None cibil_score
        base_score = credit_data.get('cibil_score')
        if base_score is None:
            base_score = 650 # Use a neutral default for new applicants

        score = base_score + (credit_data.get('payment_history_score', 0.8) - 0.8) * 100
        score -= credit_data.get('credit_utilization', 0.5) * 50
        final_score = min(850, max(300, int(score)))
        risk_level, risk_color = self.determine_risk_level(final_score)
        return {"credit_score": final_score, "risk_level": risk_level, "risk_color": risk_color}

# --- Bedrock Agent for AI Analysis ---
import boto3

class BedrockAgent:
    def __init__(self):
        self.bedrock_client = None
        try:
            region = os.environ.get("AWS_REGION")
            if not region: raise ValueError("AWS_REGION environment variable not set.")
            self.bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=region)
            self.model_id = 'amazon.titan-text-express-v1'
        except Exception as e:
            print(f"Error initializing Bedrock client: {e}")

    def _invoke_model(self, prompt: str) -> str:
        if not self.bedrock_client: raise ConnectionError("Bedrock client is not initialized.")
        body = json.dumps({"inputText": prompt, "textGenerationConfig": {"maxTokenCount": 1024, "temperature": 0.1, "topP": 1}})
        response = self.bedrock_client.invoke_model(body=body, modelId=self.model_id)
        response_body = json.loads(response.get('body').read())
        return response_body.get('results')[0].get('outputText')

    def _parse_json_from_response(self, response_text: str) -> dict:
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match: return json.loads(match.group(0))
        raise json.JSONDecodeError("No valid JSON found in AI response.", response_text, 0)

    def query_compliance(self, financial_ratios: dict) -> dict:
        prompt = f"""
        Analyze financial ratios: {json.dumps(financial_ratios)}. Is debt-to-income < 0.43? Is current ratio > 1.0?
        Respond with a single JSON object with keys: "compliance_score" (0-100), and "violations" (list of strings).
        JSON Response:
        """
        try:
            response_text = self._invoke_model(prompt)
            return self._parse_json_from_response(response_text)
        except (ClientError, ParamValidationError, json.JSONDecodeError, ConnectionError) as e:
            return {"compliance_score": 0, "violations": [f"Compliance Check Error: {str(e)}"]}

    def explain_risk_decision(self, credit_score: int, financial_ratios: dict, compliance_violations: list) -> dict:
        prompt = f"""
        As a loan advisor, explain a decision for a credit score of {credit_score}, ratios {json.dumps(financial_ratios)}, and violations ({', '.join(compliance_violations)}).
        Respond with a single JSON object with keys: "decision", "primary_explanation", "detailed_factors" (list), "suggestions_for_improvement" (list), and "confidence_score" (number).
        JSON Response:
        """
        try:
            response_text = self._invoke_model(prompt)
            parsed_json = self._parse_json_from_response(response_text)
            parsed_json.setdefault('detailed_factors', [])
            parsed_json.setdefault('suggestions_for_improvement', [])
            return parsed_json
        except (ClientError, ParamValidationError, json.JSONDecodeError, ConnectionError) as e:
            return {
                "decision": "Error", "primary_explanation": f"AI Explanation Failed: {str(e)}",
                "detailed_factors": [], "suggestions_for_improvement": [], "confidence_score": 0
            }

# --- Main Workflow Logic ---
def run_agentic_workflow(entity_data: EntityData, scoring_pipeline: CreditScoringPipeline, ai_agent: BedrockAgent) -> dict:
    credit_data_dict = entity_data.credit_data.dict()
    financial_data_dict = entity_data.financial_data.dict()
    
    risk_result = scoring_pipeline.run_scoring(credit_data_dict, financial_data_dict)
    financial_ratios = scoring_pipeline.calculate_financial_ratios(financial_data_dict)
    compliance_result = ai_agent.query_compliance(financial_ratios)
    explanation = ai_agent.explain_risk_decision(
        risk_result['credit_score'], financial_ratios, compliance_result.get('violations', []))
    
    return {
        'entity_name': entity_data.entity_name, 'credit_data': credit_data_dict,
        'financial_data': financial_data_dict, 'timestamp': datetime.now().isoformat(),
        **risk_result, 'financial_ratios': financial_ratios,
        'compliance_result': compliance_result, 'explanation': explanation,
    }

# --- FastAPI Application ---
app = FastAPI(title="Risk Agent API", description="Provides credit scoring and AI-driven explanations.")
scoring_pipeline = CreditScoringPipeline()
ai_agent = BedrockAgent()

@app.on_event("startup")
async def startup_event():
    init_db()
    load_model()

@app.post("/assess_batch/")
async def assess_batch(request: BatchAssessmentRequest):
    assessments = []
    for entity in request.entities:
        try:
            assessment = run_agentic_workflow(entity, scoring_pipeline, ai_agent)
            assessments.append(assessment)
        except Exception as e:
            assessments.append({
                "entity_name": entity.entity_name, 
                "error": f"Workflow Error: {str(e)}",
                "credit_score": 0, "risk_level": "ERROR", "risk_color": "#dc3545",
                "credit_data": entity.credit_data.dict(), "financial_data": entity.financial_data.dict(),
                "financial_ratios": {}, 
                "compliance_result": {"compliance_score": 0, "violations": ["Workflow error"]}, 
                "explanation": {"decision": "Error", "primary_explanation": str(e), "detailed_factors": [], "suggestions_for_improvement": [], "confidence_score": 0},
                "timestamp": datetime.now().isoformat()
            })
    return assessments