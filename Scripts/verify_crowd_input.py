import unreal,json,math,wave,struct
from pathlib import Path
root=Path('C:/Work/PJ2DMX/P01Base/Saved/P03Tests');root.mkdir(exist_ok=True)
assert hasattr(unreal,'PJCrowdInputActor'), 'P-03 crowd actor not implemented'
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
a=actors.spawn_actor_from_class(unreal.PJCrowdInputActor,unreal.Vector())
def make(name,amplitude):
    path=root/name
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
        f.writeframes(b''.join(struct.pack('<h',round(amplitude*32767*math.sin(2*math.pi*1000*i/48000))) for i in range(48000)))
    return path
try:
    a.set_editor_property('gain',1.0);a.set_editor_property('noise_floor',0.0)
    a.set_editor_property('loop_file',False)
    results=[]
    for amp in (0.,0.25,0.75):
        path=make('level'+str(amp)+'.wav',amp)
        a.set_editor_property('input_mode',unreal.PJCrowdInputMode.WAV_FILE)
        a.set_editor_property('wave_file',str(path));a.start_input();a.advance_measurement(0.1)
        rms=a.get_editor_property('raw_rms')
        assert abs(rms-amp/math.sqrt(2))<0.002,(amp,rms)
        results.append({'amplitude':amp,'rms':rms})
    a.advance_measurement(2.0)
    assert a.get_editor_property('raw_rms')==0 and a.get_editor_property('crowd_level')==0
    a.set_editor_property('loop_file',True);a.start_input();a.advance_measurement(2.1)
    assert a.get_editor_property('raw_rms')>0.5
    a.stop_input();a.advance_measurement(0.1)
    assert a.get_editor_property('crowd_level')==0
    a.set_editor_property('wave_file',str(root/'missing.wav'));a.start_input()
    assert 'ERROR' in a.get_editor_property('input_status') and a.get_editor_property('raw_rms')==0
    bad=root/'bad.wav';bad.write_bytes(b'not a WAV')
    a.set_editor_property('wave_file',str(bad));a.start_input()
    assert 'ERROR' in a.get_editor_property('input_status')
    good=bytearray(make('valid.wav',0.25).read_bytes())
    cases={'short_header':b'RIFF', 'truncated_fmt':bytes(good[:25]),
           'oversized_data':bytes(good[:-2])}
    incomplete=bytearray(good[:-1]);struct.pack_into('<I',incomplete,4,len(incomplete)-8)
    struct.pack_into('<I',incomplete,40,len(incomplete)-44)
    cases['incomplete_frame']=bytes(incomplete)
    for name,data in cases.items():
        invalid=root/(name+'.wav');invalid.write_bytes(data)
        a.set_editor_property('wave_file',str(invalid));a.start_input()
        assert 'ERROR' in a.get_editor_property('input_status'),name
        assert a.get_editor_property('raw_rms')==0 and a.get_editor_property('crowd_level')==0
    a.set_editor_property('input_mode',unreal.PJCrowdInputMode.TEST_STEPS);a.start_input()
    a.advance_measurement(0.1);low=a.get_editor_property('raw_rms')
    a.advance_measurement(6.0);high=a.get_editor_property('raw_rms')
    assert low==0 and high>0.1
    a.stop_input();assert a.get_editor_property('crowd_level')==0
    (root/'results.json').write_text(json.dumps({'result':'PASS','wav_levels':results,'end_stop_missing_invalid_loop_steps':'PASS'},indent=2))
    unreal.log('PJ_CROWD_TEST_PASS')
finally:
    a.stop_input();actors.destroy_actor(a)
