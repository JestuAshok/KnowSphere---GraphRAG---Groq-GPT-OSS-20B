"""
KnowSphere seed data script.
Run automatically on first startup if Neo4j graph is empty.
Populates Neo4j with realistic enterprise data and FAISS with embedded document chunks.
"""
import asyncio
import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.graph.neo4j_driver import run_write_query, run_query, is_neo4j_available
from app.graph.embedded_graph import get_embedded_graph
from app.retrieval.embedder import add_documents, load_index

settings = get_settings()

# ─────────────────────────────────────────────
#  SEED DATA DEFINITIONS
# ─────────────────────────────────────────────

DEPARTMENTS = [
    {"name": "R&D", "description": "Research and Development department focused on innovation"},
    {"name": "Product", "description": "Product management and design department"},
    {"name": "Operations", "description": "IT operations and infrastructure department"},
    {"name": "Marketing", "description": "Marketing and customer engagement department"},
]

TEAMS = [
    {"name": "Team A", "description": "Core cloud infrastructure engineering team", "department": "R&D"},
    {"name": "Team B", "description": "Product design and management team", "department": "Product"},
    {"name": "Team C", "description": "DevOps and operations team", "department": "Operations"},
    {"name": "Team D", "description": "Marketing technology team", "department": "Marketing"},
]

EMPLOYEES = [
    {"name": "Alice", "role": "Software Engineer", "email": "alice@knowsphere.ai", "team": "Team A", "department": "R&D"},
    {"name": "Bob", "role": "Tech Lead", "email": "bob@knowsphere.ai", "team": "Team A", "department": "R&D"},
    {"name": "Carol", "role": "Product Manager", "email": "carol@knowsphere.ai", "team": "Team B", "department": "Product"},
    {"name": "Dave", "role": "UX Designer", "email": "dave@knowsphere.ai", "team": "Team B", "department": "Product"},
    {"name": "Eve", "role": "DevOps Engineer", "email": "eve@knowsphere.ai", "team": "Team C", "department": "Operations"},
    {"name": "Frank", "role": "Engineering Manager", "email": "frank@knowsphere.ai", "team": "Team A", "department": "R&D"},
    {"name": "Grace", "role": "Data Scientist", "email": "grace@knowsphere.ai", "team": "Team A", "department": "R&D"},
    {"name": "Henry", "role": "Backend Engineer", "email": "henry@knowsphere.ai", "team": "Team C", "department": "Operations"},
]

TECHNOLOGIES = [
    {"name": "Technology X", "description": "Enterprise cloud infrastructure platform used for scalable compute and storage", "category": "Cloud Infrastructure", "version": "3.2"},
    {"name": "Technology Y", "description": "Machine learning pipeline framework for model training and deployment", "category": "ML/AI", "version": "2.1"},
    {"name": "Technology Z", "description": "Modern frontend framework for building reactive user interfaces", "category": "Frontend", "version": "18.0"},
    {"name": "Tech W", "description": "Distributed database system for high-availability data storage", "category": "Database", "version": "5.0"},
    {"name": "Tech V", "description": "Continuous integration and deployment pipeline automation", "category": "DevOps", "version": "1.4"},
]

PROJECTS = [
    {
        "name": "Project Phoenix",
        "description": "Next-generation customer portal built on cloud infrastructure with ML-powered recommendations",
        "status": "active",
        "department": "R&D",
        "technologies": ["Technology X", "Technology Y"],
        "team": "Team A",
        "members": ["Alice", "Bob", "Grace"],
    },
    {
        "name": "Project Nova",
        "description": "Modern frontend redesign of core product using latest web technologies deployed on cloud",
        "status": "active",
        "department": "Product",
        "technologies": ["Technology X", "Technology Z"],
        "team": "Team B",
        "members": ["Carol", "Dave", "Alice"],
    },
    {
        "name": "Project Atlas",
        "description": "Unified data platform integrating ML capabilities with cloud storage and modern UI",
        "status": "planning",
        "department": "R&D",
        "technologies": ["Technology X", "Technology Y", "Technology Z"],
        "team": "Team A",
        "members": ["Bob", "Frank", "Grace"],
    },
    {
        "name": "Project Orion",
        "description": "Infrastructure automation and CI/CD improvement initiative",
        "status": "active",
        "department": "Operations",
        "technologies": ["Tech V", "Tech W"],
        "team": "Team C",
        "members": ["Eve", "Henry"],
    },
    {
        "name": "Project Nexus",
        "description": "Customer data platform using distributed database for analytics",
        "status": "completed",
        "department": "Marketing",
        "technologies": ["Tech W", "Technology Y"],
        "team": "Team D",
        "members": ["Carol"],
    },
]

CUSTOMERS = [
    {"name": "Acme Corp", "industry": "Manufacturing", "tier": "Enterprise"},
    {"name": "GlobalTech", "industry": "Technology", "tier": "Enterprise"},
    {"name": "Innovate Ltd", "industry": "Consulting", "tier": "Mid-Market"},
    {"name": "Vertex Solutions", "industry": "Finance", "tier": "Enterprise"},
    {"name": "BlueSky Systems", "industry": "Healthcare", "tier": "SMB"},
]

# Key relationship: Customers using products from projects
CUSTOMER_PROJECT_OWNERSHIP = [
    ("Acme Corp", "Project Phoenix"),
    ("GlobalTech", "Project Nova"),
    ("Innovate Ltd", "Project Atlas"),
    ("Vertex Solutions", "Project Phoenix"),
    ("BlueSky Systems", "Project Nexus"),
]

# ─────────────────────────────────────────────
#  SAMPLE DOCUMENTS (synthetic enterprise content)
# ─────────────────────────────────────────────

DOCUMENTS = [
    {
        "name": "Tech_Roadmap.docx",
        "content": """
Technology Roadmap Q3-Q4 2024
=============================

1. Overview
Technology X is a core infrastructure technology used by Team A and Team B. It is critical for Project Phoenix and Project Atlas.
We plan to migrate to an upgraded version in 2027. Discontinuation of Technology X would impact Project Phoenix, Project Nova, and Project Atlas.

2. Technology X — Cloud Infrastructure
Team A uses Technology X extensively for compute and storage workloads.
Project Phoenix depends on Technology X for its backend services.
Project Nova uses Technology X for deployment pipelines.
Project Atlas depends on Technology X, Technology Y, and Technology Z.

3. Technology Y — ML Pipeline
Team A uses Technology Y for machine learning model training.
Project Phoenix depends on Technology Y for recommendation engine.
Project Atlas depends on Technology Y for predictive analytics.
Grace (Data Scientist) is the primary owner of Technology Y integrations.

4. Technology Z — Frontend Framework
Team A and Team B use Technology Z for all user interfaces.
Project Nova depends heavily on Technology Z for the customer portal.
Project Atlas uses Technology Z for the unified dashboard.

5. Risk Assessment
If Technology X is discontinued:
- Project Phoenix (Team A) would be severely impacted — uses Technology X for core compute
- Project Nova (Team B) would require full re-architecture of deployment layer
- Project Atlas (Team A) would face the highest impact as it depends on Technology X, Y, and Z

Recommended action: Begin evaluation of alternative cloud providers by Q1 2025.
""",
    },
    {
        "name": "Project_Dependencies.xlsx",
        "content": """
Project Dependencies Matrix
===========================

Project Name | Technologies | Team | Department | Status
------------ | ------------ | ---- | ---------- | ------
Project Phoenix | Technology X, Technology Y | Team A | R&D | Active
Project Nova | Technology X, Technology Z | Team B | Product | Active
Project Atlas | Technology X, Technology Y, Technology Z | Team A | R&D | Planning
Project Orion | Tech V, Tech W | Team C | Operations | Active
Project Nexus | Tech W, Technology Y | Team D | Marketing | Completed

Technology Ownership:
- Technology X: Team A (Bob - Tech Lead)
- Technology Y: Team A (Grace - Data Scientist)
- Technology Z: Team B (Dave - UX Designer)
- Tech W: Team C (Eve - DevOps Engineer)
- Tech V: Team C (Henry - Backend Engineer)

Critical Dependencies (single point of failure):
- Technology X is used by 3 active projects (Phoenix, Nova, Atlas)
- Project Atlas has the highest dependency count (3 technologies)
""",
    },
    {
        "name": "Team_Technology_Doc.pdf",
        "content": """
Team Technology Usage Report
=============================

Team A — R&D Department
Members: Alice (Software Engineer), Bob (Tech Lead), Frank (Engineering Manager), Grace (Data Scientist)
Technologies Used:
  - Technology X: Core cloud infrastructure for all compute workloads
  - Technology Y: Machine learning pipeline for data science work
  - Technology Z: Frontend framework for internal tooling

Projects: Project Phoenix, Project Atlas
Department: R&D

Team B — Product Department
Members: Carol (Product Manager), Dave (UX Designer)
Technologies Used:
  - Technology Z: Primary frontend framework for all product work
  - Technology X: Cloud deployment and hosting

Projects: Project Nova
Department: Product

Team C — Operations Department
Members: Eve (DevOps Engineer), Henry (Backend Engineer)
Technologies Used:
  - Tech V: CI/CD pipeline automation
  - Tech W: Primary database system

Projects: Project Orion
Department: Operations

Employee Profiles:
- Alice: Software Engineer at Team A, working on Project Phoenix and Project Nova
- Bob: Tech Lead at Team A, working on Project Nova and Project Atlas
- Carol: Product Manager at Team B, works on Project Nova and Project Nexus
- Grace: Data Scientist at Team A, owner of Technology Y integrations
""",
    },
    {
        "name": "Customer_Accounts.md",
        "content": """
Customer Account Overview
=========================

Enterprise Customers:

1. Acme Corp (Manufacturing - Enterprise Tier)
   - Primary product: Project Phoenix
   - Account value: $2.4M ARR
   - Key contact: procurement@acme.com

2. GlobalTech (Technology - Enterprise Tier)
   - Primary product: Project Nova
   - Account value: $1.8M ARR
   - Deployment: Cloud-native on Technology X

3. Innovate Ltd (Consulting - Mid-Market)
   - Primary product: Project Atlas (pilot)
   - Account value: $450K ARR

4. Vertex Solutions (Finance - Enterprise Tier)
   - Primary product: Project Phoenix
   - Account value: $3.1M ARR
   - Critical customer — direct Technology X dependency

5. BlueSky Systems (Healthcare - SMB)
   - Primary product: Project Nexus
   - Account value: $120K ARR

Risk Note: Vertex Solutions and Acme Corp both rely on Project Phoenix which depends on Technology X.
A discontinuation of Technology X would require immediate customer communication and migration planning.
""",
    },
]


# ─────────────────────────────────────────────
#  SEEDING FUNCTIONS
# ─────────────────────────────────────────────

async def is_already_seeded() -> bool:
    """Check if Neo4j or embedded graph already has data."""
    if not await is_neo4j_available():
        return not get_embedded_graph().is_empty()
    try:
        result = await run_query("MATCH (n) RETURN count(n) AS cnt LIMIT 1")
        return result and result[0]["cnt"] > 0
    except Exception:
        return not get_embedded_graph().is_empty()


def seed_embedded_graph():
    """Populate EmbeddedGraphStore with all enterprise demo data."""
    store = get_embedded_graph()
    if not store.is_empty():
        print("[Seed] Embedded graph already has data. Skipping.")
        return

    print("[Seed] Seeding Embedded Graph Store...")
    for dept in DEPARTMENTS:
        store.upsert_entity("Department", dept["name"], {"description": dept["description"]})

    for team in TEAMS:
        store.upsert_entity("Team", team["name"], {"description": team["description"], "department": team["department"]})
        store.upsert_relationship("Team", team["name"], "Department", team["department"], "PART_OF")

    for emp in EMPLOYEES:
        store.upsert_entity("Employee", emp["name"], {"role": emp["role"], "email": emp["email"]})
        store.upsert_relationship("Employee", emp["name"], "Team", emp["team"], "MEMBER_OF")
        store.upsert_relationship("Employee", emp["name"], "Department", emp["department"], "BELONGS_TO")

    for tech in TECHNOLOGIES:
        store.upsert_entity("Technology", tech["name"], tech)

    team_tech = [
        ("Team A", "Technology X"),
        ("Team A", "Technology Y"),
        ("Team A", "Technology Z"),
        ("Team B", "Technology X"),
        ("Team B", "Technology Z"),
        ("Team C", "Tech V"),
        ("Team C", "Tech W"),
        ("Team D", "Tech W"),
        ("Team D", "Technology Y"),
    ]
    for team_name, tech_name in team_tech:
        store.upsert_relationship("Team", team_name, "Technology", tech_name, "USES")

    for proj in PROJECTS:
        store.upsert_entity("Project", proj["name"], {
            "description": proj["description"],
            "status": proj["status"],
            "department": proj["department"],
            "team": proj["team"],
        })
        store.upsert_relationship("Project", proj["name"], "Department", proj["department"], "BELONGS_TO")
        for tech_name in proj["technologies"]:
            store.upsert_relationship("Project", proj["name"], "Technology", tech_name, "DEPENDS_ON")
        store.upsert_relationship("Team", proj["team"], "Project", proj["name"], "WORKS_ON")
        for member_name in proj["members"]:
            store.upsert_relationship("Employee", member_name, "Project", proj["name"], "WORKS_ON")

    for cust in CUSTOMERS:
        store.upsert_entity("Customer", cust["name"], cust)

    for cust_name, proj_name in CUSTOMER_PROJECT_OWNERSHIP:
        store.upsert_relationship("Customer", cust_name, "Project", proj_name, "OWNS")

    for doc in DOCUMENTS:
        store.upsert_entity("Document", doc["name"], {"filename": doc["name"]})

    print("[Seed] Embedded Graph Store seeded successfully!")


async def create_constraints():
    """Create uniqueness constraints for cleaner upserts."""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Employee) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Team) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Project) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Technology) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Department) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Customer) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Document) REQUIRE n.name IS UNIQUE",
    ]
    for cql in constraints:
        try:
            await run_write_query(cql)
        except Exception as e:
            print(f"  Constraint (may already exist): {e}")


async def seed_neo4j():
    print("[Seed] Creating constraints...")
    await create_constraints()

    print("[Seed] Seeding Departments...")
    for dept in DEPARTMENTS:
        await run_write_query(
            "MERGE (d:Department {name: $name}) SET d.description = $description",
            dept
        )

    print("[Seed] Seeding Teams...")
    for team in TEAMS:
        await run_write_query(
            "MERGE (t:Team {name: $name}) SET t.description = $description",
            {"name": team["name"], "description": team["description"]}
        )
        # PART_OF relationship
        await run_write_query("""
            MATCH (t:Team {name: $team}), (d:Department {name: $dept})
            MERGE (t)-[:PART_OF]->(d)
        """, {"team": team["name"], "dept": team["department"]})

    print("[Seed] Seeding Employees...")
    for emp in EMPLOYEES:
        await run_write_query(
            "MERGE (e:Employee {name: $name}) SET e.role = $role, e.email = $email",
            {"name": emp["name"], "role": emp["role"], "email": emp["email"]}
        )
        await run_write_query("""
            MATCH (e:Employee {name: $emp}), (t:Team {name: $team})
            MERGE (e)-[:MEMBER_OF]->(t)
        """, {"emp": emp["name"], "team": emp["team"]})
        await run_write_query("""
            MATCH (e:Employee {name: $emp}), (d:Department {name: $dept})
            MERGE (e)-[:BELONGS_TO]->(d)
        """, {"emp": emp["name"], "dept": emp["department"]})

    print("[Seed] Seeding Technologies...")
    for tech in TECHNOLOGIES:
        await run_write_query(
            "MERGE (t:Technology {name: $name}) SET t.description = $description, t.category = $category, t.version = $version",
            tech
        )

    # Team → USES → Technology (CRITICAL for demo scenario)
    print("[Seed] Seeding Team→Technology relationships...")
    team_tech = [
        ("Team A", "Technology X"),
        ("Team A", "Technology Y"),
        ("Team A", "Technology Z"),
        ("Team B", "Technology X"),
        ("Team B", "Technology Z"),
        ("Team C", "Tech V"),
        ("Team C", "Tech W"),
        ("Team D", "Tech W"),
        ("Team D", "Technology Y"),
    ]
    for team_name, tech_name in team_tech:
        await run_write_query("""
            MATCH (t:Team {name: $team}), (tech:Technology {name: $tech})
            MERGE (t)-[:USES]->(tech)
        """, {"team": team_name, "tech": tech_name})

    print("[Seed] Seeding Projects...")
    for proj in PROJECTS:
        await run_write_query(
            "MERGE (p:Project {name: $name}) SET p.description = $description, p.status = $status",
            {"name": proj["name"], "description": proj["description"], "status": proj["status"]}
        )
        # BELONGS_TO department
        await run_write_query("""
            MATCH (p:Project {name: $proj}), (d:Department {name: $dept})
            MERGE (p)-[:BELONGS_TO]->(d)
        """, {"proj": proj["name"], "dept": proj["department"]})

        # DEPENDS_ON technologies (CRITICAL for demo scenario)
        for tech_name in proj["technologies"]:
            await run_write_query("""
                MATCH (p:Project {name: $proj}), (t:Technology {name: $tech})
                MERGE (p)-[:DEPENDS_ON]->(t)
            """, {"proj": proj["name"], "tech": tech_name})

        # Team WORKS_ON project
        await run_write_query("""
            MATCH (t:Team {name: $team}), (p:Project {name: $proj})
            MERGE (t)-[:WORKS_ON]->(p)
        """, {"team": proj["team"], "proj": proj["name"]})

        # Members WORKS_ON project
        for member_name in proj["members"]:
            await run_write_query("""
                MATCH (e:Employee {name: $emp}), (p:Project {name: $proj})
                MERGE (e)-[:WORKS_ON]->(p)
            """, {"emp": member_name, "proj": proj["name"]})

    print("[Seed] Seeding Customers...")
    for cust in CUSTOMERS:
        await run_write_query(
            "MERGE (c:Customer {name: $name}) SET c.industry = $industry, c.tier = $tier",
            cust
        )

    for cust_name, proj_name in CUSTOMER_PROJECT_OWNERSHIP:
        await run_write_query("""
            MATCH (c:Customer {name: $cust}), (p:Project {name: $proj})
            MERGE (c)-[:OWNS]->(p)
        """, {"cust": cust_name, "proj": proj_name})

    print("[Seed] Seeding Documents (Neo4j nodes)...")
    for doc in DOCUMENTS:
        await run_write_query(
            "MERGE (d:Document {name: $name}) SET d.filename = $name, d.ingested_at = datetime()",
            {"name": doc["name"]}
        )


async def seed_faiss():
    """Embed all document content into FAISS."""
    print("[Seed] Building FAISS index from documents...")
    load_index()
    all_chunks = []
    for doc in DOCUMENTS:
        words = doc["content"].split()
        chunk_size, overlap = 100, 20
        i = 0
        chunk_idx = 0
        while i < len(words):
            chunk_words = words[i: i + chunk_size]
            all_chunks.append({
                "text": " ".join(chunk_words),
                "doc_id": doc["name"],
                "doc_name": doc["name"],
                "chunk_idx": chunk_idx,
            })
            i += chunk_size - overlap
            chunk_idx += 1
    add_documents(all_chunks)
    print(f"[Seed] Added {len(all_chunks)} chunks to FAISS.")


async def seed_sqlite():
    """Seed SQLite: demo user, data sources, activity log, document records."""
    import uuid
    from datetime import datetime, timedelta
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select, insert
    from app.core.database import Base
    from app.models.user import UserORM
    from app.models.document import DocumentORM
    from app.models.activity import ActivityLogORM
    from app.models.datasource import DataSourceORM
    from app.core.auth import hash_password

    engine = create_async_engine(settings.sqlite_url, echo=False, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        # Demo user
        existing = await session.execute(select(UserORM).where(UserORM.email == "demo@knowsphere.ai"))
        if not existing.scalar_one_or_none():
            user = UserORM(
                id=str(uuid.uuid4()),
                email="demo@knowsphere.ai",
                name="Jestu",
                password_hash=hash_password("demo1234"),
            )
            session.add(user)

        # Admin user
        existing_admin = await session.execute(select(UserORM).where(UserORM.email == "admin@knowsphere.ai"))
        if not existing_admin.scalar_one_or_none():
            admin_user = UserORM(
                id=str(uuid.uuid4()),
                email="admin@knowsphere.ai",
                name="Admin",
                password_hash=hash_password("admin123"),
            )
            session.add(admin_user)

        # Documents
        for doc in DOCUMENTS:
            existing_doc = await session.execute(
                select(DocumentORM).where(DocumentORM.original_name == doc["name"])
            )
            if not existing_doc.scalar_one_or_none():
                d = DocumentORM(
                    id=str(uuid.uuid4()),
                    filename=doc["name"].replace(" ", "_"),
                    original_name=doc["name"],
                    file_size=len(doc["content"].encode()),
                    mime_type="text/plain",
                    content=doc["content"],
                    entities_json="[]",
                    status="done",
                    processed_at=datetime.utcnow(),
                )
                session.add(d)

        # Activity log
        activities = [
            ("document_ingested", "Tech_Roadmap.docx ingested successfully", "Document", "Tech_Roadmap.docx", 3),
            ("entity_detected", "New Technology 'Technology X' detected", "Technology", "Technology X", 6),
            ("relationship_updated", "Team A → USES → Technology X relationship updated", "Team", "Team A", 12),
            ("entity_detected", "New Project 'Project Phoenix' detected", "Project", "Project Phoenix", 24),
            ("document_ingested", "Project_Dependencies.xlsx ingested successfully", "Document", "Project_Dependencies.xlsx", 36),
            ("entity_detected", "New Customer 'Acme Corp' detected", "Customer", "Acme Corp", 48),
        ]
        for event_type, description, entity_type, entity_name, hours_ago in activities:
            log = ActivityLogORM(
                id=str(uuid.uuid4()),
                event_type=event_type,
                description=description,
                entity_type=entity_type,
                entity_name=entity_name,
            )
            session.add(log)

        # Data sources
        sources = [
            ("SharePoint", "sharepoint", "connected"),
            ("Confluence", "confluence", "connected"),
            ("Google Drive", "google_drive", "connected"),
            ("PostgreSQL", "postgres", "connected"),
            ("Neo4j", "neo4j", "connected"),
            ("Custom API", "custom_api", "not_connected"),
        ]
        for name, stype, status in sources:
            existing_ds = await session.execute(
                select(DataSourceORM).where(DataSourceORM.source_type == stype)
            )
            if not existing_ds.scalar_one_or_none():
                ds = DataSourceORM(
                    id=str(uuid.uuid4()),
                    name=name,
                    source_type=stype,
                    status=status,
                    last_sync=datetime.utcnow() - timedelta(days=1) if status == "connected" else None,
                )
                session.add(ds)

        await session.commit()
    print("[Seed] SQLite seeded (user, documents, activity, data sources).")


async def main():
    print("=" * 50)
    print("KnowSphere — Seed Data Script")
    print("=" * 50)

    # Check if Neo4j is available
    try:
        if await is_neo4j_available():
            if await is_already_seeded():
                print("[Seed] Neo4j already has data. Skipping Neo4j seed.")
            else:
                print("[Seed] Starting Neo4j seed...")
                await seed_neo4j()
                print("[Seed] Neo4j seeded successfully!")
        else:
            print("[Seed] Neo4j not detected, seeding Embedded Graph Store...")
            seed_embedded_graph()
    except Exception as e:
        print(f"[Seed] Graph seed error: {e}")
        seed_embedded_graph()

    # Always ensure embedded graph is seeded
    seed_embedded_graph()

    try:
        await seed_faiss()
    except Exception as e:
        print(f"[Seed] FAISS error: {e}")

    try:
        await seed_sqlite()
    except Exception as e:
        print(f"[Seed] SQLite error: {e}")

    print("[Seed] Done!")


if __name__ == "__main__":
    asyncio.run(main())
