"""Session Manager for bot creation projects."""

import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from bot_generator.models.project import BotProject, ProjectStatus


logger = logging.getLogger(__name__)


class SessionManager:
    """Manage active bot creation sessions."""
    
    def __init__(self):
        self.active_projects: Dict[int, BotProject] = {}
        logger.info("SessionManager initialized")
    
    def has_active_project(self, user_id: int) -> bool:
        """Check if user has an active project."""
        return user_id in self.active_projects
    
    def get_project(self, user_id: int) -> Optional[BotProject]:
        """Get user's active project."""
        return self.active_projects.get(user_id)
    
    def start_project(self, user_id: int) -> BotProject:
        """
        Start a new bot creation project.
        
        Raises:
            ValueError: If user already has an active project
        """
        if self.has_active_project(user_id):
            raise ValueError(
                f"User {user_id} already has an active project. "
                "Must end current project first."
            )
        
        project = BotProject(
            user_id=user_id,
            project_id=str(uuid.uuid4())[:8]
        )
        
        self.active_projects[user_id] = project
        logger.info(f"Started project {project.project_id} for user {user_id}")
        
        return project
    
    def end_project(self, user_id: int) -> bool:
        """
        End user's active project.
        
        Returns:
            True if project was ended, False if no active project
        """
        if not self.has_active_project(user_id):
            return False
        
        project = self.active_projects[user_id]
        project.mark_completed()
        
        # Remove from active projects
        del self.active_projects[user_id]
        
        logger.info(
            f"Ended project {project.project_id} for user {user_id}. "
            f"Duration: {datetime.now() - project.started_at}, "
            f"Iterations: {project.iteration_count}"
        )
        
        return True
    
    def update_project_status(self, user_id: int, status: ProjectStatus):
        """Update project status."""
        if project := self.get_project(user_id):
            project.status = status
            project.last_updated = datetime.now()
            logger.debug(f"Project {project.project_id} status → {status}")
    
    def cleanup_stale_projects(self, timeout_minutes: int = 60):
        """Remove stale projects (inactive for too long)."""
        stale_users = []
        
        for user_id, project in self.active_projects.items():
            if project.is_stale(timeout_minutes):
                stale_users.append(user_id)
        
        for user_id in stale_users:
            logger.warning(f"Cleaning up stale project for user {user_id}")
            self.end_project(user_id)
        
        return len(stale_users)
    
    def get_stats(self) -> Dict:
        """Get session statistics."""
        return {
            "active_projects": len(self.active_projects),
            "projects_by_status": {
                status: sum(1 for p in self.active_projects.values() if p.status == status)
                for status in ProjectStatus
            }
        }


# Global session manager instance
session_manager = SessionManager()
