"""라우트 모듈"""

from .attendance_routes import attendance_bp
from .assignment_routes import assignment_bp
from .workspace_routes import workspace_bp
from .schedule_routes import schedule_bp
from .thread_routes import thread_bp

__all__ = [
    'attendance_bp',
    'assignment_bp',
    'workspace_bp',
    'schedule_bp',
    'thread_bp',
]
