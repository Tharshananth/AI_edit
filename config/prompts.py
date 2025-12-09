"""
SQLite database manager for project tracking and pipeline stages
Thread-safe with connection pooling
"""

import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager

from config.settings import DATABASE_PATH, DATABASE_BACKUP_ENABLED
from utils.logger import setup_logger

logger = setup_logger("database")


class Database:
    """Thread-safe SQLite database manager"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure one database instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection"""
        if not hasattr(self, 'initialized'):
            self.db_path = DATABASE_PATH
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._local = threading.local()
            self.initialized = True
            self._create_tables()
            logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        else:
            self._local.connection.commit()
    
    def _create_tables(self):
        """Create database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    video_name VARCHAR(255) NOT NULL,
                    video_path TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    current_stage VARCHAR(50),
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_start TIMESTAMP,
                    processing_end TIMESTAMP,
                    duration_seconds FLOAT,
                    file_size_mb FLOAT,
                    resolution VARCHAR(20),
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Pipeline stages tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id VARCHAR(36) NOT NULL,
                    stage_name VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds FLOAT,
                    tokens_used INTEGER DEFAULT 0,
                    cost_usd DECIMAL(10,4) DEFAULT 0.0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_user_id 
                ON projects(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_status 
                ON projects(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stages_project_id 
                ON pipeline_stages(project_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stages_stage_name 
                ON pipeline_stages(stage_name)
            """)
            
            conn.commit()
            logger.info("Database tables created/verified")
    
    # ========================================================================
    # PROJECT OPERATIONS
    # ========================================================================
    
    def create_project(self, project_data: Dict[str, Any]) -> bool:
        """
        Create a new project record
        
        Args:
            project_data: Dictionary with project information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO projects (
                        project_id, user_id, video_name, video_path,
                        status, current_stage, duration_seconds,
                        file_size_mb, resolution
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_data['project_id'],
                    project_data.get('user_id', 'default'),
                    project_data['video_name'],
                    project_data['video_path'],
                    project_data.get('status', 'created'),
                    project_data.get('current_stage', 'initialized'),
                    project_data.get('duration_seconds'),
                    project_data.get('file_size_mb'),
                    project_data.get('resolution')
                ))
                
                logger.info(f"Created project record: {project_data['project_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create project: {e}", exc_info=True)
            return False
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM projects WHERE project_id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get project: {e}", exc_info=True)
            return None
    
    def update_project_status(self, project_id: str, status: str, 
                             current_stage: Optional[str] = None) -> bool:
        """
        Update project status and current stage
        
        Args:
            project_id: Project identifier
            status: New status (processing, complete, error, etc.)
            current_stage: Optional current stage name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if current_stage:
                    cursor.execute("""
                        UPDATE projects 
                        SET status = ?, 
                            current_stage = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE project_id = ?
                    """, (status, current_stage, project_id))
                else:
                    cursor.execute("""
                        UPDATE projects 
                        SET status = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE project_id = ?
                    """, (status, project_id))
                
                # Set processing timestamps
                if status == "processing":
                    cursor.execute("""
                        UPDATE projects 
                        SET processing_start = CURRENT_TIMESTAMP
                        WHERE project_id = ? AND processing_start IS NULL
                    """, (project_id,))
                elif status in ["complete", "error", "failed"]:
                    cursor.execute("""
                        UPDATE projects 
                        SET processing_end = CURRENT_TIMESTAMP
                        WHERE project_id = ?
                    """, (project_id,))
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update project status: {e}", exc_info=True)
            return False
    
    def list_projects(self, user_id: Optional[str] = None, 
                     status: Optional[str] = None,
                     limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List projects with optional filters
        
        Args:
            user_id: Filter by user ID
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of project dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM projects WHERE 1=1"
                params = []
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to list projects: {e}", exc_info=True)
            return []
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete project and all related records
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete stages (cascade should handle this, but being explicit)
                cursor.execute("""
                    DELETE FROM pipeline_stages WHERE project_id = ?
                """, (project_id,))
                
                # Delete project
                cursor.execute("""
                    DELETE FROM projects WHERE project_id = ?
                """, (project_id,))
                
                logger.info(f"Deleted project from database: {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete project: {e}", exc_info=True)
            return False
    
    # ========================================================================
    # PIPELINE STAGE OPERATIONS
    # ========================================================================
    
    def log_stage(self, project_id: str, stage_name: str, status: str,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  tokens_used: int = 0,
                  cost_usd: float = 0.0,
                  error_message: Optional[str] = None) -> bool:
        """
        Log a pipeline stage execution
        
        Args:
            project_id: Project identifier
            stage_name: Name of the stage
            status: Stage status (started, completed, failed)
            start_time: Stage start time
            end_time: Stage end time
            tokens_used: Number of tokens consumed
            cost_usd: Cost in USD
            error_message: Error message if failed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate duration if both times provided
                duration_seconds = None
                if start_time and end_time:
                    duration_seconds = (end_time - start_time).total_seconds()
                
                cursor.execute("""
                    INSERT INTO pipeline_stages (
                        project_id, stage_name, status, start_time, end_time,
                        duration_seconds, tokens_used, cost_usd, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id, stage_name, status,
                    start_time, end_time, duration_seconds,
                    tokens_used, cost_usd, error_message
                ))
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to log stage: {e}", exc_info=True)
            return False
    
    def get_project_stages(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all stages for a project
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of stage dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM pipeline_stages 
                    WHERE project_id = ?
                    ORDER BY created_at ASC
                """, (project_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get project stages: {e}", exc_info=True)
            return []
    
    def get_project_cost_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get cost summary for a project
        
        Args:
            project_id: Project identifier
            
        Returns:
            Cost summary dictionary
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        SUM(tokens_used) as total_tokens,
                        SUM(cost_usd) as total_cost_usd,
                        stage_name,
                        SUM(cost_usd) as stage_cost
                    FROM pipeline_stages
                    WHERE project_id = ?
                    GROUP BY stage_name
                """, (project_id,))
                
                stages = cursor.fetchall()
                
                # Get totals
                cursor.execute("""
                    SELECT 
                        SUM(tokens_used) as total_tokens,
                        SUM(cost_usd) as total_cost_usd
                    FROM pipeline_stages
                    WHERE project_id = ?
                """, (project_id,))
                
                totals = cursor.fetchone()
                
                return {
                    "total_tokens": totals['total_tokens'] or 0,
                    "total_cost_usd": float(totals['total_cost_usd'] or 0.0),
                    "breakdown": {
                        stage['stage_name']: float(stage['stage_cost'] or 0.0)
                        for stage in stages
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get cost summary: {e}", exc_info=True)
            return {
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "breakdown": {}
            }
    
    # ========================================================================
    # UTILITY OPERATIONS
    # ========================================================================
    
    def backup_database(self, backup_path: Optional[Path] = None) -> bool:
        """
        Create a backup of the database
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            True if successful, False otherwise
        """
        if not DATABASE_BACKUP_ENABLED:
            return True
        
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.db_path.parent / f"projects_backup_{timestamp}.db"
            
            with self._get_connection() as conn:
                # Create backup connection
                backup_conn = sqlite3.connect(str(backup_path))
                conn.backup(backup_conn)
                backup_conn.close()
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}", exc_info=True)
            return False
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Delete records older than specified days
        
        Args:
            days: Number of days to retain
            
        Returns:
            Number of records deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete old projects
                cursor.execute("""
                    DELETE FROM projects 
                    WHERE created_at < datetime('now', '-' || ? || ' days')
                """, (days,))
                
                deleted = cursor.rowcount
                logger.info(f"Cleaned up {deleted} old database records")
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}", exc_info=True)
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total projects
                cursor.execute("SELECT COUNT(*) as count FROM projects")
                total_projects = cursor.fetchone()['count']
                
                # Projects by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM projects 
                    GROUP BY status
                """)
                by_status = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Total cost
                cursor.execute("""
                    SELECT SUM(cost_usd) as total_cost
                    FROM pipeline_stages
                """)
                total_cost = cursor.fetchone()['total_cost'] or 0.0
                
                # Database size
                db_size_mb = self.db_path.stat().st_size / (1024 * 1024)
                
                return {
                    "total_projects": total_projects,
                    "projects_by_status": by_status,
                    "total_cost_usd": float(total_cost),
                    "database_size_mb": round(db_size_mb, 2)
                }
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {}
    
    def close(self):
        """Close database connections"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')


# Create global database instance
_db_instance = Database()

def get_db() -> Database:
    """Get global database instance"""
    return _db_instance
