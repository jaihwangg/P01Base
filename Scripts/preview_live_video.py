"""GPU NDI check; launch using -ExecCmds, no map save."""
import unreal,time,json
from pathlib import Path
root=Path('C:/Work/PJ2DMX/P01Base/Saved')
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
panel=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='PJ_RearPanel_Video')
loc=panel.get_attach_parent_actor().get_actor_location()
cam=actors.spawn_actor_from_class(unreal.CameraActor,loc+unreal.Vector(0,1100,0),unreal.Rotator(pitch=0,yaw=-90,roll=0))
panel.open_video()
deadline=time.monotonic()+25; step=0; busy=False

def tick(dt):
    global step,deadline,busy
    if busy or time.monotonic()<deadline: return
    busy=True
    try:
        if step==0:
            p=panel.get_editor_property('media_player'); t=panel.get_editor_property('media_texture')
            data={'playing':p.is_playing(),'preparing':p.is_preparing(),'error':p.has_error(),'url':p.get_url(),'texture_width':t.get_width(),'texture_height':t.get_height(),'video_tracks':p.get_num_tracks(unreal.MediaPlayerTrack.VIDEO),'screen_transform':str(panel.get_actor_transform()),'camera':str(cam.get_actor_transform()),'bounds':str(panel.get_actor_bounds(False))}
            (root/'live-video-runtime.json').write_text(json.dumps(data,indent=2))
            unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(root/'RearPanel-NDI.png'),camera=cam)
            unreal.log('PJ_VIDEO_RUNTIME '+str(data))
        elif step==1:
            cam.set_actor_location(loc+unreal.Vector(0,350,0),False,False)
        elif step==2:
            unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(root/'RearPanel-LED-closeup.png'),camera=cam)
        else:
            panel.close_video()
            unreal.unregister_slate_post_tick_callback(handle)
            unreal.SystemLibrary.quit_editor()
        step+=1
        deadline=time.monotonic()+12
    except Exception:
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.SystemLibrary.quit_editor()
        raise
    finally:
        busy=False
handle=unreal.register_slate_post_tick_callback(tick)
