from dataclasses import dataclass


@dataclass(slots=True)
class Project:
    name: str
    completed: bool


@dataclass(slots=True)
class Log:
    date: str
    action: str


@dataclass(slots=True)
class Team:
    name: str
    leader: bool
    projects: list[Project]

    # def __post_init__(self):
    #     self.projects = [Project(**project) for project in self.projects]


@dataclass(slots=True)
class User:
    id: str
    name: str
    age: int
    score: int
    active: bool
    country: str
    team: Team
    logs: list[Log]

    # def __post_init__(self):
    #     self.team = Team(**self.team)
    #     self.logs = [Log(**log) for log in self.logs]
