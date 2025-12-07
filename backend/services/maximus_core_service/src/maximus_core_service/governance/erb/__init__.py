"""
Ethics Review Board (ERB) Package.

Contains ERB member, meeting, and decision models.
"""

from __future__ import annotations

from .models import ERBDecision, ERBMeeting, ERBMember

__all__ = [
    "ERBMember",
    "ERBMeeting",
    "ERBDecision",
]
