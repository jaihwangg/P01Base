import unreal,json,shutil
from pathlib import Path
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
path="/Game/PJ2DMX/Maps/L_DemoStage2"
assert level.load_level(path)
existing=list(actors.get_all_level_actors())
assert not any(a.get_class().get_name()=="PJLiveDMXActor" for a in existing)
patches=[]
targets=[]
for a in existing:
    if a.get_class().get_name() in ("BP_MovingHead_C","BP_WashLED_C","BP_StaticHead_C"):
        targets.append(a)
        component=a.get_component_by_class(unreal.DMXComponent)
        patch=component.get_fixture_patch()
        if patch and patch not in patches: patches.append(patch)
    if isinstance(a,unreal.LevelSequenceActor):
        settings=a.get_editor_property("playback_settings")
        settings.set_editor_property("auto_play",False)
        a.set_editor_property("playback_settings",settings)
controller=actors.spawn_actor_from_class(unreal.PJLiveDMXActor,unreal.Vector(0,0,0))
controller.set_actor_label("PJ_LiveDJ_DMX")
controller.set_folder_path("Control/LiveDJ")
controller.set_editor_property("patches",patches)
controller.set_editor_property("target_fixtures",targets)
devices=controller.list_input_devices()
unreal.log("PJ_INPUT_DEVICES "+str(devices))
controller.set_editor_property("device_index",-1)
controller.set_editor_property("channel_count",2)
results=[]
for value in (0.0,0.5,1.0):
    controller.apply_music_level(value)
    # In the commandlet, read back the output port through the patch cache.
    row=[]
    for patch in patches:
        attribute=unreal.DMXAttributeName()
        attribute.set_editor_property("name","Dimmer")
        row.append(str(patch.get_attribute_value(attribute)))
    results.append({"level":value,"readback":row})
controller.apply_music_level(0)
assert level.save_current_level()
assert level.load_level(path)
loaded=[a for a in actors.get_all_level_actors() if a.get_class().get_name()=="PJLiveDMXActor"]
assert len(loaded)==1
assert len(loaded[0].get_editor_property("target_fixtures"))==len(targets)
Path(r"C:/Work/PJ2DMX/P01Base/Saved/live-dmx-validation.json").write_text(json.dumps({"patches":len(patches),"devices":[str(d) for d in devices],"readback":results,"reload":"PASS"},indent=2),encoding="utf-8")
unreal.log("PJ_LIVE_SETUP_PASS")
