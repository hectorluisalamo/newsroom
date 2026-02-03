# ABOUTME: Angle templates for pitch differentiation.
# ABOUTME: Defines named framing strategies to generate distinct pitches.
"""Angle templates for pitch generation.

Each angle defines a named framing strategy with a short description.
The ANGLES dict maps angle names to their metadata. Full template fields
(title pattern, thesis framing, key_points extraction) belong here
alongside the description.
"""

ANGLES = {
    "trend_analysis": {
        "description": "Trajectory and why it matters.",
    },
    "skeptics_take": {
        "description": "What is overlooked or overhyped.",
    },
    "human_impact": {
        "description": "Who is affected and how.",
    },
    "incentives": {
        "description": "Follow the money and power.",
    },
    "second_order": {
        "description": "What happens next that nobody is discussing.",
    },
    "language_framing": {
        "description": "How the story is told shapes belief.",
    },
}
