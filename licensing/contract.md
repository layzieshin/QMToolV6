# Licensing Feature Contract

```json
{
  "feature_id": "licensing",
  "consumes": [
    {"name": "LicenseBackendInterface", "schema_path": "licensing.LOGIC.interfaces.license_backend_interface.LicenseBackendInterface", "cardinality": "1"},
    {"name": "MachineFingerprintProviderInterface", "schema_path": "licensing.LOGIC.interfaces.machine_fingerprint_provider_interface.MachineFingerprintProviderInterface", "cardinality": "1"},
    {"name": "FileLicenseRepository", "schema_path": "licensing.LOGIC.repositories.file_license_repository.FileLicenseRepository", "cardinality": "1"},
    {"name": "WindowsFingerprintProvider", "schema_path": "licensing.LOGIC.fingerprint.windows_fingerprint_provider.WindowsFingerprintProvider", "cardinality": "1"},
    {"name": "SignatureVerifier", "schema_path": "licensing.LOGIC.crypto.signature_verifier.SignatureVerifier", "cardinality": "1"},
    {"name": "Filesystem", "schema_path": "%PROGRAMDATA%\\QMTool\\license.qmlic (Windows) or /var/lib/qmtool/license.qmlic (Linux)", "cardinality": "1"},
    {"name": "Windows Registry", "schema_path": "HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid", "cardinality": "0..1"},
    {"name": "WMI", "schema_path": "Win32_ComputerSystemProduct.UUID, Win32_BaseBoard.SerialNumber", "cardinality": "0..1"}
  ],
  "produces": [
    {"name": "LicenseVerificationResultDTO", "schema_path": "licensing.MODELS.dto.verification_result_dto.LicenseVerificationResultDTO", "cardinality": "1"},
    {"name": "EntitlementsDTO", "schema_path": "licensing.MODELS.dto.entitlements_dto.EntitlementsDTO", "cardinality": "1"},
    {"name": "GateDecisionDTO", "schema_path": "licensing.MODELS.dto.gate_decision_dto.GateDecisionDTO", "cardinality": "0..*"},
    {"name": "LicenseDTO", "schema_path": "licensing.MODELS.dto.license_dto.LicenseDTO", "cardinality": "0..1"},
    {"name": "MachineFingerprint", "schema_path": "hex:SHA256 hash of canonical fingerprint string", "cardinality": "1"}
  ],
  "side_effects": [
    "fs:read license.qmlic file on initialization",
    "registry:read MachineGuid from Windows registry",
    "wmi:query Win32_ComputerSystemProduct.UUID and Win32_BaseBoard.SerialNumber",
    "memory:cache verification result and entitlements"
  ],
  "failure_modes": [
    {"code": "LICENSE_MISSING", "conditions": "License file not found at configured path", "propagation": "LicenseVerificationResultDTO with status=MISSING"},
    {"code": "LICENSE_INVALID_FORMAT", "conditions": "License file has invalid JSON or missing required fields (schema, license_id, customer, etc.)", "propagation": "LicenseVerificationResultDTO with status=INVALID_FORMAT"},
    {"code": "LICENSE_INVALID_SIGNATURE", "conditions": "Signature verification fails", "propagation": "LicenseVerificationResultDTO with status=INVALID_SIGNATURE"},
    {"code": "LICENSE_EXPIRED", "conditions": "valid_until date is in the past", "propagation": "LicenseVerificationResultDTO with status=EXPIRED"},
    {"code": "LICENSE_FINGERPRINT_MISMATCH", "conditions": "Machine fingerprint not in allowed_fingerprints list", "propagation": "LicenseVerificationResultDTO with status=FINGERPRINT_MISMATCH"},
    {"code": "FEATURE_NOT_ENTITLED", "conditions": "Feature code not in entitlements or entitlements[feature_code] is false", "propagation": "GateDecisionDTO with allowed=False"},
    {"code": "FEATURE_META_INVALID", "conditions": "Feature requires license but feature_code is missing or invalid format", "propagation": "GateDecisionDTO with error_code=FEATURE_META_INVALID"},
    {"code": "FINGERPRINT_UNAVAILABLE", "conditions": "Cannot read machine identifiers from registry/WMI", "propagation": "LicenseErrorCode.FINGERPRINT_UNAVAILABLE"}
  ],
  "auth_rules": [
    {"action": "get_verification", "required_roles": ["*"], "additional_checks": "No auth - returns cached verification status"},
    {"action": "get_entitlements", "required_roles": ["*"], "additional_checks": "No auth - returns cached entitlements (empty if no valid license)"},
    {"action": "is_feature_allowed", "required_roles": ["*"], "additional_checks": "No auth - checks entitlement for specific feature code"},
    {"action": "refresh_license", "required_roles": ["*"], "additional_checks": "No auth - reloads and re-verifies license"},
    {"action": "check_feature (FeatureGatekeeper)", "required_roles": ["*"], "additional_checks": "Core features (is_core=true) bypass license check; non-licensed features allowed; licensed features require entitlement"}
  ],
  "assumptions": [
    "ASSUMPTION: License file follows qmtool-license-v1 schema with fields: schema, license_id, customer, issued_at, valid_until, allowed_fingerprints, entitlements, signature",
    "ASSUMPTION: Machine fingerprint is SHA256 hash of canonical string: MG={guid}|UUID={uuid}|MB={serial}",
    "ASSUMPTION: Fingerprint values prefixed with 'hex:' for hash format",
    "ASSUMPTION: Signature prefixed with 'b64:' for base64-encoded signature",
    "ASSUMPTION: Feature codes must match pattern ^[a-z0-9_]+$ (lowercase, numbers, underscores)",
    "ASSUMPTION: Core features (is_core=true in meta.json) bypass licensing completely",
    "ASSUMPTION: MVP uses hash-based signature verification; production should use RSA/ECDSA via cryptography library",
    "ASSUMPTION: Windows fingerprinting uses MachineGuid (primary), BIOS UUID (secondary), Baseboard Serial (optional)",
    "ASSUMPTION: Entitlements cached after initialization; call refresh_license() to reload"
  ]
}
```
