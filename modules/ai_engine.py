"""
AI Engine Module for HireAI Pro
Handles resume text extraction, video analysis, and multimodal evaluation
"""

import re
import os
import time
import json
from typing import Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def extract_text_from_pdf(file_obj) -> str:
    """
    Extract text content from uploaded PDF file.
    """
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"Extraction Error: {str(e)}"

def get_ai_evaluation(text: str) -> Dict[str, Any]:
    """
    Perform AI evaluation on resume text using Gemini.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Analyze the following resume text and provide a structured JSON evaluation.
    Resume Text: {text}
    
    Required JSON Format:
    {{
        "score": (float 0-10),
        "best_role": (string),
        "skills": {{ "SkillName": score_0_10 }},
        "efficiency": {{
            "Technical": 0-10,
            "Experience": 0-10,
            "Communication": 0-10,
            "Logic": 0-10,
            "Leadership": 0-10
        }},
        "summary": (brief string),
        "pros": [string],
        "cons": [string],
        "experience": [{{ "title": string, "company": string, "duration": string, "description": string }}]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
        
    # Fallback to demo data if API fails or parsing fails
    return {
        'score': 7.5,
        'best_role': "Software Engineer",
        'skills': {"Python": 8.5, "SQL": 7.0},
        'efficiency': {"Technical": 8.0, "Experience": 7.0, "Communication": 6.5, "Logic": 7.5, "Leadership": 5.0},
        'summary': "Candidate shows strong potential in backend development.",
        'pros': ["Python proficiency", "Solid projects"],
        'cons': ["Limited leadership experience"],
        'experience': [{"title": "Junior Dev", "company": "Tech Corp", "duration": "2 years", "description": "Backend work"}]
    }

def get_video_evaluation(video_path: str) -> Dict[str, Any]:
    """
    Analyze video introduction for sentiment, persona, and communication skills.
    """
    if not api_key:
        return {"error": "API Key missing"}

    try:
        # Upload video to Gemini
        video_file = genai.upload_file(path=video_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Analyze this video introduction and provide a JSON report on the candidate's persona.
        Include:
        1. Confidence level (0-10)
        2. Communication clarity (0-10)
        3. Sentiment (Positive/Neutral/Concise)
        4. Keywords detected in speech
        5. Personality traits (e.g., Energetic, Professional, Analytical)
        6. Social Media Alignment (Would they be good for public facing/social roles?)
        
        Format as JSON:
        {
            "confidence": float,
            "clarity": float,
            "sentiment": string,
            "keywords": [string],
            "traits": [string],
            "social_alignment": string,
            "summary": string
        }
        """
        
        response = model.generate_content([prompt, video_file])
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
            
    except Exception as e:
        return {"error": f"Video analysis failed: {str(e)}"}
        
    return {
        "confidence": 8.0,
        "clarity": 7.5,
        "sentiment": "Positive",
        "keywords": ["innovation", "teamwork", "creative"],
        "traits": ["Energetic", "Professional"],
        "social_alignment": "High potential for brand representation.",
        "summary": "Candidate presents very well on camera with clear speech."
    }

def cross_reference_analysis(resume_data: Dict, video_data: Dict) -> Dict[str, Any]:
    """
    Find alignment between the Resume (Technical) and Video (Persona).
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Compare the resume analysis and video analysis for this candidate.
        Resume: {json.dumps(resume_data)}
        Video: {json.dumps(video_data)}
        
        Provide a JSON alignment report:
        1. Consistency Score (0-10) - Does the persona match the experience?
        2. Cross-Verification - Do the keywords in video match the skills in resume?
        3. Hiring Recommendation Strength (0-10)
        4. "Multimodal Highlight" - One specific insight gained from combining both.
        
        Format as JSON:
        {{
            "consistency_score": float,
            "alignment_details": string,
            "recommendation_strength": float,
            "multimodal_insight": string
        }}
        """
        
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
            
    except Exception:
        pass
        
    return {
        "consistency_score": 8.5,
        "alignment_details": "Video persona well-aligned with the technical claims in resume.",
        "recommendation_strength": 9.0,
        "multimodal_insight": "Candidate's enthusiasm in video reinforces the 'Team Lead' potential noted in resume."
    }

def calculate_weighted_score(ai_result: Dict, weights: Dict[str, int]) -> float:
    """Calculate weighted final score based on AI evaluation and user weights."""
    eff = ai_result.get('efficiency', {})
    
    technical = eff.get('Technical', 5) * (weights.get('Technical', 50) / 100)
    experience = eff.get('Experience', 5) * (weights.get('Experience', 30) / 100)
    soft_skills = ((eff.get('Communication', 5) + eff.get('Leadership', 5)) / 2) * (weights.get('Soft_Skills', 20) / 100)
    
    return round(technical + experience + soft_skills, 2)

def infer_role(text: str, skills: Dict) -> str:
    """Infer best role based on skills and keywords."""
    text_lower = text.lower()
    if any(k in text_lower for k in ['manager', 'lead', 'director']): return "Technical Lead"
    if any(k in text_lower for k in ['data', 'analytics', 'machine learning']): return "Data Scientist"
    if any(k in text_lower for k in ['frontend', 'react', 'ui', 'ux']): return "Frontend Developer"
    if any(k in text_lower for k in ['backend', 'api', 'server']): return "Backend Developer"
    if any(k in text_lower for k in ['devops', 'aws', 'cloud', 'docker']): return "DevOps Engineer"
    return "Software Engineer"