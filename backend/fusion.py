from dataclasses import dataclass
from typing import Optional

WEIGHTS = {
    'voice':  0.40,
    'tremor': 0.25,
    'gait':   0.20,
    'tapping': 0.15,
}

@dataclass
class ModalityScore:
    voice:   Optional[float] = None  # 0.0–1.0 probability
    tremor:  Optional[float] = None
    gait:    Optional[float] = None
    tapping: Optional[float] = None

@dataclass
class FusionResult:
    raw_score:     float        # 0–100
    risk_level:    str          # 'low' | 'moderate' | 'high'
    modality_scores: dict
    advice:        str
    confidence:    float        # based on how many modalities were available

def fuse_scores(scores: ModalityScore, personal_baseline: Optional[dict] = None) -> FusionResult:
    available = {
        k: getattr(scores, k)
        for k in WEIGHTS
        if getattr(scores, k) is not None
    }
    
    if not available:
        raise ValueError("At least one modality score is required.")
    
    # Renormalize weights for available modalities
    total_weight = sum(WEIGHTS[k] for k in available)
    weighted_sum = sum(WEIGHTS[k] * v for k, v in available.items())
    normalized_score = weighted_sum / total_weight  # 0.0–1.0
    
    # Adjust against personal baseline if available
    if personal_baseline and len(personal_baseline.get('scores', [])) >= 7:
        baseline_mean = sum(personal_baseline['scores']) / len(personal_baseline['scores'])
        baseline_std  = (
            sum((x - baseline_mean)**2 for x in personal_baseline['scores'])
            / len(personal_baseline['scores'])
        ) ** 0.5
        
        if baseline_std > 0:
            z_score = (normalized_score - baseline_mean) / baseline_std
            # Blend raw + z-score-adjusted (gentle 20% pull toward personal context)
            adjusted = normalized_score + 0.20 * (z_score * 0.1)
            normalized_score = max(0.0, min(1.0, adjusted))
    
    raw_score = round(normalized_score * 100, 1)
    confidence = round(total_weight, 2)
    
    if raw_score < 30:
        risk_level = 'low'
        advice = (
            "Your motor patterns appear within normal range. "
            "Continue regular monitoring and maintain an active lifestyle."
        )
    elif raw_score < 60:
        risk_level = 'moderate'
        advice = (
            "Some motor patterns show mild variation. "
            "Consider scheduling a check-up with your doctor and repeat the screening in 2 weeks."
        )
    else:
        risk_level = 'high'
        advice = (
            "Several motor biomarkers show patterns associated with Parkinson's risk. "
            "Please consult a neurologist for a full clinical evaluation."
        )
    
    return FusionResult(
        raw_score=raw_score,
        risk_level=risk_level,
        modality_scores={k: round(v * 100, 1) for k, v in available.items()},
        advice=advice,
        confidence=confidence,
    )