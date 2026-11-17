import unreal, json
from pathlib import Path
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
panels=[a for a in actors.get_all_level_actors() if a.get_actor_label()=='PJ_RearPanel_Video']
assert len(panels)==1, 'Expected one rear-panel live video surface'
p=panels[0]
assert p.get_attach_parent_actor().get_actor_label()=='PJ_RearPanel'
assert p.get_editor_property('media_source')
assert p.get_editor_property('media_player')
assert p.get_editor_property('media_texture')
assert p.get_editor_property('screen').get_material(0)
_,extent=p.get_actor_bounds(False)
parent_scale=p.get_attach_parent_actor().get_actor_scale3d()
assert abs(extent.x-50*abs(parent_scale.x))<1, str(extent)
assert abs(extent.z-50*abs(parent_scale.z))<1, str(extent)
assert not p.get_editor_property('media_source').get_editor_property('capture_audio')
assert len([a for a in actors.get_all_level_actors() if a.get_actor_label()=='PJ_LiveDJ_DMX'])==1
Path('C:/Work/PJ2DMX/P01Base/Saved/live-video-validation.json').write_text(json.dumps({'reload':'PASS','surface':p.get_path_name(),'audio_capture':False},indent=2))
unreal.log('PJ_VIDEO_VALIDATION_PASS')
