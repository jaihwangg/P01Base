import unreal,json
from pathlib import Path
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level("/Game/PJ2DMX/Maps/L_DemoStage2")
controller=next(a for a in actors.get_all_level_actors() if a.get_class().get_name()=="PJLiveDMXActor")
patches=[]
for a in controller.get_editor_property("target_fixtures"):
 c=a.get_component_by_class(unreal.DMXComponent)
 if c:
  p=c.get_fixture_patch()
  if p and p not in patches: patches.append(p)
assert len(patches)==17, str(len(patches))
controller.set_editor_property("patches",patches)
attribute=unreal.DMXAttributeName()
attribute.set_editor_property("name","Dimmer")
results=[]
for value in (0.0,0.5,1.0):
 controller.apply_music_level(value)
 readings=[(v,v>=0) for v in controller.read_dimmer_values()]
 assert len(readings)==17
 results.append({"level":value,"readback":[list(r) for r in readings]})
controller.apply_music_level(0)
controller.set_editor_property("use_test_signal",False)
controller.start_input()
status=controller.get_editor_property("input_status")
controller.stop_input()
Path(r"C:/Work/PJ2DMX/P01Base/Saved/live-dmx-loopback.json").write_text(json.dumps({"results":results,"capture_status":status},indent=2),encoding="utf-8")
assert all(ok and val==round(row["level"]*255+0.000001) for row in results for val,ok in row["readback"])
unreal.log("PJ_LOOPBACK_PASS")
