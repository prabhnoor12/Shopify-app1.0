import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import func, desc, select
from ..database import AsyncSessionLocal
from ..models.user import User
from ..models.audit import AuditLog
from ..models.order import Order, OrderItem
from ..models.product import Product

# Service logic for dashboard features


class DashboardService:
    async def get_top_products(self, limit: int = 5, by: str = "sales") -> list[dict]:
        """Return top products by sales or views."""
        async with AsyncSessionLocal() as db:
            if by == "sales":
                # Top products by total sales amount
                result = await db.execute(
                    select(Product.id, Product.title, func.sum(OrderItem.total_price).label("total_sales"), func.count(OrderItem.id).label("orders"))
                    .join(OrderItem, OrderItem.product_id == Product.id)
                    .group_by(Product.id, Product.title)
                    .order_by(desc("total_sales"))
                    .limit(limit)
                )
                rows = result.all()
                return [
                    {"product_id": r.id, "title": r.title, "total_sales": float(r.total_sales or 0), "orders": r.orders}
                    for r in rows
                ]
            elif by == "views":
                # Top products by views (from AuditLog)
                result = await db.execute(
                    select(Product.id, Product.title, func.count().label("views"))
                    .join(AuditLog, AuditLog.target_id == func.cast(Product.id, str))
                    .filter(AuditLog.action == "view_product")
                    .group_by(Product.id, Product.title)
                    .order_by(desc("views"))
                    .limit(limit)
                )
                rows = result.all()
                return [
                    {"product_id": r.id, "title": r.title, "views": r.views}
                    for r in rows
                ]
            else:
                return []

    async def get_recent_orders(self, limit: int = 5) -> list[dict]:
        """Return recent orders with customer, product, and order value."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Order.id, Order.created_at, User.name.label("customer"), OrderItem.product_id, OrderItem.total_price)
                .join(User, User.id == Order.user_id)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .order_by(desc(Order.created_at))
                .limit(limit)
            )
            rows = result.all()
            return [
                {
                    "order_id": r.id,
                    "created_at": r.created_at,
                    "customer": r.customer,
                    "product_id": r.product_id,
                    "total_price": float(r.total_price or 0),
                }
                for r in rows
            ]

    async def get_sales_trend(self, days: int = 30) -> list[dict]:
        """Return sales/revenue per day for the last N days."""
        async with AsyncSessionLocal() as db:
            today = datetime.utcnow().date()
            trend = []
            for i in range(days):
                day = today - timedelta(days=i)
                start_of_day = datetime.combine(day, datetime.min.time())
                end_of_day = datetime.combine(day, datetime.max.time())
                result = await db.execute(
                    select(func.sum(Order.total_price))
                    .filter(Order.created_at >= start_of_day, Order.created_at <= end_of_day)
                )
                total = result.scalar_one() or 0
                trend.append({"date": day.isoformat(), "total_sales": float(total)})
            return trend[::-1]  # chronological order

    async def get_user_dashboard(self, user_id):
        """Fetch dashboard data for a user (summary, activity, recent descriptions)."""
        summary, activity, recent_descriptions = await asyncio.gather(
            self.get_user_summary(user_id),
            self.get_activity_summary(user_id),
            self.get_recent_descriptions(user_id),
        )
        return {
            "summary": summary,
            "activity": activity,
            "recent_descriptions": recent_descriptions,
        }

    async def get_user_summary(self, user_id: int) -> Dict:
        """Return a summary for the dashboard welcome (e.g., name, role, last login)."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).filter(User.id == user_id))
            user = result.scalars().first()
            if not user:
                return {}
            return {
                "name": user.name,
                "role": user.role,
                "last_login": user.last_login,
                "email": user.email,
            }

    async def get_activity_summary(self, user_id: int) -> Dict:
        """Return activity summary for the user (completed, ongoing, deleted, total, conversion rate)."""
        async with AsyncSessionLocal() as db:
            completed_result = await db.execute(
                select(func.count(AuditLog.id)).filter(
                    AuditLog.user_id == user_id, AuditLog.action == "completed"
                )
            )
            completed = completed_result.scalar_one()

            ongoing_result = await db.execute(
                select(func.count(AuditLog.id)).filter(
                    AuditLog.user_id == user_id, AuditLog.action == "ongoing"
                )
            )
            ongoing = ongoing_result.scalar_one()

            deleted_result = await db.execute(
                select(func.count(AuditLog.id)).filter(
                    AuditLog.user_id == user_id, AuditLog.action == "deleted"
                )
            )
            deleted = deleted_result.scalar_one()

            used_result = await db.execute(
                select(func.count(AuditLog.id)).filter(
                    AuditLog.user_id == user_id, AuditLog.action == "used"
                )
            )
            used = used_result.scalar_one()

            total = completed + ongoing + deleted
            conversion_rate = (used / total * 100) if total else 0
            return {
                "completed": completed,
                "ongoing": ongoing,
                "deleted": deleted,
                "total": total,
                "conversion_rate": conversion_rate,
            }

    async def get_recent_descriptions(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Return a list of recent product descriptions created/edited by the user."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AuditLog)
                .filter(
                    AuditLog.user_id == user_id,
                    AuditLog.action == "generate_description",
                )
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            )
            logs = result.scalars().all()
            return [
                {
                    "timestamp": log.created_at,
                    "product_id": log.details,  # You may want to parse details for product_id
                    "action": log.action,
                }
                for log in logs
            ]

    async def get_team_activity(self, team_id: int) -> List[Dict]:
        """Return team activity for the dashboard widget."""
        # This requires a Team/User relationship, which is not shown in your models.
        # Placeholder for future implementation.
        return []

    async def get_monthly_description_counts(
        self, user_id: Optional[int] = None, days: int = 30
    ) -> List[int]:
        """Return daily description counts for the last N days (for chart)."""
        async with AsyncSessionLocal() as db:
            today = datetime.utcnow().date()
            counts = []
            for i in range(days):
                day = today - timedelta(days=i)
                start_of_day = datetime.combine(day, datetime.min.time())
                end_of_day = datetime.combine(day, datetime.max.time())

                query = select(func.count(AuditLog.id)).filter(
                    AuditLog.action == "generate_description",
                    AuditLog.created_at >= start_of_day,
                    AuditLog.created_at <= end_of_day,
                )
                if user_id:
                    query = query.filter(AuditLog.user_id == user_id)

                result = await db.execute(query)
                count = result.scalar_one()
                counts.append(count)
            return counts[::-1]  # Return in chronological order
