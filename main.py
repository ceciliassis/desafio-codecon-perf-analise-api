import orjson

from collections import Counter
from datetime import datetime
from itertools import chain

from fastapi import FastAPI, Request, status


class Service:
    def __init__(self, users=[]):
        self.users = users


app = FastAPI()
service = Service()


def timestamp(func):
    def wrapper():
        start = datetime.now()
        result = func()
        end = datetime.now() - start

        result["timestamp"] = start
        result["execution_time_ms"] = round(
            float(str(end * 1e3).split(":")[-1])
        )  # milisseconds = 1e3 == 1000

        return result

    return wrapper


@app.post("/users")
async def load_users(request: Request):
    users = await request.body()
    service.users = orjson.loads(users)

    return {
        "message": "Arquivo recebido com sucesso",
        "user_count": len(service.users),
    }


@app.get("/superusers")
@timestamp
def get_superusers():
    superusers = [
        user for user in service.users if user["score"] >= 900 and user["active"]
    ]

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
        for country, total in top_countries.most_common()
    ]

    return {"countries": top_countries}


@app.get("/team-insights")
@timestamp
def get_team_insights():
    active_members = [user["team"]["name"] for user in service.users if user["active"]]
    active_members = Counter(active_members)

    team_members = [user["team"]["name"] for user in service.users]
    team_members = Counter(team_members)

    team_leaders = [
        user["team"]["name"] for user in service.users if user["team"]["leader"]
    ]
    team_leaders = Counter(team_leaders)

    completed_projects = [
        user["team"]["name"]
        for user in service.users
        for project in user["team"]["projects"]
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
def get_active_users_per_day(min=0):
    logins = chain.from_iterable(map(lambda user: user["logs"], service.users))
    logins = [login["date"] for login in logins if login["action"] == "login"]
    logins = Counter(logins)
    logins = [
        {"date": date, "total": total} for date, total in logins.items() if total >= min
    ]

    return {"logins": logins}


@app.get("/evaluation")
def get_evaluation():
    tested_endpoints = {}

    for route in app.routes:
        if route.name == "wrapper":
            path = route.path
            func = "get" + path.replace("/", "_").replace("-", "_")

            tested_endpoints[path] = {
                "status": status.HTTP_200_OK,
                "time_ms": 0,
                "valid_response": True,
            }

            try:
                result = eval(func)()
                tested_endpoints[path]["time_ms"] = result["execution_time_ms"]
            except:
                tested_endpoints[path]["status"] = status.HTTP_500_INTERNAL_SERVER_ERROR
                tested_endpoints[path]["valid_response"] = False

    return {"tested_endpoints": tested_endpoints}
