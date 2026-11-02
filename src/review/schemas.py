from enum import Enum
from pydantic import BaseModel,Field

class Severity(str,Enum):
    LOW="LOW"
    MEDIUM="MEDIUM"
    HIGH="HIGH"
    CRITICAL="CRITICAL"

class Category(str,Enum):
    BUG="Bug"
    SECURITY="Security"
    PERFORMANCE="Performance"
    MAINTAINABILITY="Maintainability"
    STYLE="Style"
    BEST_PRACTICE="Best Practice"

class ReviewIssue(BaseModel):
    severity:Severity
    category:Category
    title:str
    description:str
    suggestion:str
    file:str
    line:int | None=None

class ReviewResult(BaseModel):
    summary:str
    issues:list[ReviewIssue]=Field(default_factory=list)
