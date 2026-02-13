import os
from openai import OpenAI
import google.generativeai as genai
import json
from typing import Dict, Any

# Client wrapper
def get_llm_provider():
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if gemini_key:
        genai.configure(api_key=gemini_key)
        return "gemini", genai.GenerativeModel('gemini-1.5-flash')
    elif openai_key:
        return "openai", OpenAI(api_key=openai_key)
    else:
        return None, None

def generate_architecture_summary(graph_data: Dict[str, Any]) -> str:
    print("DEBUG: Generating Summary...")
    provider, client = get_llm_provider()
    
    if not client:
        print("DEBUG: No API Key found. Returning Mock Summary.")
        return "## Analysis Simulation (Fallback)\n\n**Note:** Real-time generation failed (Missing API Keys). Showing a simulated summary.\n\nPlease set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env`."

    repo_context = json.dumps(graph_data, indent=2)[:5000]
    
    system_prompt = """You are a Principal Software Architect. 
    Analyze the provided JSON representation of a codebase.
    Construct a high-level architectural summary.
    Identify pattern, key components, and data flow.
    Output concise Markdown."""

    full_prompt = f"{system_prompt}\n\nRepository Data:\n{repo_context}"

    try:
        if provider == "gemini":
            print("DEBUG: Using Gemini...")
            response = client.generate_content(full_prompt)
            return response.text
        else:
            # OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Repository Data:\n\n{repo_context}"}
                ],
                timeout=30
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"DEBUG: LLM Error ({provider}): {e}")
        return "## Analysis Simulation (Fallback)\n\n**Note:** Real-time generation failed. Showing a simulated summary.\n\nError details: " + str(e)

def generate_mermaid(graph_data: Dict[str, Any]) -> str:
    print("DEBUG: Generating Diagram...")
    provider, client = get_llm_provider()
    
    if not client:
        print("DEBUG: No API Key found. Returning Mock Diagram.")
        return get_mock_mermaid()

    repo_context = json.dumps(graph_data, indent=2)[:5000]
    
    system_prompt = """You are an expert in Mermaid.js diagram generation.
    Create a detailed Architecture diagram.
    Return ONLY the Mermaid code block (no markdown fences if possible, or inside ```mermaid)."""

    full_prompt = f"{system_prompt}\n\nRepository Data:\n{repo_context}"

    try:
        content = ""
        if provider == "gemini":
            print("DEBUG: Using Gemini...")
            response = client.generate_content(full_prompt)
            content = response.text
        else:
            # OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Repository Data:\n\n{repo_context}"}
                ],
                timeout=30
            )
            content = response.choices[0].message.content
            
        # Cleanup response
        if "```mermaid" in content:
            content = content.split("```mermaid")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content
            
    except Exception as e:
        print(f"DEBUG: LLM Error ({provider}): {e}")
        return get_mock_mermaid()

def get_mock_mermaid() -> str:
    return """graph TD;
    subgraph "Simulated Architecture"
        Client[Client / Frontend] --> API[API Gateway];
        API --> ServiceA[Auth Service];
        API --> ServiceB[Core Logic];
        ServiceB --> DB[(Database)];
        ServiceA --> Cache[(Redis)];
        
        classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
        classDef db fill:#e1f5fe,stroke:#0288d1;
        class DB,Cache db;
    end
    
    note right of API
        Live generation failed.
        Showing placebo structure.
    end"""
