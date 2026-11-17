"""P-03-A read-only device readiness check. Does not save or change the map."""
import unreal,json
from pathlib import Path
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
dj=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='PJ_LiveDJ_DMX')
devices=[str(x) for x in dj.list_input_devices()]
result={'stage':'P-03-A','devices':devices,'saved_dj_settings':{k:dj.get_editor_property(k) for k in ('device_index','first_channel','channel_count','use_test_signal')},'checks':[]}
# Isolated probe actors have no fixtures, so opening them cannot send DMX.
music=[x for x in devices if 'CABLE Output' in x]
microphones=[x for x in devices if ('microphone' in x.lower() or '마이크' in x) and 'cable' not in x.lower()]
probes=[]
try:
    if music and microphones:
        for role,line in [('Music',music[0]),('Audience candidate',microphones[0])]:
            probe=actors.spawn_actor_from_class(unreal.PJLiveDMXActor,unreal.Vector())
            probes.append(probe)
            probe.set_editor_property('use_test_signal',False)
            probe.set_editor_property('device_index',int(line.split('|')[0].strip()))
            probe.set_editor_property('channel_count',1)
            probe.start_input()
            result['checks'].append({'role':role,'device':line,'status':probe.get_editor_property('input_status')})
        result['scope']='Two streams opened concurrently; sample delivery and acoustic independence not measured.'
    else:
        result['scope']='Device enumeration only; cable and microphone pair not found.'
finally:
    for probe in probes:
        probe.stop_input()
        actors.destroy_actor(probe)
Path('C:/Work/PJ2DMX/P01Base/Saved/p03-input-readiness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.log('PJ_P03_INPUT_PROBE_DONE '+str(result))
