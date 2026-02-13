import os
import ast
import tempfile
import shutil
import git
from typing import Dict, Any, List
import re

def clone_repo(repo_url: str, token: str = None) -> str:
    """Clones a git repo to a temp directory and returns the path."""
    temp_dir = tempfile.mkdtemp(prefix="autoarchitect_")
    
    # Simple auth insertion for MVP if token provided
    if token and "github.com" in repo_url:
        auth_url = repo_url.replace("https://", f"https://{token}@")
    else:
        auth_url = repo_url
        
    try:
        git.Repo.clone_from(auth_url, temp_dir, depth=1)
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir) # Cleanup on fail
        raise e

def parse_python_file(file_path: str, rel_path: str) -> Dict[str, Any]:
    """Extracts imports, classes, functions, and framework hints from Python files."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"error": "SyntaxError", "path": rel_path}

    imports = []
    classes = []
    functions = []
    framework_hints = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
            # Check for framework patterns like Pydantic models or Django models
            for base in node.bases:
                if isinstance(base, ast.Name):
                   if base.id in ["BaseModel", "Model"]:
                       framework_hints.append(f"Model: {node.name}")
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
            # Check for decorators (FastAPI/Flask)
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    # e.g., @app.get("/")
                    if dec.func.attr in ["get", "post", "put", "delete"]:
                        framework_hints.append(f"Route: {dec.func.attr.upper()} {node.name}")

    return {
        "language": "python",
        "path": rel_path,
        "imports": list(set(imports)),
        "classes": classes,
        "functions": functions,
        "hints": framework_hints
    }

def parse_js_file(file_path: str, rel_path: str) -> Dict[str, Any]:
    """Regex-based extraction for JS/TS (MVP) to avoid complex parsers."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    imports = []
    # Simple regex for imports: import x from 'y' or const x = require('y')
    import_matches = re.findall(r'import\s+.*?from\s+[\'"](.*?)[\'"]', content)
    require_matches = re.findall(r'require\s*\(\s*[\'"](.*?)[\'"]\s*\)', content)
    imports.extend(import_matches)
    imports.extend(require_matches)
    
    # Clean up imports (remove relative paths for high-level graph usually, but keep for local linkage)
    
    hints = []
    if "react" in content.lower():
        hints.append("React Component?")
    if "express" in content.lower():
        hints.append("Express App?")

    return {
        "language": "javascript/typescript",
        "path": rel_path,
        "imports": list(set(imports)),
        "hints": hints
    }

def remove_readonly(func, path, excinfo):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, 0o777)
    func(path)

def analyze_repo(repo_url: str, token: str = None) -> Dict[str, Any]:
    """Orchestrates the cloning and parsing."""
    temp_dir = clone_repo(repo_url, token)
    
    file_nodes = []
    
    try:
        for root, _, files in os.walk(temp_dir):
            if ".git" in root:
                continue
            
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, temp_dir)
                
                if file.endswith(".py"):
                    file_nodes.append(parse_python_file(full_path, rel_path))
                elif file.endswith((".js", ".jsx", ".ts", ".tsx")):
                    file_nodes.append(parse_js_file(full_path, rel_path))
                # Add generic file info for others?
    finally:
        # Robust cleanup for Windows
        shutil.rmtree(temp_dir, onerror=remove_readonly)
        
    return {
        "repo": repo_url,
        "files": file_nodes,
        "structure_summary": f"Analyzed {len(file_nodes)} supported files."
    }
