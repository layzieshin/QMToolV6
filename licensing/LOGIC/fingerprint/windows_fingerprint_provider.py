"""
Windows Fingerprint Provider - Machine fingerprinting for Windows.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import hashlib
import logging
import platform
import subprocess
from typing import Optional

from licensing.MODELS.dto.machine_fingerprint_dto import MachineFingerprintDTO

logger = logging.getLogger(__name__)


class WindowsFingerprintProvider:
    """
    Provides hardware-based machine fingerprinting for Windows.
    
    Uses:
    1. Registry MachineGuid (HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid)
    2. WMI BIOS UUID (Win32_ComputerSystemProduct.UUID)
    3. Baseboard serial (Win32_BaseBoard.SerialNumber) - optional
    
    Fingerprint format: "MG=<guid>|UUID=<uuid>|MB=<serial>"
    Hash: sha256(canonical_string) -> hex:<hash>
    """
    
    def get_fingerprint(self) -> MachineFingerprintDTO:
        """
        Get machine fingerprint with all components.
        
        Returns:
            MachineFingerprintDTO with fingerprint data
            
        Raises:
            RuntimeError: If unable to retrieve fingerprint
        """
        machine_guid = self._get_machine_guid()
        bios_uuid = self._get_bios_uuid()
        baseboard_serial = self._get_baseboard_serial()
        
        # Build canonical string
        canonical = self._build_canonical_string(
            machine_guid, bios_uuid, baseboard_serial
        )
        
        # Calculate hash
        fp_hash = self._calculate_hash(canonical)
        
        return MachineFingerprintDTO(
            machine_guid=machine_guid,
            bios_uuid=bios_uuid,
            baseboard_serial=baseboard_serial,
            canonical_string=canonical,
            hash=fp_hash
        )
    
    def get_fingerprint_hash(self) -> str:
        """
        Get only the fingerprint hash.
        
        Returns:
            Fingerprint hash (hex:<sha256>)
        """
        fp = self.get_fingerprint()
        return fp.hash
    
    def _get_machine_guid(self) -> Optional[str]:
        """Get Windows MachineGuid from registry."""
        if platform.system() != "Windows":
            logger.warning("Not on Windows, using fallback for MachineGuid")
            return "fallback-machine-guid"
        
        try:
            # On Windows, use reg query
            result = subprocess.run(
                [
                    "reg", "query",
                    r"HKLM\SOFTWARE\Microsoft\Cryptography",
                    "/v", "MachineGuid"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse output: "MachineGuid    REG_SZ    {GUID}"
                for line in result.stdout.split('\n'):
                    if 'MachineGuid' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[-1].strip()
            
            logger.warning("Could not retrieve MachineGuid")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving MachineGuid: {e}")
            return None
    
    def _get_bios_uuid(self) -> Optional[str]:
        """Get BIOS UUID via WMI."""
        if platform.system() != "Windows":
            logger.warning("Not on Windows, using fallback for BIOS UUID")
            return "fallback-bios-uuid"
        
        try:
            # On Windows, use WMIC
            result = subprocess.run(
                ["wmic", "csproduct", "get", "UUID"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    uuid = lines[1].strip()
                    if uuid and uuid.lower() != "uuid":
                        return uuid
            
            logger.warning("Could not retrieve BIOS UUID")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving BIOS UUID: {e}")
            return None
    
    def _get_baseboard_serial(self) -> Optional[str]:
        """Get baseboard serial number via WMI."""
        if platform.system() != "Windows":
            return None  # Optional field
        
        try:
            result = subprocess.run(
                ["wmic", "baseboard", "get", "SerialNumber"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    serial = lines[1].strip()
                    # Ignore generic serials
                    if serial and serial.lower() not in ["serialnumber", "to be filled by o.e.m.", "default string"]:
                        return serial
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not retrieve baseboard serial: {e}")
            return None
    
    def _build_canonical_string(
        self,
        machine_guid: Optional[str],
        bios_uuid: Optional[str],
        baseboard_serial: Optional[str]
    ) -> str:
        """
        Build canonical fingerprint string.
        
        Format: "MG=<...>|UUID=<...>|MB=<...>"
        Missing values are represented as "-"
        """
        mg = machine_guid or "-"
        uuid = bios_uuid or "-"
        mb = baseboard_serial or "-"
        
        return f"MG={mg}|UUID={uuid}|MB={mb}"
    
    def _calculate_hash(self, canonical_string: str) -> str:
        """
        Calculate SHA256 hash of canonical string.
        
        Returns:
            Hash with hex: prefix
        """
        hash_bytes = hashlib.sha256(canonical_string.encode('utf-8')).digest()
        hash_hex = hash_bytes.hex()
        return f"hex:{hash_hex}"
