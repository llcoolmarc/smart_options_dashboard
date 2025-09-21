# oauth_cli.py — one-shot OAuth that avoids local callback hassles.
# It guides you, opens the login page, you paste back the URL with ?code=..., and it saves tokens.
# After it saves tokens, it verifies your login and lists your accounts.

from __future__ import annotations
import os, json, time, webbrowser
from urllib.parse import urlencode, urlsplit, parse_qs

import requests

TOKEN_PATH = "data/tastytrade_token.json"

def prompt(msg, default=None):
    if default:
        v = input(f"{msg} [{default}]: ").strip()
        return v or default
    return input(f"{msg}: ").strip()

def build_auth_url(base: str, client_id: str, redirect_uri: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "offline_access",
        "state": "x"
    }
    return f"{base}/oauth/authorize?" + urlencode(params)

def exchange_code(base: str, client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    token_url = f"{base}/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    r = requests.post(token_url, data=data, timeout=30)
    if r.status_code >= 400:
        raise SystemExit(f"[exchange] HTTP {r.status_code}: {r.text}")
    j = r.json()
    return {
        "access_token": j.get("access_token"),
        "refresh_token": j.get("refresh_token"),
        "expires_at": time.time() + float(j.get("expires_in", 1800))
    }

def verify_me(base: str, access_token: str) -> dict:
    url = f"{base}/customers/me"
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    r.raise_for_status()
    return r.json()

def list_accounts(base: str, access_token: str) -> int:
    url = f"{base}/customers/me/accounts"
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    r.raise_for_status()
    j = r.json()
    items = (j.get("data") or {}).get("items", [])
    return len(items)

def main():
    os.makedirs(os.path.dirname(TOKEN_PATH) or ".", exist_ok=True)

    # 1) Choose environment (CERT or PROD)
    env = prompt("Environment CERT or PROD", "CERT").upper()
    if env not in {"CERT", "PROD"}:
        raise SystemExit("Please type CERT or PROD")
    base = "https://api.cert.tastytrade.com" if env == "CERT" else "https://api.tastytrade.com"

    # 2) Credentials and redirect (must match your app’s registered redirect)
    client_id = prompt("Client ID")
    client_secret = prompt("Client Secret")
    redirect_uri = prompt("Redirect URI (must match your app)", "http://localhost:8080/callback")

    # 3) Build & open the login page
    auth_url = build_auth_url(base, client_id, redirect_uri)
    print("\n[oauth] Opening browser to:\n", auth_url, "\n")
    webbrowser.open(auth_url)

    print("After you log in and click Approve, the browser may say 'site can't be reached' — that's OK.")
    pasted = prompt("Paste the FULL URL from your browser address bar (it contains ?code=...)")
    qs = urlsplit(pasted).query
    code = parse_qs(qs).get("code", [None])[0]
    if not code:
        raise SystemExit("No ?code= found. Make sure you pasted the entire URL after approving.")

    # 4) Exchange, save, verify
    tokens = exchange_code(base, client_id, client_secret, redirect_uri, code)
    with open(TOKEN_PATH, "w") as f:
        json.dump(tokens, f)
    print(f"[ok] Saved tokens to {TOKEN_PATH}")

    # 5) Verify who you are and count accounts
    me = verify_me(base, tokens["access_token"])
    acct_count = list_accounts(base, tokens["access_token"])
    print("[ok] Verified /customers/me:", bool(me))
    print(f"[ok] Accounts count: {acct_count}")

    print("\nAll set. Run:\n  python broker_diag.py\n  python app.py\n")

if __name__ == "__main__":
    main()
