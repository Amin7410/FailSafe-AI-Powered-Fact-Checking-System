"""
API endpoints for backup and recovery operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.core.backup import BackupManager, BackupScheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backup", tags=["backup"])

# Initialize backup manager
backup_manager = BackupManager()
backup_scheduler = BackupScheduler(backup_manager)

# Request/Response Models
class BackupRequest(BaseModel):
    backup_type: str = "full"  # full, database, configuration
    description: Optional[str] = None

class RestoreRequest(BaseModel):
    backup_path: str
    restore_type: str = "full"  # full, database, configuration
    confirm: bool = False

class BackupResponse(BaseModel):
    success: bool
    backup_path: Optional[str] = None
    message: str
    backup_id: Optional[str] = None

class BackupListResponse(BaseModel):
    success: bool
    backups: List[Dict[str, Any]]
    total_count: int
    total_size_mb: float

class BackupStatusResponse(BaseModel):
    success: bool
    status: Dict[str, Any]

@router.post("/create", response_model=BackupResponse)
async def create_backup(request: BackupRequest, background_tasks: BackgroundTasks):
    """
    Create a new backup
    """
    try:
        if request.backup_type == "full":
            backup_path = backup_manager.create_full_backup()
        elif request.backup_type == "database":
            backup_path = backup_manager.create_database_backup()
        elif request.backup_type == "configuration":
            backup_path = backup_manager.create_configuration_backup()
        else:
            raise HTTPException(status_code=400, detail="Invalid backup type")
        
        # Extract backup ID from path
        backup_id = backup_path.split("/")[-1].replace(".tar.gz", "")
        
        return BackupResponse(
            success=True,
            backup_path=backup_path,
            message=f"{request.backup_type.title()} backup created successfully",
            backup_id=backup_id
        )
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore", response_model=BackupResponse)
async def restore_backup(request: RestoreRequest):
    """
    Restore from a backup
    """
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400, 
                detail="Restore operation requires confirmation. Set 'confirm' to true."
            )
        
        success = backup_manager.restore_backup(
            request.backup_path, 
            request.restore_type
        )
        
        if success:
            return BackupResponse(
                success=True,
                message=f"Backup restored successfully from {request.backup_path}"
            )
        else:
            return BackupResponse(
                success=False,
                message="Failed to restore backup"
            )
        
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=BackupListResponse)
async def list_backups():
    """
    List all available backups
    """
    try:
        backups = backup_manager.list_backups()
        
        total_size = sum(backup["size"] for backup in backups)
        
        return BackupListResponse(
            success=True,
            backups=backups,
            total_count=len(backups),
            total_size_mb=total_size / (1024 * 1024)
        )
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=BackupStatusResponse)
async def get_backup_status():
    """
    Get backup status and statistics
    """
    try:
        status = backup_scheduler.get_backup_status()
        
        return BackupStatusResponse(
            success=True,
            status=status
        )
        
    except Exception as e:
        logger.error(f"Error getting backup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_old_backups():
    """
    Clean up old backups based on retention policy
    """
    try:
        removed_count = backup_manager.cleanup_old_backups()
        
        return {
            "success": True,
            "message": f"Cleaned up {removed_count} old backups",
            "removed_count": removed_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule/{backup_type}")
async def run_scheduled_backup(backup_type: str):
    """
    Run a scheduled backup (for cron jobs)
    """
    try:
        if backup_type not in ["full_backup", "database_backup", "config_backup", "cleanup"]:
            raise HTTPException(status_code=400, detail="Invalid backup type")
        
        backup_scheduler.run_scheduled_backup(backup_type)
        
        return {
            "success": True,
            "message": f"Scheduled backup '{backup_type}' completed"
        }
        
    except Exception as e:
        logger.error(f"Error running scheduled backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def backup_health_check():
    """
    Health check for backup system
    """
    try:
        # Check if backup directory is accessible
        backup_dir = backup_manager.backup_dir
        if not backup_dir.exists():
            return {
                "success": False,
                "status": "unhealthy",
                "message": "Backup directory not accessible"
            }
        
        # Check if we can create a test backup
        test_backup = backup_manager.create_configuration_backup()
        
        return {
            "success": True,
            "status": "healthy",
            "message": "Backup system is operational",
            "test_backup": test_backup
        }
        
    except Exception as e:
        logger.error(f"Backup health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "message": f"Backup system error: {str(e)}"
        }

@router.delete("/{backup_id}")
async def delete_backup(backup_id: str):
    """
    Delete a specific backup
    """
    try:
        import os
        from pathlib import Path
        
        # Find backup file
        backup_files = list(backup_manager.backup_dir.glob(f"*{backup_id}*"))
        
        if not backup_files:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        # Delete backup file
        for backup_file in backup_files:
            backup_file.unlink()
        
        return {
            "success": True,
            "message": f"Backup {backup_id} deleted successfully"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        logger.error(f"Error deleting backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{backup_id}")
async def download_backup(backup_id: str):
    """
    Get download link for a backup (in production, this would return a signed URL)
    """
    try:
        # Find backup file
        backup_files = list(backup_manager.backup_dir.glob(f"*{backup_id}*"))
        
        if not backup_files:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        backup_file = backup_files[0]
        
        # In production, this would generate a signed URL for secure download
        # For now, return the file path (not recommended for production)
        return {
            "success": True,
            "backup_path": str(backup_file),
            "backup_size": backup_file.stat().st_size,
            "message": "Backup file found (in production, this would be a signed URL)"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        logger.error(f"Error getting backup download link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify/{backup_id}")
async def verify_backup(backup_id: str):
    """
    Verify the integrity of a backup
    """
    try:
        # Find backup file
        backup_files = list(backup_manager.backup_dir.glob(f"*{backup_id}*"))
        
        if not backup_files:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        backup_file = backup_files[0]
        
        # Verify backup integrity
        try:
            import tarfile
            with tarfile.open(backup_file, "r:gz") as tar:
                # Try to read the manifest
                manifest_file = tar.extractfile("manifest.json")
                if manifest_file:
                    import json
                    manifest = json.load(manifest_file)
                    
                    return {
                        "success": True,
                        "backup_id": backup_id,
                        "integrity": "valid",
                        "manifest": manifest,
                        "message": "Backup integrity verified"
                    }
                else:
                    return {
                        "success": False,
                        "backup_id": backup_id,
                        "integrity": "invalid",
                        "message": "Backup manifest not found"
                    }
        except Exception as e:
            return {
                "success": False,
                "backup_id": backup_id,
                "integrity": "corrupted",
                "message": f"Backup file is corrupted: {str(e)}"
            }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        logger.error(f"Error verifying backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

