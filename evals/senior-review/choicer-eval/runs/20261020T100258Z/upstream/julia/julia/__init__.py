"""Supersonic Labs Julia typed decision models.

Use ``load_model`` for a resident CPU or CUDA inference engine.
"""

from .inference import load_model

__all__ = ['load_model']
