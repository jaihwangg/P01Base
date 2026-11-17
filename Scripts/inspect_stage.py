import unreal, json
from pathlib import Path
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report = {}
for name in ("/Game/DMXTemplate/Maps/Fixtures","/Game/DMXTemplate/Maps/PixelMapping","/Game/DMXTemplate/Maps/WaterFountain","/Game/PJ2DMX/Maps/L_DemoStage2"):
    assert levels.load_level(name)
    rows = []
    for a in actors.get_all_level_actors():
        v=a.get_actor_location()
        r=a.get_actor_rotation()
        rows.append(dict(label=a.get_actor_label(),cls=a.get_class().get_path_name(),location=[v.x,v.y,v.z],rotation=[r.pitch,r.yaw,r.roll],folder=str(a.get_folder_path())))
    report[name]=rows
Path(r"C:/Work/PJ2DMX/P01Base/Saved/stage-inventory.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
unreal.log("PJ_INVENTORY_PASS")
