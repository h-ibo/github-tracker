import os
import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def fetch_repo_commits_async(owner: str, repo_name: str, client: httpx.AsyncClient):
    """
    GitHub reposunun son commit'lerini asenkron (eşzamanlı) çeker.
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}/commits"
    
    headers = {
        "Accept": "application/vnd.github+json",
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    print(f"[*] Async sorgu atılıyor: {url}")
    
    # await ile isteğin asenkron olarak tamamlanmasını bekliyoruz
    response = await client.get(url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    
    return response.json()