import unreal,json
from pathlib import Path
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level("/Game/PJ2DMX/Maps/L_DemoStage2")
report=[]
for a in actors.get_all_level_actors():
 c=a.get_component_by_class(unreal.DMXComponent)
 if c:
  p=c.get_fixture_patch()
  if p: report.append({"actor":a.get_actor_label(),"patch":p.get_path_name(),"defaults":str(p.get_attribute_default_map())})
Path(r"C:/Work/PJ2DMX/P01Base/Saved/live-patches.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
