"""
Dashboard module for Trello-Slack AI Bot Analytics
"""
from .app import router as dashboard_router
from .routes.analytics import router as analytics_router
from .routes.projects import router as projects_router

__all__ = ['dashboard_router', 'analytics_router', 'projects_router']