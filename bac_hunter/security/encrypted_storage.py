"""
Encrypted Storage System for BAC Hunter
Provides secure storage for sensitive data like authentication tokens, cookies, and credentials
"""

from __future__ import annotations
import os
import json
import base64
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import secrets

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None
    hashes = None
    PBKDF2HMAC = None

logger = logging.getLogger(__name__)

@dataclass
class SecureData:
    """Represents securely stored data"""
    data_id: str
    data_type: str  # 'auth_token', 'cookie', 'credential', 'api_key', etc.
    encrypted_data: str
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class StorageConfig:
    """Configuration for encrypted storage"""
    storage_path: Path
    key_derivation_iterations: int = 100000
    require_password: bool = True
    auto_lock_timeout: int = 3600  # seconds
    max_failed_attempts: int = 3
    backup_enabled: bool = True


class EncryptedStorage:
    """Secure encrypted storage for sensitive data"""
    
    def __init__(self, config: StorageConfig):
        if not CRYPTO_AVAILABLE:
            raise ImportError("Cryptography library not available. Install with: pip install cryptography")
        
        self.config = config
        self.storage_path = config.storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.key_file = self.storage_path / ".key"
        self.data_file = self.storage_path / "secure_data.enc"
        self.metadata_file = self.storage_path / "metadata.json"
        
        self._cipher: Optional[Fernet] = None
        self._unlocked = False
        self._unlock_time: Optional[datetime] = None
        self._failed_attempts = 0
        
        self._load_or_create_key()
    
    def _load_or_create_key(self) -> None:
        """Load existing key or create new one"""
        if self.key_file.exists():
            logger.info("Found existing encryption key")
        else:
            logger.info("Creating new encryption key")
            self._create_new_key()
    
    def _create_new_key(self) -> None:
        """Create a new encryption key"""
        # Generate a random salt
        salt = secrets.token_bytes(32)
        
        # Store salt in key file (not the actual key)
        key_data = {
            "salt": base64.b64encode(salt).decode(),
            "iterations": self.config.key_derivation_iterations,
            "created_at": datetime.now().isoformat()
        }
        
        with open(self.key_file, 'w') as f:
            json.dump(key_data, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(self.key_file, 0o600)
        
        logger.info("New encryption key created")
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        with open(self.key_file, 'r') as f:
            key_data = json.load(f)
        
        salt = base64.b64decode(key_data["salt"])
        iterations = key_data["iterations"]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def unlock(self, password: str) -> bool:
        """Unlock the storage with password"""
        if self._failed_attempts >= self.config.max_failed_attempts:
            logger.error("Maximum failed unlock attempts reached")
            return False
        
        try:
            key = self._derive_key(password)
            self._cipher = Fernet(key)
            
            # Test the key by trying to decrypt metadata if it exists
            if self.data_file.exists():
                with open(self.data_file, 'rb') as f:
                    encrypted_data = f.read()
                
                if encrypted_data:
                    # Try to decrypt a small test
                    self._cipher.decrypt(encrypted_data[:100])  # Just test first part
            
            self._unlocked = True
            self._unlock_time = datetime.now()
            self._failed_attempts = 0
            
            logger.info("Storage unlocked successfully")
            return True
            
        except Exception as e:
            self._failed_attempts += 1
            logger.warning(f"Failed to unlock storage: {e}")
            return False
    
    def lock(self) -> None:
        """Lock the storage"""
        self._cipher = None
        self._unlocked = False
        self._unlock_time = None
        logger.info("Storage locked")
    
    def is_unlocked(self) -> bool:
        """Check if storage is unlocked"""
        if not self._unlocked:
            return False
        
        # Check for auto-lock timeout
        if self._unlock_time and self.config.auto_lock_timeout > 0:
            if (datetime.now() - self._unlock_time).total_seconds() > self.config.auto_lock_timeout:
                self.lock()
                return False
        
        return True
    
    def store_data(self, data_id: str, data_type: str, data: Any, 
                   metadata: Dict[str, Any] = None, expires_at: datetime = None) -> bool:
        """Store data securely"""
        if not self.is_unlocked():
            logger.error("Storage is locked")
            return False
        
        try:
            # Serialize data
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
            else:
                data_str = str(data)
            
            # Encrypt data
            encrypted_data = self._cipher.encrypt(data_str.encode())
            
            # Create secure data object
            secure_data = SecureData(
                data_id=data_id,
                data_type=data_type,
                encrypted_data=base64.b64encode(encrypted_data).decode(),
                metadata=metadata or {},
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            # Load existing data
            stored_data = self._load_stored_data()
            
            # Add or update data
            stored_data[data_id] = secure_data
            
            # Save to file
            self._save_stored_data(stored_data)
            
            logger.info(f"Stored data: {data_id} ({data_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            return False
    
    def retrieve_data(self, data_id: str) -> Optional[Any]:
        """Retrieve and decrypt data"""
        if not self.is_unlocked():
            logger.error("Storage is locked")
            return None
        
        try:
            stored_data = self._load_stored_data()
            
            if data_id not in stored_data:
                logger.warning(f"Data not found: {data_id}")
                return None
            
            secure_data = stored_data[data_id]
            
            # Check if data has expired
            if secure_data.expires_at and datetime.now() > secure_data.expires_at:
                logger.warning(f"Data expired: {data_id}")
                self.delete_data(data_id)
                return None
            
            # Decrypt data
            encrypted_data = base64.b64decode(secure_data.encrypted_data)
            decrypted_data = self._cipher.decrypt(encrypted_data).decode()
            
            # Update access tracking
            secure_data.access_count += 1
            secure_data.last_accessed = datetime.now()
            stored_data[data_id] = secure_data
            self._save_stored_data(stored_data)
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return None
    
    def delete_data(self, data_id: str) -> bool:
        """Delete stored data"""
        if not self.is_unlocked():
            logger.error("Storage is locked")
            return False
        
        try:
            stored_data = self._load_stored_data()
            
            if data_id in stored_data:
                del stored_data[data_id]
                self._save_stored_data(stored_data)
                logger.info(f"Deleted data: {data_id}")
                return True
            else:
                logger.warning(f"Data not found for deletion: {data_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete data: {e}")
            return False
    
    def list_data(self, data_type: str = None) -> List[Dict[str, Any]]:
        """List stored data (metadata only)"""
        if not self.is_unlocked():
            logger.error("Storage is locked")
            return []
        
        try:
            stored_data = self._load_stored_data()
            
            result = []
            for data_id, secure_data in stored_data.items():
                if data_type is None or secure_data.data_type == data_type:
                    # Return metadata without encrypted data
                    item_info = {
                        "data_id": secure_data.data_id,
                        "data_type": secure_data.data_type,
                        "metadata": secure_data.metadata,
                        "created_at": secure_data.created_at.isoformat(),
                        "expires_at": secure_data.expires_at.isoformat() if secure_data.expires_at else None,
                        "access_count": secure_data.access_count,
                        "last_accessed": secure_data.last_accessed.isoformat() if secure_data.last_accessed else None
                    }
                    result.append(item_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list data: {e}")
            return []
    
    def cleanup_expired(self) -> int:
        """Remove expired data entries"""
        if not self.is_unlocked():
            logger.error("Storage is locked")
            return 0
        
        try:
            stored_data = self._load_stored_data()
            expired_ids = []
            
            for data_id, secure_data in stored_data.items():
                if secure_data.expires_at and datetime.now() > secure_data.expires_at:
                    expired_ids.append(data_id)
            
            for data_id in expired_ids:
                del stored_data[data_id]
            
            if expired_ids:
                self._save_stored_data(stored_data)
                logger.info(f"Cleaned up {len(expired_ids)} expired entries")
            
            return len(expired_ids)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return 0
    
    def _load_stored_data(self) -> Dict[str, SecureData]:
        """Load stored data from file"""
        if not self.data_file.exists():
            return {}
        
        try:
            with open(self.data_file, 'rb') as f:
                encrypted_content = f.read()
            
            if not encrypted_content:
                return {}
            
            # Decrypt the entire file content
            decrypted_content = self._cipher.decrypt(encrypted_content)
            data_dict = json.loads(decrypted_content.decode())
            
            # Convert back to SecureData objects
            result = {}
            for data_id, item_data in data_dict.items():
                # Convert datetime strings back to datetime objects
                item_data["created_at"] = datetime.fromisoformat(item_data["created_at"])
                if item_data.get("expires_at"):
                    item_data["expires_at"] = datetime.fromisoformat(item_data["expires_at"])
                if item_data.get("last_accessed"):
                    item_data["last_accessed"] = datetime.fromisoformat(item_data["last_accessed"])
                
                result[data_id] = SecureData(**item_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to load stored data: {e}")
            return {}
    
    def _save_stored_data(self, data: Dict[str, SecureData]) -> None:
        """Save stored data to file"""
        try:
            # Convert to JSON-serializable format
            data_dict = {}
            for data_id, secure_data in data.items():
                item_dict = asdict(secure_data)
                # Convert datetime objects to ISO strings
                item_dict["created_at"] = secure_data.created_at.isoformat()
                if secure_data.expires_at:
                    item_dict["expires_at"] = secure_data.expires_at.isoformat()
                if secure_data.last_accessed:
                    item_dict["last_accessed"] = secure_data.last_accessed.isoformat()
                
                data_dict[data_id] = item_dict
            
            # Encrypt entire content
            content = json.dumps(data_dict, indent=2)
            encrypted_content = self._cipher.encrypt(content.encode())
            
            # Write to file
            with open(self.data_file, 'wb') as f:
                f.write(encrypted_content)
            
            # Set restrictive permissions
            os.chmod(self.data_file, 0o600)
            
            # Create backup if enabled
            if self.config.backup_enabled:
                self._create_backup()
                
        except Exception as e:
            logger.error(f"Failed to save stored data: {e}")
            raise
    
    def _create_backup(self) -> None:
        """Create backup of encrypted data"""
        try:
            backup_dir = self.storage_path / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"secure_data_{timestamp}.enc"
            
            if self.data_file.exists():
                import shutil
                shutil.copy2(self.data_file, backup_file)
                
                # Keep only last 5 backups
                backups = sorted(backup_dir.glob("secure_data_*.enc"))
                if len(backups) > 5:
                    for old_backup in backups[:-5]:
                        old_backup.unlink()
                
                logger.debug(f"Created backup: {backup_file}")
                
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def export_data(self, output_file: Path, include_encrypted: bool = False) -> bool:
        """Export data for backup or migration"""
        if not self.is_unlocked():
            logger.error("Storage is locked")
            return False
        
        try:
            stored_data = self._load_stored_data()
            
            export_data = {}
            for data_id, secure_data in stored_data.items():
                item_data = {
                    "data_id": secure_data.data_id,
                    "data_type": secure_data.data_type,
                    "metadata": secure_data.metadata,
                    "created_at": secure_data.created_at.isoformat(),
                    "expires_at": secure_data.expires_at.isoformat() if secure_data.expires_at else None,
                    "access_count": secure_data.access_count,
                    "last_accessed": secure_data.last_accessed.isoformat() if secure_data.last_accessed else None
                }
                
                if include_encrypted:
                    # Include encrypted data for complete backup
                    item_data["encrypted_data"] = secure_data.encrypted_data
                
                export_data[data_id] = item_data
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported data to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if not self.is_unlocked():
            return {"error": "Storage is locked"}
        
        try:
            stored_data = self._load_stored_data()
            
            stats = {
                "total_entries": len(stored_data),
                "data_types": {},
                "expired_entries": 0,
                "total_accesses": 0,
                "storage_size_bytes": self.data_file.stat().st_size if self.data_file.exists() else 0
            }
            
            now = datetime.now()
            for secure_data in stored_data.values():
                # Count by data type
                data_type = secure_data.data_type
                if data_type not in stats["data_types"]:
                    stats["data_types"][data_type] = 0
                stats["data_types"][data_type] += 1
                
                # Count expired entries
                if secure_data.expires_at and now > secure_data.expires_at:
                    stats["expired_entries"] += 1
                
                # Sum total accesses
                stats["total_accesses"] += secure_data.access_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}


class SecureAuthStorage:
    """Specialized secure storage for authentication data"""
    
    def __init__(self, storage_path: Path, password: str):
        config = StorageConfig(
            storage_path=storage_path,
            require_password=True,
            auto_lock_timeout=1800,  # 30 minutes
            backup_enabled=True
        )
        
        self.storage = EncryptedStorage(config)
        if not self.storage.unlock(password):
            raise ValueError("Failed to unlock secure storage")
    
    def store_auth_token(self, token_id: str, token: str, expires_in: int = None) -> bool:
        """Store authentication token"""
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        metadata = {
            "token_type": "bearer",
            "created_by": "bac_hunter"
        }
        
        return self.storage.store_data(token_id, "auth_token", token, metadata, expires_at)
    
    def store_session_cookies(self, session_id: str, cookies: Dict[str, str], 
                            domain: str, expires_in: int = None) -> bool:
        """Store session cookies"""
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        metadata = {
            "domain": domain,
            "cookie_count": len(cookies)
        }
        
        return self.storage.store_data(session_id, "session_cookies", cookies, metadata, expires_at)
    
    def store_credentials(self, cred_id: str, username: str, password: str, 
                         domain: str = None) -> bool:
        """Store user credentials"""
        cred_data = {
            "username": username,
            "password": password
        }
        
        metadata = {
            "domain": domain,
            "credential_type": "user_password"
        }
        
        return self.storage.store_data(cred_id, "credentials", cred_data, metadata)
    
    def get_auth_token(self, token_id: str) -> Optional[str]:
        """Retrieve authentication token"""
        return self.storage.retrieve_data(token_id)
    
    def get_session_cookies(self, session_id: str) -> Optional[Dict[str, str]]:
        """Retrieve session cookies"""
        return self.storage.retrieve_data(session_id)
    
    def get_credentials(self, cred_id: str) -> Optional[Dict[str, str]]:
        """Retrieve credentials"""
        return self.storage.retrieve_data(cred_id)
    
    def cleanup_expired_auth_data(self) -> int:
        """Clean up expired authentication data"""
        return self.storage.cleanup_expired()


# Convenience functions
def create_secure_storage(storage_path: str, password: str) -> EncryptedStorage:
    """Create encrypted storage with default configuration"""
    config = StorageConfig(
        storage_path=Path(storage_path),
        require_password=True,
        auto_lock_timeout=3600,
        backup_enabled=True
    )
    
    storage = EncryptedStorage(config)
    if not storage.unlock(password):
        raise ValueError("Failed to unlock storage")
    
    return storage


def create_auth_storage(storage_path: str, password: str) -> SecureAuthStorage:
    """Create secure authentication storage"""
    return SecureAuthStorage(Path(storage_path), password)