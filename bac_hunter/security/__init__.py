"""
Security modules for BAC Hunter
Provides encrypted storage and sandboxing capabilities
"""

from .encrypted_storage import (
    EncryptedStorage,
    SecureAuthStorage,
    StorageConfig,
    SecureData,
    create_secure_storage,
    create_auth_storage
)

from .sandbox import (
    PayloadSandbox,
    PayloadTester,
    SandboxConfig,
    SandboxResult,
    create_safe_sandbox,
    test_payload_safely,
    check_payload_safety
)

__all__ = [
    "EncryptedStorage",
    "SecureAuthStorage", 
    "StorageConfig",
    "SecureData",
    "create_secure_storage",
    "create_auth_storage",
    "PayloadSandbox",
    "PayloadTester",
    "SandboxConfig",
    "SandboxResult",
    "create_safe_sandbox",
    "test_payload_safely",
    "check_payload_safety"
]