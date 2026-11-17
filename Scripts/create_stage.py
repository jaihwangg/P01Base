import unreal
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
path = "/Game/PJ2DMX/Maps/L_DemoStage"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    raise RuntimeError("Demo map already exists. Review it in the editor before rebuilding.")
else:
    assert level.new_level(path)
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
def box(label, location, scale):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location))
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor
box("Venue_Floor_20m_24m", (0,0,-25), (20,24,0.5))
box("Stage_10m_5m", (400,0,50), (5,10,1))
box("DJ_Booth", (400,0,150), (0.8,2,1))
box("Rear_Panel_8m_3m", (650,0,300), (0.1,8,3))
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-850,0,230), unreal.Rotator(0,0,0))
camera.set_actor_label("Audience_Camera")
camera.camera_component.set_editor_property("field_of_view", 65.0)
for group,x in (("Rear",580),("Front",100)):
    for index,y in enumerate((-350,350)):
        fixture_class = unreal.load_class(None, "/DMXFixtures/LightFixtures/BP_MovingHead.BP_MovingHead_C")
        assert fixture_class
        actor = actors.spawn_actor_from_class(fixture_class, unreal.Vector(x,y,500))
        actor.set_actor_label(f"{group}_MovingHead_{index+1}")
        actor.tags = [unreal.Name(group)]
light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0,0,800), unreal.Rotator(-55,-30,0))
light.set_actor_label("Work_Light")
assert level.save_current_level()
assert level.load_level(path)
labels = {a.get_actor_label() for a in actors.get_all_level_actors()}
required = {"Venue_Floor_20m_24m","Stage_10m_5m","DJ_Booth","Rear_Panel_8m_3m","Audience_Camera","Rear_MovingHead_1","Rear_MovingHead_2","Front_MovingHead_1","Front_MovingHead_2"}
assert required <= labels, required - labels
unreal.log("PJ_STAGE_RELOAD_PASS " + str(sorted(required)))



