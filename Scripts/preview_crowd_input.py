import unreal,time,json
from pathlib import Path
root=Path('C:/Work/PJ2DMX/P01Base/Saved/P03Tests')
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
step=0;deadline=time.monotonic()+15;busy=False;records=[]
def tick(dt):
    global step,deadline,busy
    if busy or time.monotonic()<deadline:return
    busy=True
    try:
        if step==0:level.editor_request_begin_play()
        elif step in (1,2):
            world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            assert world,'No PIE world'
            actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.PJCrowdInputActor)
            assert len(actors)==1
            a=actors[0]
            if step==1:
                a.start_input();a.advance_measurement(6.5)
            else:
                a.set_editor_property('input_mode',unreal.PJCrowdInputMode.WAV_FILE)
                a.start_input();a.advance_measurement(6.5)
            records.append({'mode':str(a.get_editor_property('input_mode')),'rms':a.get_editor_property('raw_rms'),'level':a.get_editor_property('crowd_level'),'status':a.get_editor_property('input_status')})
            assert a.get_editor_property('raw_rms')>0.15
            unreal.SystemLibrary.execute_console_command(world,'Shot SHOWUI filename=C:/Work/PJ2DMX/P01Base/Saved/P03Tests/Meter'+str(step)+'.png')
        elif step==3:
            (root/'runtime.json').write_text(json.dumps({'result':'PASS','samples':records},indent=2))
            level.editor_request_end_play()
        else:
            unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.quit_editor()
        step+=1;deadline=time.monotonic()+8
    except Exception:
        level.editor_request_end_play()
        unreal.unregister_slate_post_tick_callback(handle)
        unreal.SystemLibrary.quit_editor()
        raise
    finally:busy=False
handle=unreal.register_slate_post_tick_callback(tick)
