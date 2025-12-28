"""
FeatureNotFoundException - Feature wurde nicht gefunden.

Author: QMToolV6 Development Team
Version: 1.0.0
"""
from __future__ import annotations


class FeatureNotFoundException(Exception):
    """
    Feature wurde nicht gefunden (kein Ordner oder kein `meta.json`).

    Wird geworfen wenn:
    - Ordner mit feature_id existiert nicht
    - meta.json im Ordner fehlt
    - Feature wurde nicht discovered (Cache leer)

    Attributes:
        feature_id:  ID des gesuchten Features

    Example:
        >>> raise FeatureNotFoundException("documentlifecycle")
        FeatureNotFoundException: Feature nicht gefunden: documentlifecycle
    """

    def __init__(self, feature_id: str):
        """
        Initialisiert Exception.

        Args:
            feature_id:  ID des nicht gefundenen Features
        """
        super().__init__(f"Feature nicht gefunden: {feature_id}")
        self.feature_id = feature_id