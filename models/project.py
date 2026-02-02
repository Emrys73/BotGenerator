"""Bot Project model for session management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class ProjectStatus(str, Enum):
    """Project lifecycle states."""
    GATHERING_REQUIREMENTS = "gathering_requirements"
    CLARIFYING = "clarifying"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    ITERATING = "iterating"
    COMPLETED = "completed"


@dataclass
class ConversationTurn:
    """A single conversation turn."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class BotProject:
    """Active bot creation project."""
    
    # Identity
    user_id: int
    project_id: str
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Status
    status: ProjectStatus = ProjectStatus.GATHERING_REQUIREMENTS
    
    # Requirements & Design
    requirements: Dict[str, Any] = field(default_factory=dict)
    bot_description: Optional[str] = None
    bot_token: Optional[str] = None
    bot_name: Optional[str] = None
    
    # Conversation
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    
    # Generated Code
    generated_files: Optional[Dict[str, str]] = None
    architecture: Optional[Dict[str, Any]] = None
    
    # Iteration tracking
    iteration_count: int = 0
    pending_changes: Optional[str] = None
    
    def add_message(self, role: str, content: str, tool_calls: Optional[List] = None):
        """Add a message to conversation history."""
        turn = ConversationTurn(
            role=role,
            content=content,
            tool_calls=tool_calls
        )
        self.conversation_history.append(turn)
        self.last_updated = datetime.now()
    
    def get_conversation_context(self, max_turns: int = 20) -> List[Dict[str, str]]:
        """Get recent conversation for LLM context."""
        recent = self.conversation_history[-max_turns:]
        return [
            {"role": turn.role, "content": turn.content}
            for turn in recent
        ]
    
    def is_stale(self, timeout_minutes: int = 60) -> bool:
        """Check if project is stale (inactive)."""
        elapsed = datetime.now() - self.last_updated
        return elapsed.total_seconds() > (timeout_minutes * 60)
    
    def mark_completed(self):
        """Mark project as completed."""
        self.status = ProjectStatus.COMPLETED
        self.last_updated = datetime.now()
