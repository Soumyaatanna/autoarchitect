import httpx
import re
from typing import Dict, Any, List

GITHUB_API_BASE = "https://api.github.com"

def get_repo_details(repo_url: str) -> tuple[str, str]:
    """Extract owner and repo name from URL."""
    # Simplified regex for github.com URLs
    match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        raise ValueError("Invalid GitHub URL. Must be like https://github.com/owner/repo")
    return match.group(1), match.group(2)

def fetch_repo_content(repo_url: str, token: str = None) -> Dict[str, Any]:
    """
    Fetches file contents from GitHub API without cloning.
    Returns a dictionary structure suitable for LLM context.
    """
    owner, repo = get_repo_details(repo_url)
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    # 1. Get default branch tree (recursive)
    # First get the default branch name
    with httpx.Client() as client:
        repo_resp = client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=headers)
        if repo_resp.status_code != 200:
            raise Exception(f"Failed to access repo: {repo_resp.status_code} {repo_resp.text}")
        
        default_branch = repo_resp.json().get("default_branch", "main")
        
        # Get the tree
        tree_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        tree_resp = client.get(tree_url, headers=headers)
        if tree_resp.status_code != 200:
             raise Exception(f"Failed to fetch file tree: {tree_resp.status_code}")
             
        tree_data = tree_resp.json().get("tree", [])
        
        # 2. Filter relevant files
        # Limit the number of files to prevent blowing up the context window
        # Prioritize core logic files
        relevant_extensions = ('.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.java', '.rb', '.php', '.md', '.json')
        # Skip lock files, tests, etc. for brevity if needed, but keeping simple for now
        
        files_to_fetch = []
        for item in tree_data:
            if item["type"] == "blob" and item["path"].endswith(relevant_extensions):
                 # Basic heuristic to skip some large/irrelevant paths
                 if "node_modules" in item["path"] or "venv" in item["path"] or "dist" in item["path"] or ".git" in item["path"]:
                     continue
                 files_to_fetch.append(item)
        
        # reliable limit 50 files for MVP? Or strictly rely on token count (harder to know upfront)
        # Let's cap at 30 files for this iteration to be safe with rate limits and context
        files_to_fetch = files_to_fetch[:30] 
        
        file_contents = []
        
        # 3. Fetch content (Sequential for MVP to keep it simple and avoid rate limits burst)
        # Using the 'url' from the tree item which points to the blob API
        for file_item in files_to_fetch:
            # The blob API returns base64 or raw. 
            # Better to use raw. The 'url' field in tree is for the git blob.
            # We can use the raw content URL: https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
            # OR better, use the API to get content.
            # Let's use the API with raw media type header to avoid base64 decoding hassle if possible
            # GET /repos/{owner}/{repo}/contents/{path}
            
            # Using the blob URL from the tree item is efficient
            blob_url = file_item["url"]
            blob_resp = client.get(blob_url, headers=headers)
            
            if blob_resp.status_code == 200:
                # API returns base64 content in 'content' field, we need to decode
                import base64
                try:
                    content_b64 = blob_resp.json().get("content", "")
                    content = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                    file_contents.append({
                        "path": file_item["path"],
                        "content": content
                    })
                except Exception as e:
                    print(f"Failed to decode {file_item['path']}: {e}")
            
    return {
        "repo": repo_url,
        "files": file_contents,
        "structure_summary": f"Fetched {len(file_contents)} files from {owner}/{repo}."
    }

# Keep the same signature as before for compatibility, but ignore token if not needed/handled inside
def analyze_repo(repo_url: str, token: str = None) -> Dict[str, Any]:
    return fetch_repo_content(repo_url, token)
