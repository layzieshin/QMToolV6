"""
Core translation API (MASTERPROMPT)
===================================

The translation feature exposes a simple, function-based API:

    set_global_language(lang)
    set_user_language(user_id, lang)
    get_effective_language(user_id)
    available_languages(feature_id=None)
    load_features(feature_descriptors)
    t(key, *, feature_id, user_id=None)

All functions are thin wrappers around a singleton TranslationEngine instance.
"""

from typing import Iterable, Optional

from translation.services.translation_engine import FeatureDescriptor, TranslationEngine

_engine = TranslationEngine()


def reset_state() -> None:
    """Reset engine state (used in tests)."""
    _engine.reset()


def load_features(feature_descriptors: Iterable[FeatureDescriptor]) -> None:
    _engine.load_features(feature_descriptors)


def set_global_language(lang: str) -> bool:
    return _engine.set_global_language(lang)


def set_user_language(user_id: int, lang: str) -> bool:
    return _engine.set_user_language(user_id, lang)


def get_effective_language(user_id: Optional[int]) -> str:
    return _engine.get_effective_language(user_id)


def available_languages(feature_id: Optional[str] = None) -> list[str]:
    return _engine.available_languages(feature_id)


def t(key: str, *, feature_id: str, user_id: Optional[int] = None) -> str:
    return _engine.t(key, feature_id=feature_id, user_id=user_id)


__all__ = [
    "FeatureDescriptor",
    "load_features",
    "set_global_language",
    "set_user_language",
    "get_effective_language",
    "available_languages",
    "t",
    "reset_state",
]

__version__ = "1.1.0"
