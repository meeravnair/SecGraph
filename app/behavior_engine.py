import numpy as np
from app.models import db, BehaviorFeatures

def calculate_peer_baselines():
    """
    Computes peer-group baseline metrics across the organization.
    Returns a dictionary of peer median values.
    """
    all_behaviors = BehaviorFeatures.query.all()
    if not all_behaviors:
        return {'after_hours_count': 2.0, 'unique_devices': 1.0, 'unique_resources': 3.0}

    after_hours = [b.after_hours_count for b in all_behaviors]
    devices = [b.unique_devices for b in all_behaviors]
    resources = [b.unique_resources for b in all_behaviors]

    return {
        'after_hours_count': float(np.median(after_hours)),
        'unique_devices': float(np.median(devices)),
        'unique_resources': float(np.median(resources))
    }
