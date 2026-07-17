# ABOUTME: Algorithmic pitch generation from ranked clusters.
# ABOUTME: Produces exactly 3 differentiated pitch candidates per brief.
"""Pitch generation for the Newsroom pipeline."""

from newsroom.models import BriefCluster, BriefPack, Pitch, PitchSet
from newsroom.pitches.angles import ANGLES

_ANGLE_ORDER = [
    "trend_analysis",
    "skeptics_take",
    "human_impact",
    "incentives",
    "second_order",
    "language_framing",
]


def _dedupe_preserve_order(urls: list[str]) -> list[str]:
    seen: list[str] = []
    for url in urls:
        if url not in seen:
            seen.append(url)
    return seen


def _pitch_from_cluster(
    cluster: BriefCluster,
    angle_name: str,
    beat: str,
    date_str: str,
    index: int,
) -> Pitch:
    angle_description = ANGLES[angle_name]["description"]
    source_urls = _dedupe_preserve_order([str(item.url) for item in cluster.items])
    key_points = [item.title for item in cluster.items[:5]]
    return Pitch(
        pitch_id=f"{beat}-{date_str}-{index}",
        title=cluster.label,
        thesis_angle=f"{angle_description} Centered on: {cluster.label}.",
        why_now=(
            f"{cluster.size} stories across {cluster.source_diversity} source(s) "
            f"are covering this within the current window."
        ),
        key_points=key_points,
        source_urls=source_urls,
        risk_flags=[],
        cluster_id=cluster.cluster_id,
        angle=angle_name,
    )


def generate_pitches(brief: BriefPack, n: int = 3) -> PitchSet:
    """Generate n pitch candidates from a BriefPack.

    Strategy varies by cluster count (clusters are assumed pre-ranked,
    highest-priority first):
    - >=3 clusters: one pitch per top-3 cluster
    - 2 clusters: one pitch each + second angle on top cluster
    - 1 cluster: three different angle templates
    - 0 clusters: raises an error
    """
    if n != 3:
        msg = (
            f"generate_pitches only supports n=3 (PitchSet requires exactly 3), got {n}"
        )
        raise ValueError(msg)

    clusters = brief.clusters
    if not clusters:
        msg = "Cannot generate pitches from a brief pack with zero clusters"
        raise ValueError(msg)

    date_str = brief.date.isoformat()
    pitches: list[Pitch] = []

    if len(clusters) >= 3:
        for index, (cluster, angle) in enumerate(
            zip(clusters[:3], _ANGLE_ORDER[:3], strict=True), start=1
        ):
            pitches.append(
                _pitch_from_cluster(cluster, angle, brief.beat, date_str, index)
            )
    elif len(clusters) == 2:
        pitches.append(
            _pitch_from_cluster(clusters[0], _ANGLE_ORDER[0], brief.beat, date_str, 1)
        )
        pitches.append(
            _pitch_from_cluster(clusters[1], _ANGLE_ORDER[1], brief.beat, date_str, 2)
        )
        pitches.append(
            _pitch_from_cluster(clusters[0], _ANGLE_ORDER[2], brief.beat, date_str, 3)
        )
    else:
        cluster = clusters[0]
        for index, angle in enumerate(_ANGLE_ORDER[:3], start=1):
            pitches.append(
                _pitch_from_cluster(cluster, angle, brief.beat, date_str, index)
            )

    return PitchSet(
        beat=brief.beat,
        date=brief.date,
        pitches=pitches,
        brief_pack_ref=f"{brief.beat}-{date_str}",
        generated_at=brief.generated_at,
    )
