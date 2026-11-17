import unreal,json,shutil
from pathlib import Path
root=Path('C:/Work/PJ2DMX/P01Base')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
original=list(actors.get_all_level_actors())
assert not any(a.get_actor_label()=='PJ_CrowdInput' for a in original),'Already installed'
backup=root/'Saved/L_DemoStage2-before-p03b.umap'
assert not backup.exists(),'Backup already exists; inspect before repeating'
shutil.copy2(root/'Content/PJ2DMX/Maps/L_DemoStage2.umap',backup)
dj=next(a for a in original if a.get_actor_label()=='PJ_LiveDJ_DMX')
keys=('device_index','first_channel','channel_count','use_test_signal','gain','noise_floor','attack_seconds','release_seconds')
settings={k:dj.get_editor_property(k) for k in keys}
before={a.get_name():str(a.get_actor_transform()) for a in original}
crowd=actors.spawn_actor_from_class(unreal.PJCrowdInputActor,unreal.Vector(0,0,0))
crowd.set_actor_label('PJ_CrowdInput');crowd.set_folder_path('Control/Crowd')
crowd.set_editor_property('wave_file','TestInputs/CrowdLevelSteps.wav')
crowd.set_editor_property('input_mode',unreal.PJCrowdInputMode.TEST_STEPS)
assert all(str(a.get_actor_transform())==before[a.get_name()] for a in original)
assert all(dj.get_editor_property(k)==v for k,v in settings.items())
assert levels.save_current_level()
assert levels.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
loaded=list(actors.get_all_level_actors())
assert len(loaded)==len(original)+1
assert len([a for a in loaded if a.get_actor_label()=='PJ_CrowdInput'])==1
dj=next(a for a in loaded if a.get_actor_label()=='PJ_LiveDJ_DMX')
assert all(dj.get_editor_property(k)==v for k,v in settings.items())
(root/'Saved/P03Tests/setup.json').write_text(json.dumps({'reload':'PASS','original_actors':len(original),'added':1,'dj_settings_preserved':settings,'backup':str(backup)},indent=2))
unreal.log('PJ_CROWD_SETUP_PASS')
