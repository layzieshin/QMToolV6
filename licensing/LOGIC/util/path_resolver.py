"""
Path Resolver - Resolves platform-specific paths.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import os
import platform
from pathlib import Path


def resolve_license_path(path_template: str) -> Path:
    """
    Resolve license file path with environment variable expansion.
    
    Supports Windows environment variables like %PROGRAMDATA%.
    
    Args:
        path_template: Path template with variables
        
    Returns:
        Resolved Path object
        
    Example:
        >>> resolve_license_path("%PROGRAMDATA%\\QMTool\\license.qmlic")
        Path('C:/ProgramData/QMTool/license.qmlic')  # on Windows
    """
    # Expand environment variables
    expanded = os.path.expandvars(path_template)
    
    # Convert to Path
    path = Path(expanded)
    
    # On non-Windows, use alternative location
    if platform.system() != "Windows":
        if "%PROGRAMDATA%" in path_template:
            # Use /var/lib on Linux/Unix
            path = Path("/var/lib/qmtool") / path.name
    
    return path


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists for given path.
    
    Args:
        path: Path to file or directory
    """
    directory = path.parent if path.is_file() or "." in path.name else path
    directory.mkdir(parents=True, exist_ok=True)
