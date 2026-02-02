"""Progress tracking utility for bot generation."""

import time
from typing import Callable, Optional
from enum import Enum


class GenerationStage(Enum):
    """Stages of bot generation process."""
    PARSING_INTENT = ("🔍 Parsing your requirements", 2)
    DESIGNING_ARCHITECTURE = ("🏗️ Designing bot architecture", 3)
    FINDING_TEMPLATES = ("📚 Finding best code patterns", 2)
    GENERATING_CODE = ("💻 Generating code files", 4)
    VALIDATING_CODE = ("✅ Validating code quality", 2)
    PACKAGING = ("📦 Packaging your bot", 1)
    COMPLETE = ("🎉 Bot generation complete!", 0)
    
    def __init__(self, description: str, estimated_seconds: int):
        self.description = description
        self.estimated_seconds = estimated_seconds


class ProgressTracker:
    """Track progress of bot generation with time estimates."""
    
    def __init__(self, total_stages: int = 6):
        self.total_stages = total_stages
        self.current_stage = 0
        self.start_time = time.time()
        self.stage_times = []
        self.completed_stages = []
    
    def update(self, stage: GenerationStage):
        """Update progress to next stage."""
        self.current_stage += 1
        elapsed = time.time() - self.start_time
        self.stage_times.append(elapsed)
        self.completed_stages.append(stage)
    
    def estimate_remaining(self) -> int:
        """Estimate remaining time in seconds."""
        if not self.stage_times:
            return 15  # default estimate
        
        # Calculate average time per stage
        avg_time = sum(self.stage_times) / len(self.stage_times)
        remaining_stages = self.total_stages - self.current_stage
        return int(avg_time * remaining_stages)
    
    def get_progress_percentage(self) -> int:
        """Get completion percentage."""
        return int((self.current_stage / self.total_stages) * 100)
    
    def get_progress_bar(self, width: int = 6) -> str:
        """Generate visual progress bar."""
        filled = int((self.current_stage / self.total_stages) * width)
        empty = width - filled
        percentage = self.get_progress_percentage()
        return f"[{'█' * filled}{'░' * empty}] {percentage}%"
    
    def get_elapsed_time(self) -> int:
        """Get elapsed time in seconds."""
        return int(time.time() - self.start_time)
    
    def format_time(self, seconds: int) -> str:
        """Format seconds to human readable string."""
        if seconds < 60:
            return f"{seconds}s"
        else:
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}m {secs}s"
    
    def get_status_text(self, current_stage: Optional[GenerationStage] = None) -> str:
        """Get formatted status text for display."""
        lines = []
        
        # Progress bar
        lines.append(f"<b>{self.get_progress_bar()}</b>\n")
        
        # Completed stages
        if self.completed_stages:
            for stage in self.completed_stages:
                lines.append(f"✅ {stage.description}")
        
        # Current stage
        if current_stage and current_stage != GenerationStage.COMPLETE:
            lines.append(f"\n{current_stage.description}...")
        
        # Time info
        if self.current_stage < self.total_stages:
            remaining = self.estimate_remaining()
            lines.append(f"\n⏱️ <b>Estimated time remaining:</b> ~{self.format_time(remaining)}")
        else:
            elapsed = self.get_elapsed_time()
            lines.append(f"\n⏱️ <b>Total time:</b> {self.format_time(elapsed)}")
        
        return "\n".join(lines)


def generate_simple_progress_bar(current: int, total: int) -> str:
    """Simple progress bar generator."""
    filled = int((current / total) * 6)
    empty = 6 - filled
    percentage = int((current / total) * 100)
    return f"[{'█' * filled}{'░' * empty}] {percentage}%"
