"""Verify a recorded physical rollout; no Isaac Sim installation needed."""
import argparse
import json
import math
from pathlib import Path

def verify(folder):
    folder=Path(folder)
    rows=json.loads((folder/'trajectory.json').read_text())
    params=json.loads((folder/'parameters.json').read_text())
    hold=[r for r in rows if 4 <= r['time'] <= 6.1]
    assert len(hold)>=60, 'Missing hold trajectory'
    start=hold[0]['cube_position']
    z=[r['cube_position'][2] for r in hold]
    displacement=max(math.dist(start,r['cube_position']) for r in hold)
    # Bounding spheres conservatively enclose any orientation of the cube and platform.
    gaps=[math.dist(r['cube_position'],r['support_position'])-math.sqrt(3)*params['size']/2-math.sqrt(.032**2+.032**2+.018**2)/2 for r in hold]
    released=[r for r in rows if r['time']>=8.5]
    release_drop=start[2]-min(r['cube_position'][2] for r in released) if released else 0.
    support_force=max(math.dist(r['contact_normal_forces_N']['support'],[0,0,0]) for r in hold)
    finger_force=min(sum(math.dist(v,[0,0,0]) for n,v in r['contact_normal_forces_N'].items() if n not in ['support','hand_base_link']) for r in hold)
    checks={
        'finger_contact_present':finger_force>.05,
        'no_support_contact':support_force<1e-5,
        'held_at_least_two_simulation_seconds':hold[-1]['time']-hold[0]['time']>=2.,
        'remained_near_grasp_height':min(z)>.22+params['cube_z']-.025,
        'drift_under_10mm':displacement<.01,
        'support_fully_separated':min(gaps)>.005,
        'falls_after_opening':release_drop>.08,
    }
    result={'pass':all(checks.values()),'checks':checks,'hold_duration_s':hold[-1]['time']-hold[0]['time'], 'maximum_drift_m':displacement,'height_range_m':[min(z),max(z)],'minimum_support_gap_bound_m':min(gaps),'release_drop_m':release_drop,'minimum_finger_normal_force_sum_N':finger_force,'maximum_support_normal_force_N':support_force}
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args()
    result=verify(args.folder)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['pass'] else 1)
