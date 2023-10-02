"""TGS API to python connector. Do not report bugs please."""
import base64
from datetime import datetime
import json
import requests
import pytz

from config import TGS_ADDRESS, TGS_LOGIN, TGS_PASS, GITHUB_USER, GITHUB_PAT

bearer_valid_until = datetime.utcnow().replace(tzinfo=pytz.utc)
bearer = {"Authorization": "fixme"}
default_headers = {"accept": "application/json",
                   "User-Agent": "Amogus/1.0.0.0", "Api": "Tgstation.Server.Api/9.12.0"}
auth_header: str


def make_token(tgs_login, tgs_pass) -> str:
    """Will not change, no reason to call more than once.
    """
    auth_string = tgs_login + ':' + tgs_pass
    auth_bytes = auth_string.encode('utf-8')
    return {"Authorization": "Basic "+(base64.b64encode(auth_bytes).decode('utf-8'))}


def auth():
    """POST / Authorization: Basic ...
    Updates global bearer.
    Returns bearer dict to update headers with, 
    but we don't really need it as func also updates global bearer."""
    # pylint: disable-next=global-statement
    global bearer_valid_until, auth_header
    auth_header = make_token(TGS_LOGIN, TGS_PASS)
    headers = default_headers | auth_header
    response = requests.post(
        url=TGS_ADDRESS + "/", headers=headers, timeout=1000)
    response_json = response.json()
    bearer_valid_until = datetime.fromisoformat(response_json['expiresAt'])
    print(bearer_valid_until)
    response_json.pop('expiresAt')
    bearer["Authorization"] = "Bearer " + response_json["bearer"]
    return bearer


def check_auth():
    """Check if bearer still valid, reauth if not, then return.
    """
    if bearer_valid_until < datetime.utcnow().replace(tzinfo=pytz.utc) \
            or bearer == {"Authorization": "fixme"}:
        auth()
        return bearer
    else:
        return bearer


def get_instances():
    """GET /Instance/List
    Requires auth and ViewGlobalSomething perm.
    Returns only attached instances.
    """
    check_auth()
    headers = default_headers | bearer
    print(headers)
    response = requests.get(
        url=TGS_ADDRESS + '/Instance/List', headers=headers, timeout=1000)
    x = json.loads(json.dumps(response.json()))
    y = []
    for i in range(x["totalItems"]):
        y.append({"id": x["content"][i]["id"],
                  "name": x["content"][i]["name"],
                  "online": x["content"][i]["online"]})
    return y


def get_instance(inst_id: int):
    """GET /Instance/{id}
    Requires perms for provided instance.
    Will give 410 if instance detached/does not exist. I don't care."""
    check_auth()
    headers = default_headers | bearer
    response = requests.get(
        url=TGS_ADDRESS + f"/Instance/{inst_id}", headers=headers, timeout=1000)
    x = json.loads(json.dumps(response.json()))
    return x


def get_active_jobs():
    """GET /Job
    Returns only active jobs, UNLIKE /Job/List, which returns ALL PAST AND CURRENT jobs.
    No idea why we would need this but fuck it.
    """
    check_auth()
    headers = default_headers | bearer
    response = requests.get(
        url=TGS_ADDRESS + "/Job", headers=headers, timeout=1000)
    x = json.loads(json.dumps(response.json()))
    return x


def git_pull_repo_for_inst(inst_id: int, *commit_sha: str):
    """POST /Repository/{id}
    git pull at it's finest
    Cool parameters: {   
        "checkoutSha": "string",    } 
                                    } Can be only one of those. updateFromOrigin will pull latest commit, checkoutSha - commit by full SHA
        "updateFromOrigin": true,   } 

        "accessUser": "string",     - Should be token owner
        "accessToken": GITHUB_PAT   - Github PAT
    }  
    """
    check_auth()
    headers = default_headers | bearer
    params = {"accessUser": GITHUB_USER, "accessToken": GITHUB_PAT}
    params = params | {
        "checkoutSha": commit_sha} if commit_sha else params | {"updateFromOrigin": "true"}
    response = requests.post(
        url=TGS_ADDRESS + f"/Repository/{inst_id}", headers=headers, params=params, timeout=1000)
    return response.json()

  def start(inst_id: int):
    """PUT /DreamDaemon 
    Header Instance: {inst_id}
    """
    inst = {"Instance": inst_id}
    check_auth()
    headers = default_headers | bearer | inst
    response = requests.put(
        url=TGS_ADDRESS + "/DreamDaemon", headers=headers, timeout=1000)
    return response.json()

  def stop(inst_id: int):
    """DELETE /DreamDaemon
    Header Instance: {inst_id}
    """
    inst = {"Instance": inst_id}
    headers = default_headers | bearer | inst
    response = requests.delete(
        url=TGS_ADDRESS + "/DreamDaemon", headers=headers, timeout=1000)
    return response.json()
