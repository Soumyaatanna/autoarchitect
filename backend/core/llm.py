import os
from openai import OpenAI
import google.generativeai as genai
import json
from typing import Dict, Any

# Client wrapper
def get_llm_provider():
    """Return (provider_name, client) based on available API keys.

    - Prefers Gemini (GEMINI_API_KEY or GOOGLE_API_KEY)
    - Falls back to OpenAI (OPENAI_API_KEY)
    - Gemini model names are configurable via env:
      GEMINI_MODEL (default: gemini-1.5-flash-latest)
    """

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        genai.configure(api_key=gemini_key)
        # The SDK expects full model IDs like "models/gemini-flash-latest".
        # Default to a general-purpose flash model that supports generateContent.
        model_name = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")
        return "gemini", genai.GenerativeModel(model_name)
    elif openai_key:
        return "openai", OpenAI(api_key=openai_key)
    else:
        return None, None

def call_gemini_with_fallback(client, prompt):
    """Call Gemini, falling back to a secondary model if the primary is unsupported."""
    try:
        return client.generate_content(prompt).text
    except Exception as e:
        msg = str(e)
        if "404" in msg or "not found" in msg.lower():
            fallback_name = os.getenv("GEMINI_FALLBACK_MODEL", "models/gemini-pro-latest")
            print(f"DEBUG: Primary model failed ({e}). Retrying with {fallback_name} ...")
            try:
                fallback_client = genai.GenerativeModel(fallback_name)
                return fallback_client.generate_content(prompt).text
            except Exception as e2:
                print(f"DEBUG: Fallback model failed: {e2}")
                # Propagate original error so the UI shows the first failure.
                raise e
        raise e

def generate_architecture_summary(graph_data: Dict[str, Any]) -> str:
    print("DEBUG: Generating Summary...")
    provider, client = get_llm_provider()
    
    if not client:
        print("DEBUG: No API Key found. Returning Mock Summary.")
        return "## Analysis Simulation (Fallback)\n\n**Note:** Real-time generation failed (Missing API Keys). Showing a simulated summary.\n\nPlease set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env`."

    # Prepare prompt with raw file contents
    # graph_data now contains {"repo": ..., "files": [{"path": ..., "content": ...}]}
    
    file_context = ""
    if "files" in graph_data:
        for f in graph_data["files"]:
            file_context += f"File: {f['path']}\n```\n{f['content']}\n```\n\n"
    else:
        # Fallback if old format
        file_context = json.dumps(graph_data, indent=2)
            
    repo_context = file_context[:50000] # Increase limit since we are sending code. Gemini 1.5 has large window.
    
    system_prompt = """You are a Principal Software Architect. 
    Analyze the provided source code of a repository.
    Construct a high-level architectural summary.
    Identify patterns, key components, and data flow.
    Output concise Markdown."""

    full_prompt = f"{system_prompt}\n\nRepository Source Code:\n{repo_context}"

    try:
        if provider == "gemini":
            print("DEBUG: Using Gemini...")
            return call_gemini_with_fallback(client, full_prompt)
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

    # Prepare prompt with raw file contents
    file_context = ""
    if "files" in graph_data:
        for f in graph_data["files"]:
            file_context += f"File: {f['path']}\n```\n{f['content']}\n```\n\n"
    else:
        file_context = json.dumps(graph_data, indent=2)
            
    repo_context = file_context[:50000]
    
    system_prompt = """You are an expert in Mermaid.js diagram generation.
    Create a detailed Architecture diagram based on the source code.
    Use subgraphs for modules/folders.
    Return ONLY the Mermaid code block (no markdown fences if possible, or inside ```mermaid)."""

    full_prompt = f"{system_prompt}\n\nRepository Source Code:\n{repo_context}"

    try:
        content = ""
        if provider == "gemini":
            print("DEBUG: Using Gemini...")
            content = call_gemini_with_fallback(client, full_prompt)
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
