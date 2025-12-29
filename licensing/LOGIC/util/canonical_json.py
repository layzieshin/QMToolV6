"""
Canonical JSON utility - Creates canonical JSON for signing.

Author: QMToolV6 Development Team
Version: 1.0.0
"""

import json
from typing import Any, Dict


def to_canonical_json(data: Dict[str, Any], exclude_keys: list[str] = None) -> str:
    """
    Convert dictionary to canonical JSON string.
    
    Canonical JSON:
    - Keys sorted alphabetically
    - No whitespace
    - Consistent encoding
    - Excluded keys removed
    
    Args:
        data: Dictionary to convert
        exclude_keys: Keys to exclude (e.g., ["signature"])
        
    Returns:
        Canonical JSON string
        
    Example:
        >>> data = {"b": 2, "a": 1, "signature": "xyz"}
        >>> to_canonical_json(data, exclude_keys=["signature"])
        '{"a":1,"b":2}'
    """
    if exclude_keys:
        data = {k: v for k, v in data.items() if k not in exclude_keys}
    
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
