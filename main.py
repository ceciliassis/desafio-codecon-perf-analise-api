import orjson
import time

from functools import wraps
from collections import Counter
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


class Database:
    def __init__(self, users=None):
        self.users = users or []


app = FastAPI()
db = Database()
client = TestClient(app)


def timestamp(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter() - start

        result["timestamp"] = datetime.now()
        result["execution_time_ms"] = round(end * 1e3)

        return result

    return wrapper


@app.post("/users")
async def load_users(request: Request):
    users = await request.body()
    db.users = orjson.loads(users)

    return {
        "message": "Arquivo recebido com sucesso",
        "user_count": len(db.users),
    }


@app.get("/superusers")
@timestamp
def get_superusers():
    superusers = [user for user in db.users if user["score"] >= 900 and user["active"]]

    return {
        "data": superusers,
    }


@app.get("/top-countries")
@timestamp
def get_top_countries():
    superusers = get_superusers()["data"]

    top_countries = Counter([user["country"] for user in superusers])
    top_countries = [
        {"country": country, "total": total}
        for country, total in top_countries.most_common(5)
    ]

    return {"countries": top_countries}


@app.get("/team-insights")
@timestamp
def get_team_insights():
    active_members = [user["team"]["name"] for user in db.users if user["active"]]
    active_members = Counter(active_members)

    team_members = [user["team"]["name"] for user in db.users]
    team_members = Counter(team_members)

    team_leaders = [user["team"]["name"] for user in db.users if user["team"]["leader"]]
    team_leaders = Counter(team_leaders)

    completed_projects = [
        user["team"]["name"]
        for user in db.users
        for project in user["team"]["projects"]
        if project["completed"]
    ]
    completed_projects = Counter(completed_projects)

    teams = [
        {
            "team": team,
            "total_members": total_members,
            "leaders": team_leaders[team],
            "completed_projects": completed_projects[team],
            "active_percentage": round(active_members[team] / total_members * 100, 2),
        }
        for team, total_members in team_members.items()
    ]

    return {"teams": teams}


@app.get("/active-users-per-day")
@timestamp
def get_active_users_per_day(min=3000):
    logins = [
        log["date"]
        for user in db.users
        for log in user["logs"]
        if log["action"] == "login"
    ]
    logins = Counter(logins)
    logins = [
        {"date": date, "total": total} for date, total in logins.items() if total >= min
    ]

    return {"logins": logins}


@app.get("/evaluation")
def get_evaluation():
    endpoints = [
        "get_superusers",
        "get_top_countries",
        "get_team_insights",
        "get_active_users_per_day",
    ]

    tested_endpoints = {}

    for endpoint in endpoints:
        response = client.get(app.url_path_for(endpoint))

        tested_endpoints[endpoint] = {
            "time_ms": response.json()["execution_time_ms"],
            "status": response.status_code,
            "valid_response": response.headers["content-type"] == "application/json",
        }

    return {"tested_endpoints": tested_endpoints}
