"""
GraphQL API autoconfiguration for NUJ Monitor
Provides unified GraphQL interface over all microservices
"""

import asyncio
from typing import Optional, List
import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI
import httpx

# GraphQL Schema Definitions

@strawberry.type
class Platform:
    id: str
    name: str
    display_name: str
    monitoring_active: bool
    api_enabled: bool
    last_checked: Optional[str]

@strawberry.type
class PolicyChange:
    id: str
    platform_id: str
    detected_at: str
    severity: str
    confidence_score: float
    change_summary: Optional[str]
    impact_assessment: Optional[str]
    requires_notification: bool

@strawberry.type
class GuidanceDraft:
    id: str
    title: str
    summary: Optional[str]
    content: str
    status: str
    drafted_at: str
    ai_generated: bool

@strawberry.type
class Publication:
    id: str
    guidance_id: str
    scheduled_for: str
    published_at: Optional[str]
    recipients_count: int
    successful_deliveries: int
    can_rollback: bool

# Service clients
class ServiceClients:
    def __init__(self):
        self.collector_url = "http://collector:3001"
        self.analyzer_url = "http://analyzer:3002"
        self.publisher_url = "http://publisher:3003"
        self.client = httpx.AsyncClient()

    async def get_platforms(self) -> List[Platform]:
        response = await self.client.get(f"{self.collector_url}/api/platforms")
        data = response.json()
        return [
            Platform(
                id=p["id"],
                name=p["name"],
                display_name=p["display_name"],
                monitoring_active=p["monitoring_active"],
                api_enabled=p.get("api_enabled", False),
                last_checked=p.get("last_checked")
            )
            for p in data.get("platforms", [])
        ]

    async def get_changes(self, limit: int = 50) -> List[PolicyChange]:
        response = await self.client.get(
            f"{self.collector_url}/api/changes",
            params={"limit": limit}
        )
        data = response.json()
        return [
            PolicyChange(
                id=c["id"],
                platform_id=c["policy_document_id"],
                detected_at=c["detected_at"],
                severity=c["severity"],
                confidence_score=float(c["confidence_score"]),
                change_summary=c.get("change_summary"),
                impact_assessment=c.get("impact_assessment"),
                requires_notification=c["requires_member_notification"]
            )
            for c in data.get("changes", [])
        ]

    async def get_guidance_drafts(self, status: Optional[str] = None) -> List[GuidanceDraft]:
        params = {"status": status} if status else {}
        response = await self.client.get(
            f"{self.analyzer_url}/api/guidance/drafts",
            params=params
        )
        data = response.json()
        return [
            GuidanceDraft(
                id=d["id"],
                title=d["title"],
                summary=d.get("summary"),
                content=d["content"],
                status=d["status"],
                drafted_at=d["drafted_at"],
                ai_generated=d.get("generated_by") == "ai"
            )
            for d in data.get("drafts", [])
        ]

services = ServiceClients()

# GraphQL Queries

@strawberry.type
class Query:
    @strawberry.field
    async def platforms(self) -> List[Platform]:
        """Get all monitored platforms"""
        return await services.get_platforms()

    @strawberry.field
    async def platform(self, id: str) -> Optional[Platform]:
        """Get specific platform by ID"""
        platforms = await services.get_platforms()
        return next((p for p in platforms if p.id == id), None)

    @strawberry.field
    async def policy_changes(
        self,
        limit: int = 50,
        severity: Optional[str] = None
    ) -> List[PolicyChange]:
        """Get recent policy changes"""
        changes = await services.get_changes(limit)
        if severity:
            changes = [c for c in changes if c.severity == severity]
        return changes

    @strawberry.field
    async def unreviewed_changes(self) -> List[PolicyChange]:
        """Get changes pending review"""
        changes = await services.get_changes(100)
        return [c for c in changes if c.severity == "unknown"]

    @strawberry.field
    async def guidance_drafts(self, status: Optional[str] = None) -> List[GuidanceDraft]:
        """Get guidance drafts"""
        return await services.get_guidance_drafts(status)

    @strawberry.field
    async def pending_approvals(self) -> List[GuidanceDraft]:
        """Get guidance awaiting approval"""
        return await services.get_guidance_drafts("review")

# GraphQL Mutations

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def trigger_collection(self, platform_id: str) -> bool:
        """Manually trigger platform collection"""
        response = await services.client.post(
            f"{services.collector_url}/api/platforms/{platform_id}/collect"
        )
        return response.status_code == 200

    @strawberry.mutation
    async def analyze_change(self, change_id: str) -> PolicyChange:
        """Trigger analysis of a policy change"""
        response = await services.client.post(
            f"{services.analyzer_url}/api/analysis/analyze",
            json={"change_id": change_id, "force_reanalysis": False}
        )
        data = response.json()
        return PolicyChange(
            id=data["change_id"],
            platform_id="",  # Will be filled by service
            detected_at="",
            severity=data["severity"],
            confidence_score=data["confidence"],
            change_summary=data["summary"],
            impact_assessment=data["impact"],
            requires_notification=data["requires_notification"]
        )

    @strawberry.mutation
    async def generate_guidance(
        self,
        change_ids: List[str],
        platform_name: str
    ) -> GuidanceDraft:
        """Generate member guidance from changes"""
        response = await services.client.post(
            f"{services.analyzer_url}/api/guidance/generate",
            json={
                "change_ids": change_ids,
                "platform_name": platform_name,
                "draft_type": "regular"
            }
        )
        data = response.json()
        return GuidanceDraft(
            id=data["draft_id"],
            title=data["title"],
            summary=data["summary"],
            content=data["content"],
            status=data["status"],
            drafted_at="",
            ai_generated=True
        )

    @strawberry.mutation
    async def schedule_publication(
        self,
        guidance_id: str,
        scheduled_for: str,
        test_mode: bool = False
    ) -> Publication:
        """Schedule guidance publication"""
        response = await services.client.post(
            f"{services.publisher_url}/api/publications/schedule",
            json={
                "guidance_draft_id": guidance_id,
                "scheduled_for": scheduled_for,
                "test_mode": test_mode
            }
        )
        data = response.json()
        return Publication(
            id=data["publication"]["id"],
            guidance_id=guidance_id,
            scheduled_for=data["publication"]["scheduled_for"],
            published_at=None,
            recipients_count=0,
            successful_deliveries=0,
            can_rollback=True
        )

    @strawberry.mutation
    async def rollback_publication(self, publication_id: str, reason: str) -> bool:
        """Rollback a publication within grace period"""
        response = await services.client.post(
            f"{services.publisher_url}/api/publications/{publication_id}/rollback",
            json={"reason": reason}
        )
        return response.status_code == 200

# GraphQL Subscriptions (for real-time updates)

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def platform_changes(self) -> PolicyChange:
        """Subscribe to policy changes in real-time"""
        while True:
            await asyncio.sleep(10)  # Poll every 10 seconds
            changes = await services.get_changes(limit=1)
            if changes:
                yield changes[0]

    @strawberry.subscription
    async def guidance_updates(self) -> GuidanceDraft:
        """Subscribe to guidance draft updates"""
        while True:
            await asyncio.sleep(15)
            drafts = await services.get_guidance_drafts("review")
            if drafts:
                yield drafts[0]

# Create GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)

# FastAPI app with GraphQL
def create_graphql_app() -> FastAPI:
    app = FastAPI(title="NUJ Monitor GraphQL API")

    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    @app.get("/")
    async def root():
        return {
            "message": "NUJ Monitor GraphQL API",
            "graphql": "/graphql",
            "playground": "/graphql (GraphiQL)"
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "graphql-gateway"}

    return app

if __name__ == "__main__":
    import uvicorn
    app = create_graphql_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
