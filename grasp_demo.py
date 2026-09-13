"""O6 contact grasp: dynamic cube, retracting support, hold and release."""
import argparse
import json
import select
import sys
import time
from pathlib import Path
import faulthandler
faulthandler.enable()
faulthandler.dump_traceback_later(90, repeat=True)
p = argparse.ArgumentParser()
p.add_argument('--output', default='outputs/run')
p.add_argument('--cube-x', type=float, default=.043)
p.add_argument('--cube-y', type=float, default=0.)
p.add_argument('--cube-z', type=float, default=.095)
p.add_argument('--size', type=float, default=.05)
p.add_argument('--finger', type=float, default=1.30)
p.add_argument('--thumb-yaw', type=float, default=1.20)
p.add_argument('--thumb-pitch', type=float, default=.5)
p.add_argument('--render', action='store_true')
p.add_argument('--gui', action='store_true', help='Open the desktop viewport and record cameras.')
p.add_argument('--wait-for-start', action='store_true', help='Wait for the Start grasp button (or terminal Enter) before moving.')
p.add_argument('--keep-open', action='store_true', help='Keep the paused window open after the demo.')
p.add_argument('--asset', type=Path, default=Path(__file__).resolve().parent/'assets/o6_hand.usd')
p.add_argument('--isaaclab', type=Path, default=Path('/opt/IsaacLab'))
p.add_argument('--duration', type=float, default=9.)
args = p.parse_args()
if args.gui:
    args.render = True
if (args.wait_for_start or args.keep_open) and not args.gui:
    p.error('--wait-for-start and --keep-open require --gui')
out = Path(args.output).resolve(); out.mkdir(parents=True, exist_ok=True)
from isaacsim import SimulationApp
app = SimulationApp({'headless': not args.gui, 'create_new_stage': False, 'sync_loads': False,
                     'width': 960, 'height': 720, 'anti_aliasing': 0, 'disable_viewport_updates': not args.gui,
                     'extra_args': ['--/exts/omni.kit.window.viewport/blockingGetViewportDrawable=false',f'--/exts/omni.renderer.core/present/enabled={str(args.gui).lower()}','--/app/useFabricSceneDelegate=false','--/rtx/hydra/readTransformsFromFabricInRenderDelegate=false','--/physics/updateToUsd=true','--/physics/fabricUpdateTransformations=true','--/persistent/rtx/modes/rt/enabled=true']}, experience=str(args.isaaclab/'apps'/('isaaclab.python.rendering.kit' if args.gui else 'isaaclab.python.headless.rendering.kit')))
import omni.usd
import carb
carb.settings.get_settings().set('/rtx/debugView/target','')
omni.usd.get_context().new_stage()
import numpy as np
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema, UsdShade, UsdLux, Gf
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
from isaacsim.core.api.materials import PhysicsMaterial
from isaacsim.core.prims import SingleArticulation, RigidPrim
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.core.utils.stage import add_reference_to_stage

print('BUILD_WORLD',flush=True)
world = World(stage_units_in_meters=1., physics_dt=1/240, rendering_dt=1/30, backend='numpy', device='cpu')
world.get_physics_context().enable_fabric(False)
world.get_physics_context().set_physx_update_transformations_settings(True, True, False)
stage = omni.usd.get_context().get_stage()
mat = PhysicsMaterial('/World/ContactMaterial', static_friction=1.2, dynamic_friction=1., restitution=0.)
world.scene.add(FixedCuboid('/World/Floor', name='floor', position=np.array([0,0,-.025]),
                           scale=np.array([2.,2.,.05]), color=np.array([.08,.11,.15]), physics_material=mat))
asset = args.asset.resolve()
if not asset.is_file():
    raise FileNotFoundError(f'O6 asset not found: {asset}')
add_reference_to_stage(str(asset), '/World/Hand')
hand_root = '/World/Hand/linker_o6_right_v1_0_urdf'
height=.22
UsdGeom.Xformable(stage.GetPrimAtPath('/World/Hand')).AddTranslateOp().Set((0,0,height))
# Make collision meshes editable to apply the same physical material on each finger.
for prim in list(stage.Traverse()):
    if prim.IsInstance(): prim.SetInstanceable(False)
for prim in stage.Traverse():
    if prim.HasAPI(UsdPhysics.CollisionAPI):
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat.material, UsdShade.Tokens.weakerThanDescendants, 'physics')
        co=PhysxSchema.PhysxCollisionAPI.Apply(prim)
        co.CreateContactOffsetAttr(.001)
        co.CreateRestOffsetAttr(0.)
    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
        rb=PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        rb.CreateDisableGravityAttr(False)
        rb.CreateMaxDepenetrationVelocityAttr(.5)
    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
        ar=PhysxSchema.PhysxArticulationAPI.Apply(prim)
        ar.CreateSolverPositionIterationCountAttr(32)
        ar.CreateSolverVelocityIterationCountAttr(4)
        ar.CreateEnabledSelfCollisionsAttr(False)
    if prim.IsA(UsdPhysics.RevoluteJoint):
        drive=UsdPhysics.DriveAPI.Apply(prim,'angular')
        drive.CreateStiffnessAttr(3.)
        drive.CreateDampingAttr(.12)
        drive.CreateMaxForceAttr(.5)
        # Software target coupling follows the URDF ratios; native mimic is removed.
        # This is a six-command simulation approximation, not a calibrated transmission.
        if prim.HasAPI(PhysxSchema.PhysxMimicJointAPI,'rotY'):
            prim.RemoveAPI(PhysxSchema.PhysxMimicJointAPI,'rotY')
hand=world.scene.add(SingleArticulation(hand_root, name='o6'))
center=np.array([args.cube_x,args.cube_y,args.cube_z+height])
size=args.size
cube=world.scene.add(DynamicCuboid('/World/Cube', name='cube', position=center,
                    size=size, mass=.05, color=np.array([1.,.29,.055]), physics_material=mat))
PhysxSchema.PhysxRigidBodyAPI.Apply(stage.GetPrimAtPath('/World/Cube')).CreateEnableCCDAttr(True)
# The support is a kinematic rigid body, moved downward and sideways after closure.
support_pos=center+np.array([0,0,-size/2-.009])
support=DynamicCuboid('/World/Support', name='support', position=support_pos,
                        scale=np.array([.032,.032,.018]), mass=1., color=np.array([.22,.48,.64]),physics_material=mat)
UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath('/World/Support')).CreateKinematicEnabledAttr(True)
contact_names=['hand_base_link','index_proximal','index_distal','middle_proximal','middle_distal','ring_proximal','ring_distal','pinky_proximal','pinky_distal','thumb_metacarpals_base2','thumb_metacarpals','thumb_distal']
contact_view=RigidPrim('/World/Cube',name='contact_monitor',track_contact_forces=True,
    contact_filter_prim_paths_expr=[hand_root+'/'+n for n in contact_names]+['/World/Support'],
    max_contact_count=128,disable_stablization=False)
# Visible fixed wrist pedestal, without collision near the cube.
world.scene.add(FixedCuboid('/World/Mount',name='mount',position=np.array([0,0,height/2]),scale=np.array([.045,.085,height]),color=np.array([.18,.23,.30])))
light=UsdLux.DomeLight.Define(stage,'/World/Light'); light.CreateIntensityAttr(900.)
light2=UsdLux.DistantLight.Define(stage,'/World/Key'); light2.CreateIntensityAttr(2000.)
UsdGeom.Xformable(light2).AddRotateXYZOp().Set((-35,-30,0))
camera=None
overview=None
if args.render:
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('isaacsim.sensors.camera')
    from isaacsim.sensors.camera import Camera
    camera=Camera('/World/Camera',frequency=30,resolution=(960,720))
    view=Gf.Matrix4d().SetLookAt(Gf.Vec3d(.48,.45,.46),Gf.Vec3d(.025,0,.30),Gf.Vec3d(0,0,1)).GetInverse()
    camera.set_world_pose(position=np.array(view.ExtractTranslation()),orientation=np.array([view.ExtractRotationQuat().GetReal(),*view.ExtractRotationQuat().GetImaginary()]),camera_axes='usd')
    camera.set_clipping_range(.01,10.)
    overview=Camera('/World/Overview',frequency=30,resolution=(480,720))
    ov=Gf.Matrix4d().SetLookAt(Gf.Vec3d(.62,.75,.55),Gf.Vec3d(.075,0,.205),Gf.Vec3d(0,0,1)).GetInverse()
    overview.set_world_pose(position=np.array(ov.ExtractTranslation()),orientation=np.array([ov.ExtractRotationQuat().GetReal(),*ov.ExtractRotationQuat().GetImaginary()]),camera_axes='usd')
    overview.set_focal_length(5.0)
    overview.set_clipping_range(.01,10.)
print('RESET',flush=True)
stage.Flatten().Export(str(out/'scene_initial.usd'))
world.reset()
support.initialize()
contact_view.initialize()
print('DOFS',hand.dof_names,flush=True)
if camera:
    camera.initialize()
    overview.initialize()
initial=np.zeros(hand.num_dof)
hand.set_joint_positions(initial)
indices=np.arange(hand.num_dof)
closed=np.array([args.thumb_yaw if n=='thumb_cmc_yaw' else args.thumb_pitch if n=='thumb_cmc_pitch' else 1.86*args.thumb_pitch if n=='thumb_ip' else .89*args.finger if n.endswith('_dip') else args.finger for n in hand.dof_names])
rows=[]
frames=[]
overview_frames=[]
demo_status = None
demo_button = None
start_request = {'start': False}
if args.gui:
    import omni.ui as ui
    from omni.kit.viewport.utility import get_active_viewport
    viewport = get_active_viewport()
    if viewport:
        viewport.camera_path = '/World/Overview'
    demo_window = ui.Window('O6 Grasp Demo', width=350, height=185)
    with demo_window.frame:
        with ui.VStack(spacing=8):
            ui.Label('O6 contact grasp | dynamic cube', height=24)
            demo_status = ui.Label('Ready. Click Start grasp.', height=28)
            demo_button = ui.Button('Start grasp', height=36,
                clicked_fn=lambda: start_request.__setitem__('start', True))
            with ui.HStack(height=28, spacing=6):
                ui.Button('Whole scene', clicked_fn=lambda: setattr(viewport, 'camera_path', '/World/Overview'))
                ui.Button('Close-up', clicked_fn=lambda: setattr(viewport, 'camera_path', '/World/Camera'))
            ui.Label('Close the Isaac Sim window to exit.', height=22)
    for _ in range(10):
        world.render()
if args.wait_for_start:
    faulthandler.cancel_dump_traceback_later()
    print('READY: Click Start grasp in the O6 Grasp Demo panel, or press ENTER here.', flush=True)
    accept_stdin = True
    while app.is_running() and not start_request['start']:
        world.render()
        if accept_stdin and select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            if line:
                start_request['start'] = True
            else:
                accept_stdin = False
        time.sleep(.01)
    if not app.is_running():
        app.close()
        raise SystemExit(0)
    countdown_end = time.monotonic()+3
    demo_button.enabled = False
    while app.is_running() and time.monotonic()<countdown_end:
        demo_status.text = f'Starting in {max(1, int(countdown_end-time.monotonic())+1)} s...'
        world.render()
        time.sleep(.01)
if demo_button:
    demo_button.enabled = False
print('SIMULATE',flush=True)
wall_start = time.monotonic()
for step in range(round(args.duration*240)):
    if args.gui and not app.is_running():
        app.close()
        raise SystemExit(0)
    t=step/240
    # settle 0-1, close 1-3, retract 3-4, hold 4-7, release 7-8.
    alpha=float(np.clip((t-1)/2,0,1))
    if t>=7: alpha=float(np.clip(1-(t-7),0,1))
    alpha=alpha*alpha*(3-2*alpha)
    hand.apply_action(ArticulationAction(joint_positions=closed*alpha,joint_indices=indices))
    retract=float(np.clip(t-3,0,1)); retract=retract*retract*(3-2*retract)
    support_target=support_pos+np.array([.16*retract,0,-.13*retract])
    support.set_world_pose(position=support_target)
    # PhysX does not publish kinematic poses back to USD in this version.
    # Keep the rendered support at the exact same pose as its physical body.
    stage.GetPrimAtPath('/World/Support').GetAttribute('xformOp:translate').Set(Gf.Vec3d(*support_target))
    world.step(render=False)
    if step%8==0:
        pos,rot=cube.get_world_pose()
        row={'time':round(t+1/240,6),'cube_position':pos.tolist(),'cube_orientation_wxyz':rot.tolist(),'cube_velocity':cube.get_linear_velocity().tolist(),
             'contact_normal_forces_N':dict(zip(contact_names+['support'],contact_view.get_contact_force_matrix(dt=1/240)[0].tolist())),'support_position':support.get_world_pose()[0].tolist(),'joint_positions':hand.get_joint_positions().tolist()}
        rows.append(row)
        if demo_status:
            phase = 'Settling' if t<1 else 'Closing fingers' if t<3 else 'Retracting support' if t<4 else 'Holding without support' if t<7 else 'Opening / release'
            demo_status.text = f'{t:04.1f} s | {phase}'
        if camera:
            world.render()
            rgba=camera.get_rgba()
            if rgba is not None and rgba.size:
                frames.append(rgba[:,:,:3].copy())
                overview_frames.append(overview.get_rgba()[:,:,:3].copy())
                if step%240==0:
                    import imageio.v2 as imageio
                    imageio.imwrite(out/f'preview_{step//240}.png',frames[-1])
        if args.gui:
            time.sleep(max(0., wall_start+(step+8)/240-time.monotonic()))
        if step==1440: stage.Flatten().Export(str(out/'scene_held.usd'))
        if step%240==0: print('STATE',round(t,2),pos.tolist(),flush=True)
print('SIM_DONE',flush=True)
if demo_status:
    demo_status.text = 'Demo complete. Saving videos...'
    world.render()
(out/'trajectory.json').write_text(json.dumps(rows,indent=2))
(out/'parameters.json').write_text(json.dumps(vars(args),indent=2,default=str))
hold=[r for r in rows if 4<=r['time']<=6.1]
z=[r['cube_position'][2] for r in hold]
result={'hold_seconds':2.,'height_min':min(z) if z else None,'height_max':max(z) if z else None,'initial_height':center[2], 'pass':bool(z and min(z)>center[2]-.02 and max(z)-min(z)<.015)}
(out/'result.json').write_text(json.dumps(result,indent=2))
print('RESULT',result,flush=True)
if frames:
    import imageio.v2 as imageio
    for i in [0,len(frames)//3,2*len(frames)//3,len(frames)-1]: imageio.imwrite(out/f'frame_{i:04d}.png',frames[i])
    try:
        imageio.mimwrite(out/'grasp_raw.mp4',frames,fps=30,codec='libx264',quality=8)
        imageio.mimwrite(out/'overview_raw.mp4',overview_frames,fps=30,codec='libx264',quality=8)
    except Exception as e:
        print('VIDEO_ERROR',str(e),flush=True)
        np.save(out/'frames.npy',np.stack(frames))
from verify import verify
verification=verify(out)
print('VERIFICATION',json.dumps(verification),flush=True)
faulthandler.cancel_dump_traceback_later()
if demo_status:
    demo_status.text = 'PASS. Demo finished.' if verification['pass'] else 'Verification failed; see log.'
if args.keep_open:
    world.pause()
    print('DONE: Recording is saved. Close the Isaac Sim window to exit.', flush=True)
    while app.is_running():
        app.update()
        time.sleep(.01)
app.close()
raise SystemExit(0 if verification["pass"] else 1)
