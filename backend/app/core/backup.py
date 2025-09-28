"""
Backup and recovery utilities for FailSafe
"""

import os
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import gzip
import tarfile

logger = logging.getLogger(__name__)

class BackupManager:
    """Main backup manager for FailSafe"""
    
    def __init__(self, backup_dir: str = "/var/backups/failsafe"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = 30
    
    def create_full_backup(self) -> str:
        """Create a full system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"failsafe_full_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup database
            self._backup_database(backup_path)
            
            # Backup application files
            self._backup_application_files(backup_path)
            
            # Backup configuration
            self._backup_configuration(backup_path)
            
            # Backup logs
            self._backup_logs(backup_path)
            
            # Create backup manifest
            self._create_backup_manifest(backup_path, "full")
            
            # Compress backup
            compressed_path = self._compress_backup(backup_path)
            
            logger.info(f"Full backup created: {compressed_path}")
            return str(compressed_path)
            
        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            raise
    
    def create_database_backup(self) -> str:
        """Create database-only backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"failsafe_db_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup database
            self._backup_database(backup_path)
            
            # Create backup manifest
            self._create_backup_manifest(backup_path, "database")
            
            # Compress backup
            compressed_path = self._compress_backup(backup_path)
            
            logger.info(f"Database backup created: {compressed_path}")
            return str(compressed_path)
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            raise
    
    def create_configuration_backup(self) -> str:
        """Create configuration-only backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"failsafe_config_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration
            self._backup_configuration(backup_path)
            
            # Create backup manifest
            self._create_backup_manifest(backup_path, "configuration")
            
            # Compress backup
            compressed_path = self._compress_backup(backup_path)
            
            logger.info(f"Configuration backup created: {compressed_path}")
            return str(compressed_path)
            
        except Exception as e:
            logger.error(f"Error creating configuration backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str, restore_type: str = "full") -> bool:
        """Restore from backup"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_path}")
            
            # Extract backup if compressed
            if backup_path.suffix == '.gz':
                extracted_path = self._extract_backup(backup_path)
            else:
                extracted_path = backup_path
            
            # Read backup manifest
            manifest = self._read_backup_manifest(extracted_path)
            
            if manifest["type"] != restore_type:
                raise ValueError(f"Backup type mismatch: expected {restore_type}, got {manifest['type']}")
            
            # Restore based on type
            if restore_type == "full":
                self._restore_database(extracted_path)
                self._restore_application_files(extracted_path)
                self._restore_configuration(extracted_path)
            elif restore_type == "database":
                self._restore_database(extracted_path)
            elif restore_type == "configuration":
                self._restore_configuration(extracted_path)
            
            logger.info(f"Backup restored successfully: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            try:
                manifest = self._read_backup_manifest_from_compressed(backup_file)
                backups.append({
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "type": manifest.get("type", "unknown"),
                    "created_at": manifest.get("created_at", "unknown"),
                    "size": backup_file.stat().st_size
                })
            except Exception as e:
                logger.warning(f"Error reading backup manifest for {backup_file}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def cleanup_old_backups(self) -> int:
        """Remove old backups based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            try:
                manifest = self._read_backup_manifest_from_compressed(backup_file)
                created_at = datetime.fromisoformat(manifest.get("created_at", "1970-01-01T00:00:00"))
                
                if created_at < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file.name}")
                    
            except Exception as e:
                logger.warning(f"Error processing backup {backup_file}: {e}")
        
        logger.info(f"Cleaned up {removed_count} old backups")
        return removed_count
    
    def _backup_database(self, backup_path: Path):
        """Backup database files"""
        db_path = backup_path / "database"
        db_path.mkdir(exist_ok=True)
        
        # SQLite backup
        if os.path.exists("failsafe.db"):
            shutil.copy2("failsafe.db", db_path / "failsafe.db")
        
        # PostgreSQL backup (if using PostgreSQL)
        if os.getenv("DATABASE_URL", "").startswith("postgresql://"):
            self._backup_postgresql(db_path)
    
    def _backup_postgresql(self, backup_path: Path):
        """Backup PostgreSQL database"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return
            
            # Extract connection details from URL
            # This is a simplified version - in production, use proper URL parsing
            backup_file = backup_path / "failsafe_postgresql.sql"
            
            # Use pg_dump to create backup
            subprocess.run([
                "pg_dump", db_url, "-f", str(backup_file)
            ], check=True)
            
        except Exception as e:
            logger.warning(f"PostgreSQL backup failed: {e}")
    
    def _backup_application_files(self, backup_path: Path):
        """Backup application files"""
        app_path = backup_path / "application"
        app_path.mkdir(exist_ok=True)
        
        # Backup source code
        if os.path.exists("app"):
            shutil.copytree("app", app_path / "app")
        
        # Backup configuration files
        if os.path.exists("pyproject.toml"):
            shutil.copy2("pyproject.toml", app_path / "pyproject.toml")
        
        if os.path.exists("requirements.txt"):
            shutil.copy2("requirements.txt", app_path / "requirements.txt")
    
    def _backup_configuration(self, backup_path: Path):
        """Backup configuration files"""
        config_path = backup_path / "configuration"
        config_path.mkdir(exist_ok=True)
        
        # Backup environment files
        if os.path.exists(".env"):
            shutil.copy2(".env", config_path / ".env")
        
        # Backup ethical config
        if os.path.exists("app/core/ethical_config.yaml"):
            shutil.copy2("app/core/ethical_config.yaml", config_path / "ethical_config.yaml")
        
        # Backup systemd service files
        if os.path.exists("/etc/systemd/system/failsafe.service"):
            shutil.copy2("/etc/systemd/system/failsafe.service", config_path / "failsafe.service")
        
        # Backup nginx configuration
        if os.path.exists("/etc/nginx/sites-available/failsafe"):
            shutil.copy2("/etc/nginx/sites-available/failsafe", config_path / "nginx_failsafe")
    
    def _backup_logs(self, backup_path: Path):
        """Backup log files"""
        logs_path = backup_path / "logs"
        logs_path.mkdir(exist_ok=True)
        
        # Backup application logs
        log_dirs = ["/var/log/failsafe", "./logs"]
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                shutil.copytree(log_dir, logs_path / Path(log_dir).name)
    
    def _create_backup_manifest(self, backup_path: Path, backup_type: str):
        """Create backup manifest"""
        manifest = {
            "type": backup_type,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": []
        }
        
        # List components
        for item in backup_path.iterdir():
            if item.is_dir():
                manifest["components"].append({
                    "name": item.name,
                    "type": "directory",
                    "size": sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                })
            else:
                manifest["components"].append({
                    "name": item.name,
                    "type": "file",
                    "size": item.stat().st_size
                })
        
        # Write manifest
        with open(backup_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
    
    def _read_backup_manifest(self, backup_path: Path) -> Dict[str, Any]:
        """Read backup manifest"""
        manifest_file = backup_path / "manifest.json"
        if not manifest_file.exists():
            raise FileNotFoundError("Backup manifest not found")
        
        with open(manifest_file, "r") as f:
            return json.load(f)
    
    def _read_backup_manifest_from_compressed(self, backup_path: Path) -> Dict[str, Any]:
        """Read backup manifest from compressed backup"""
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                manifest_file = tar.extractfile("manifest.json")
                if manifest_file:
                    return json.load(manifest_file)
        except Exception as e:
            logger.warning(f"Error reading manifest from compressed backup: {e}")
        
        # Fallback: return basic info
        return {
            "type": "unknown",
            "created_at": datetime.fromtimestamp(backup_path.stat().st_mtime).isoformat()
        }
    
    def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup directory"""
        compressed_path = backup_path.with_suffix(".tar.gz")
        
        with tarfile.open(compressed_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        # Remove uncompressed directory
        shutil.rmtree(backup_path)
        
        return compressed_path
    
    def _extract_backup(self, backup_path: Path) -> Path:
        """Extract compressed backup"""
        extract_path = backup_path.with_suffix("")
        
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(extract_path.parent)
        
        return extract_path
    
    def _restore_database(self, backup_path: Path):
        """Restore database from backup"""
        db_path = backup_path / "database"
        
        if not db_path.exists():
            logger.warning("No database backup found")
            return
        
        # Restore SQLite database
        if (db_path / "failsafe.db").exists():
            shutil.copy2(db_path / "failsafe.db", "failsafe.db")
            logger.info("SQLite database restored")
        
        # Restore PostgreSQL database
        if (db_path / "failsafe_postgresql.sql").exists():
            self._restore_postgresql(db_path / "failsafe_postgresql.sql")
    
    def _restore_postgresql(self, backup_file: Path):
        """Restore PostgreSQL database"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return
            
            # Use psql to restore backup
            subprocess.run([
                "psql", db_url, "-f", str(backup_file)
            ], check=True)
            
            logger.info("PostgreSQL database restored")
            
        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {e}")
    
    def _restore_application_files(self, backup_path: Path):
        """Restore application files from backup"""
        app_path = backup_path / "application"
        
        if not app_path.exists():
            logger.warning("No application backup found")
            return
        
        # Restore source code
        if (app_path / "app").exists():
            if os.path.exists("app"):
                shutil.rmtree("app")
            shutil.copytree(app_path / "app", "app")
        
        # Restore configuration files
        if (app_path / "pyproject.toml").exists():
            shutil.copy2(app_path / "pyproject.toml", "pyproject.toml")
        
        if (app_path / "requirements.txt").exists():
            shutil.copy2(app_path / "requirements.txt", "requirements.txt")
        
        logger.info("Application files restored")
    
    def _restore_configuration(self, backup_path: Path):
        """Restore configuration from backup"""
        config_path = backup_path / "configuration"
        
        if not config_path.exists():
            logger.warning("No configuration backup found")
            return
        
        # Restore environment files
        if (config_path / ".env").exists():
            shutil.copy2(config_path / ".env", ".env")
        
        # Restore ethical config
        if (config_path / "ethical_config.yaml").exists():
            os.makedirs("app/core", exist_ok=True)
            shutil.copy2(config_path / "ethical_config.yaml", "app/core/ethical_config.yaml")
        
        # Restore systemd service files
        if (config_path / "failsafe.service").exists():
            shutil.copy2(config_path / "failsafe.service", "/etc/systemd/system/failsafe.service")
        
        # Restore nginx configuration
        if (config_path / "nginx_failsafe").exists():
            shutil.copy2(config_path / "nginx_failsafe", "/etc/nginx/sites-available/failsafe")
        
        logger.info("Configuration restored")

class BackupScheduler:
    """Backup scheduling and automation"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.schedule = {
            "full_backup": "0 2 * * *",  # Daily at 2 AM
            "database_backup": "0 */6 * * *",  # Every 6 hours
            "config_backup": "0 1 * * 0",  # Weekly on Sunday at 1 AM
            "cleanup": "0 3 * * *"  # Daily at 3 AM
        }
    
    def run_scheduled_backup(self, backup_type: str):
        """Run scheduled backup"""
        try:
            if backup_type == "full_backup":
                self.backup_manager.create_full_backup()
            elif backup_type == "database_backup":
                self.backup_manager.create_database_backup()
            elif backup_type == "config_backup":
                self.backup_manager.create_configuration_backup()
            elif backup_type == "cleanup":
                self.backup_manager.cleanup_old_backups()
            
            logger.info(f"Scheduled backup completed: {backup_type}")
            
        except Exception as e:
            logger.error(f"Scheduled backup failed: {backup_type}, error: {e}")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get backup status and statistics"""
        backups = self.backup_manager.list_backups()
        
        # Calculate statistics
        total_backups = len(backups)
        total_size = sum(backup["size"] for backup in backups)
        
        # Group by type
        by_type = {}
        for backup in backups:
            backup_type = backup["type"]
            if backup_type not in by_type:
                by_type[backup_type] = 0
            by_type[backup_type] += 1
        
        return {
            "total_backups": total_backups,
            "total_size_mb": total_size / (1024 * 1024),
            "by_type": by_type,
            "latest_backup": backups[0] if backups else None,
            "retention_days": self.backup_manager.retention_days
        }






