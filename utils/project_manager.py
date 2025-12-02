import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import subprocess

from config.settings import PROJECTS_DIR, PROJECT_RETENTION_DAYS
from utils.file_manager import ProjectFileManager
from utils.database import Database
from utils.logger import setup_logger

logger = setup_logger("project_manager")

class ProjectManager:
    """Manages video editing projects"""
    
    def __init__(self):
        self.db = Database()
    
    def create_project(self, video_path: str, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """
        Create a new project from a video file
        
        Args:
            video_path: Path to the input video file
            user_id: User identifier
            
        Returns:
            Project information dictionary or None if failed
        """
        try:
            # Generate project ID
            project_id = str(uuid.uuid4())
            
            # Get video metadata
            video_metadata = self._get_video_metadata(video_path)
            if not video_metadata:
                logger.error("Failed to get video metadata")
                return None
            
            # Create file structure
            file_manager = ProjectFileManager(project_id)
            if not file_manager.create_structure():
                logger.error("Failed to create project structure")
                return None
            
            # Copy video to project input directory
            video_filename = Path(video_path).name
            destination = file_manager.input_dir / video_filename
            shutil.copy2(video_path, destination)
            
            # Create project data
            project_data = {
                "project_id": project_id,
                "user_id": user_id,
                "video_name": video_filename,
                "video_path": str(destination),
                "status": "created",
                "current_stage": "initialized",
                "duration_seconds": video_metadata.get("duration"),
                "file_size_mb": video_metadata.get("file_size_mb"),
                "resolution": video_metadata.get("resolution")
            }
            
            # Save to database
            if not self.db.create_project(project_data):
                logger.error("Failed to create project in database")
                file_manager.delete_project()
                return None
            
            # Save metadata file
            metadata = {
                **project_data,
                "video_metadata": video_metadata,
                "created_at": datetime.now().isoformat()
            }
            file_manager.save_metadata(metadata)
            
            logger.info(f"Created project {project_id} for video {video_filename}")
            return project_data
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}", exc_info=True)
            return None
    
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a project
        
        Args:
            project_id: Project ID
            
        Returns:
            Status dictionary or None if not found
        """
        project = self.db.get_project(project_id)
        if not project:
            return None
        
        # Get stage information
        stages = self.db.get_project_stages(project_id)
        
        # Get cost summary
        cost_summary = self.db.get_project_cost_summary(project_id)
        
        # Get disk usage
        file_manager = ProjectFileManager(project_id)
        disk_usage = file_manager.get_disk_usage()
        
        return {
            "project": project,
            "stages": stages,
            "cost": cost_summary,
            "disk_usage": disk_usage
        }
    
    def list_user_projects(self, user_id: str = "default") -> list:
        """
        List all projects for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of project dictionaries
        """
        return self.db.list_projects(user_id=user_id)
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project completely (files and database)
        
        Args:
            project_id: Project ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from database
            self.db.delete_project(project_id)
            
            # Delete files
            file_manager = ProjectFileManager(project_id)
            file_manager.delete_project()
            
            logger.info(f"Deleted project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete project: {e}", exc_info=True)
            return False
    
    def cleanup_old_projects(self, days: int = PROJECT_RETENTION_DAYS) -> int:
        """
        Delete projects older than specified days
        
        Args:
            days: Number of days to retain projects
            
        Returns:
            Number of projects deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            all_projects = self.db.list_projects()
            
            deleted_count = 0
            for project in all_projects:
                created_at = datetime.fromisoformat(project["created_at"])
                if created_at < cutoff_date:
                    if self.delete_project(project["project_id"]):
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old projects")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old projects: {e}", exc_info=True)
            return 0
    
    def save_checkpoint(self, project_id: str, state: Dict[str, Any]) -> bool:
        """
        Save pipeline state checkpoint
        
        Args:
            project_id: Project ID
            state: LangGraph state dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_manager = ProjectFileManager(project_id)
            return file_manager.save_json(state, "pipeline_state.json", subdir="state")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
            return False
    
    def load_checkpoint(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Load pipeline state checkpoint
        
        Args:
            project_id: Project ID
            
        Returns:
            State dictionary or None if not found
        """
        try:
            file_manager = ProjectFileManager(project_id)
            return file_manager.load_json("pipeline_state.json", subdir="state")
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}", exc_info=True)
            return None
    
    def _get_video_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract video metadata using FFprobe
        
        Args:
            video_path: Path to video file
            
        Returns:
            Metadata dictionary or None if failed
        """
        try:
            # Use ffprobe to get video information
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"FFprobe failed: {result.stderr}")
                return None
            
            import json
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                logger.error("No video stream found")
                return None
            
            # Get file size
            file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
            
            return {
                "duration": float(data['format'].get('duration', 0)),
                "file_size_mb": round(file_size_mb, 2),
                "resolution": f"{video_stream['width']}x{video_stream['height']}",
                "width": video_stream['width'],
                "height": video_stream['height'],
                "fps": eval(video_stream.get('r_frame_rate', '30/1')),
                "codec": video_stream.get('codec_name'),
                "bitrate": int(data['format'].get('bit_rate', 0))
            }
            
        except Exception as e:
            logger.error(f"Failed to get video metadata: {e}", exc_info=True)
            return None