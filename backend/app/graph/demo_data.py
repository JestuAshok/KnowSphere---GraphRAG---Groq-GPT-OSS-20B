from typing import Any, Dict, List

TEAMS = [
    {"name": "Team A", "description": "Core cloud infrastructure engineering team", "department": "R&D"},
    {"name": "Team B", "description": "Product design and management team", "department": "Product"},
    {"name": "Team C", "description": "DevOps and operations team", "department": "Operations"},
    {"name": "Team D", "description": "Marketing technology team", "department": "Marketing"},
]

TECHNOLOGIES = ["Technology X", "Technology Y", "Technology Z", "Tech W", "Tech V"]

PROJECTS = [
    {"name": "Project Phoenix", "department": "R&D", "technologies": ["Technology X", "Technology Y"]},
    {"name": "Project Nova", "department": "Product", "technologies": ["Technology X", "Technology Z"]},
    {"name": "Project Atlas", "department": "R&D", "technologies": ["Technology X", "Technology Y", "Technology Z"]},
    {"name": "Project Orion", "department": "Operations", "technologies": ["Tech V", "Tech W"]},
    {"name": "Project Nexus", "department": "Marketing", "technologies": ["Tech W", "Technology Y"]},
]


def nodes(node_type: str | None = None) -> Dict[str, List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []

    def add_node(name: str, kind: str, properties: Dict[str, Any]) -> str:
        node_id = f"demo-{kind.lower()}-{name.lower().replace(' ', '-')}"
        items.append({"id": node_id, "label": name, "type": kind, "properties": properties})
        return node_id

    departments = sorted({team["department"] for team in TEAMS})
    department_ids = {name: add_node(name, "Department", {"name": name}) for name in departments}
    team_ids = {team["name"]: add_node(team["name"], "Team", team) for team in TEAMS}
    technology_ids = {name: add_node(name, "Technology", {"name": name}) for name in TECHNOLOGIES}
    project_ids = {project["name"]: add_node(project["name"], "Project", project) for project in PROJECTS}

    for team in TEAMS:
        edges.append({"source": team_ids[team["name"]], "target": department_ids[team["department"]], "type": "PART_OF"})
    for project in PROJECTS:
        for technology in project["technologies"]:
            edges.append({"source": project_ids[project["name"]], "target": technology_ids[technology], "type": "DEPENDS_ON"})

    if node_type and node_type != "All":
        items = [item for item in items if item["type"] == node_type]
        visible_ids = {item["id"] for item in items}
        edges = [edge for edge in edges if edge["source"] in visible_ids and edge["target"] in visible_ids]
    return {"nodes": items, "edges": edges}


def projects_by_technology() -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for project in PROJECTS:
        for technology in project["technologies"]:
            counts[technology] = counts.get(technology, 0) + 1
    return [{"technology": name, "project_count": count} for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)]


def department_projects() -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for project in PROJECTS:
        department = project["department"]
        counts[department] = counts.get(department, 0) + 1
    return [{"department": name, "project_count": count} for name, count in counts.items()]


def top_relationships() -> List[Dict[str, Any]]:
    uses = sum(len(team["department"]) > 0 for team in TEAMS)
    depends_on = sum(len(project["technologies"]) for project in PROJECTS)
    return [
        {"relationship_type": "DEPENDS_ON", "count": depends_on},
        {"relationship_type": "USES", "count": uses},
    ]
