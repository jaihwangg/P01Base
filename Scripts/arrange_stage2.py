import unreal, json
from pathlib import Path
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level("/Game/PJ2DMX/Maps/L_DemoStage2")
original=list(actors.get_all_level_actors())
assert not any(a.get_actor_label()=="PJ_DJ_Stage" for a in original), "Already arranged"
before={a.get_name():a.get_class().get_path_name() for a in original}
mapping={"US_Truss":"Stage/Truss/Upper","VerticalTrusses":"Stage/Truss/Vertical","Drape":"Stage/Drapes","MovingHeads":"Lighting/Rear/MovingHeads","LEDWash":"Lighting/Rear/Wash","StaticFixtures":"Lighting/Floor/Static","Strobes":"Lighting/Rear/Strobes","MovingMirrors":"Lighting/Rear/Mirrors","MatrixFixtures":"Lighting/Rear/Matrix","PyroModules":"Effects/Pyro","Fireworks":"Effects/Fireworks","Lasers":"Effects/Lasers"}
for a in original:
    folder=str(a.get_folder_path())
    a.set_folder_path(mapping.get(folder,"Environment"))
    if isinstance(a,unreal.LevelSequenceActor): a.set_folder_path("Control/TemplateSequence")
    if isinstance(a,unreal.PlayerStart): a.set_folder_path("Audience")
cube=unreal.load_asset("/Engine/BasicShapes/Cube")
def box(label,loc,scale,folder):
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc))
    a.set_actor_label(label)
    a.static_mesh_component.set_static_mesh(cube)
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.set_folder_path(folder)
    return a
box("PJ_DJ_Stage",(0,-400,30),(9,4.5,0.6),"Stage/Platform")
box("PJ_DJ_Booth",(0,-420,115),(2.4,0.8,1.1),"Stage/Booth")
box("PJ_RearPanel",(0,-960,330),(7,0.12,3.5),"Stage/Panel")
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(0,1000,260),unreal.Rotator(-4,-90,0))
camera.set_actor_label("PJ_AudienceCamera")
camera.set_folder_path("Audience")
camera.camera_component.set_editor_property("field_of_view",75.0)
added=[]
for clsname,group in (("BP_MovingHead_C","MovingHeads"),("BP_WashLED_C","Wash")):
    sources=sorted([a for a in original if a.get_class().get_name()==clsname],key=lambda a:a.get_actor_location().x)
    for index,source in enumerate((sources[0],sources[-1])):
        a=actors.spawn_actor_from_class(source.get_class(), source.get_actor_location(), source.get_actor_rotation())
        a.get_component_by_class(unreal.DMXComponent).set_fixture_patch(source.get_component_by_class(unreal.DMXComponent).get_fixture_patch())
        assert a
        x=(-650,650)[index]
        y=150 if group=="MovingHeads" else -50
        target=unreal.Vector(x,y,source.get_actor_location().z)
        a.set_actor_location(target,False,False)
        a.set_actor_label("PJ_Front_"+group+"_"+str(index+1))
        a.set_folder_path("Lighting/Front/"+group)
        a.tags=list(a.tags)+[unreal.Name("Front"),unreal.Name("SharedTemplatePatch")]
        added.append(a.get_actor_label())
assert levels.save_current_level()
assert levels.load_level("/Game/PJ2DMX/Maps/L_DemoStage2")
after=list(actors.get_all_level_actors())
names={a.get_name():a.get_class().get_path_name() for a in after}
assert all(names.get(k)==v for k,v in before.items())
labels={a.get_actor_label() for a in after}
assert set(added+["PJ_DJ_Stage","PJ_DJ_Booth","PJ_RearPanel","PJ_AudienceCamera"])<=labels
assert len(after)==len(original)+8
Path(r"C:/Work/PJ2DMX/P01Base/Saved/stage2-result.json").write_text(json.dumps({"original_actors":len(original),"saved_actors":len(after),"added_lights":added,"reload":"PASS","shared_patch":True},indent=2),encoding="utf-8")
unreal.log("PJ_STAGE2_RELOAD_PASS")
