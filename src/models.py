"""Define the models for backbone service."""

from pydantic import BaseModel
from typing import List

class InnerDependency:
    """Transitive dependencies information."""
    package: str
    version: str

class Dependency:
    """Dependency information."""
    package: str
    version: str
    deps: List[InnerDependency] = []

class Detail:
    """Result details."""
    ecosystem: str
    manifest_file_path: str
    manifest_file: str
    _resolved: List[Dependency]


class Result:
    """Result section."""
    details: List[Detail]

class ServiceInput(BaseModel):
    """Input for stack aggregation and recommendation."""
    result: List[Result]
    external_request_id: str
    current_stack_license: dict = {}
    is_modified: bool

