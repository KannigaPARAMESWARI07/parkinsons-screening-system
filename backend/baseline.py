import json
import os
from datetime import datetime
from typing import List, Optional
from collections import defaultdict

BASELINE_DIR = 'user_baselines'
os.makedirs(BASELINE_DIR, exist_ok=True)

def _path(user_id: str) -> str:
    return os.path.join(BASELINE_DIR, f"{user_id}.json")

def load_baseline(user_id: str) -> dict:
    path = _path(user_id)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {'user_id': user_id, 'sessions': [], 'baseline_established': False}

def save_session(user_id: str, fusion_score: float, modality_scores: dict):
    data = load_baseline(user_id)
    data['sessions'].append({
        'timestamp': datetime.utcnow().isoformat(),
        'fusion_score': fusion_score,
        'modality_scores': modality_scores,
    })
    
    # Establish baseline after 7 sessions
    if len(data['sessions']) >= 7 and not data['baseline_established']:
        scores = [s['fusion_score'] for s in data['sessions'][:7]]
        data['baseline_mean'] = sum(scores) / len(scores)
        data['baseline_std']  = (
            sum((x - data['baseline_mean'])**2 for x in scores) / len(scores)
        ) ** 0.5
        data['baseline_established'] = True
    
    with open(_path(user_id), 'w') as f:
        json.dump(data, f, indent=2)

def get_baseline_for_fusion(user_id: str) -> Optional[dict]:
    data = load_baseline(user_id)
    if not data['baseline_established']:
        return None
    return {
        'scores': [s['fusion_score'] / 100 for s in data['sessions'][-30:]],
        'mean': data['baseline_mean'] / 100,
        'std':  data['baseline_std'] / 100,
    }

def get_history(user_id: str, limit: int = 30) -> List[dict]:
    data = load_baseline(user_id)
    sessions = data['sessions'][-limit:]
    return [
        {
            'date': s['timestamp'][:10],
            'score': s['fusion_score'],
            'modalities': s['modality_scores'],
        }
        for s in sessions
    ]