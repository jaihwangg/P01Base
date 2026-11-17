import unreal, json, shutil, socket
from pathlib import Path
root=Path('C:/Work/PJ2DMX/P01Base')
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
all_actors=list(actors.get_all_level_actors())
panel=next(a for a in all_actors if a.get_actor_label()=='PJ_RearPanel')
existing_surface=next((a for a in all_actors if a.get_actor_label()=='PJ_RearPanel_Video'),None)
backup=root/'Saved/L_DemoStage2-before-live-video.umap'
if not backup.exists(): shutil.copy2(root/'Content/PJ2DMX/Maps/L_DemoStage2.umap',backup)
before={a.get_name():str(a.get_actor_transform()) for a in all_actors}
tools=unreal.AssetToolsHelpers.get_asset_tools()
folder='/Game/PJ2DMX/Media/RearPanel'
unreal.EditorAssetLibrary.make_directory(folder)
def asset(name,cls,factory):
    return unreal.load_asset(folder+'/'+name) or tools.create_asset(name,folder,cls,factory)
player=asset('MP_RearPanel',unreal.MediaPlayer,unreal.MediaPlayerFactoryNew())
player.set_editor_property('play_on_open',True)
tex=asset('MT_RearPanel',unreal.MediaTexture,unreal.MediaTextureFactoryNew())
tex.set_media_player(player)
tex.set_editor_property('auto_clear',True)
tex.set_editor_property('clear_color',unreal.LinearColor(0,0,0,1))
source=asset('NDI_RearPanel',unreal.NDIMediaSource,unreal.NDIMediaSourceFactory())
config=source.get_editor_property('media_configuration')
conn=config.get_editor_property('media_connection')
device=conn.get_editor_property('device')
device.set_editor_property('device_name',socket.gethostname()+' (PJ2DMX Test)')
device.set_editor_property('device_identifier',0)
conn.set_editor_property('device',device)
conn.set_editor_property('protocol','ndi')
conn.set_editor_property('port_identifier',0)
assert str(config.get_editor_property('media_connection').get_editor_property('device').get_editor_property('device_name')) == socket.gethostname()+' (PJ2DMX Test)'
source.set_editor_property('media_configuration',config)
# bAutoDetectInput defaults to true (not reflected).
source.set_editor_property('capture_audio',False)
source.set_editor_property('capture_video',True)
source.set_editor_property('render_jit',False)
mat=asset('M_LEDPanel',unreal.Material,unreal.MaterialFactoryNew())
lib=unreal.MaterialEditingLibrary
lib.delete_all_material_expressions(mat)
mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property('two_sided',True)
def node(cls,x,y): return lib.create_material_expression(mat,cls,x,y)
uv=node(unreal.MaterialExpressionTextureCoordinate,-800,0)
sample=node(unreal.MaterialExpressionTextureSampleParameter2D,-500,-250)
sample.set_editor_property('parameter_name','VideoTexture')
sample.set_editor_property('texture',tex)
sample.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
# This upright Plane presents V=0 at its bottom edge. Flip only video sampling.
video_uv=node(unreal.MaterialExpressionCustom,-650,-450)
video_uv.set_editor_property('description','RearPanel upright video UV')
video_uv.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT2)
video_uv.set_editor_property('code','return float2(UV.x, 1.0 - UV.y);')
video_input=unreal.CustomInput(); video_input.set_editor_property('input_name','UV')
video_uv.set_editor_property('inputs',[video_input])
lib.connect_material_expressions(uv,'',video_uv,'UV')
lib.connect_material_expressions(video_uv,'',sample,'UVs')
custom=node(unreal.MaterialExpressionCustom,-200,100)
custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
custom.set_editor_property('code','''
float2 cells = max(float2(Columns, Rows), 1.0);
float2 grid = UV * cells;
float radius = clamp(DotSize, 0.05, 0.98) * 0.5;
float dist = length(frac(grid) - 0.5);
float footprint = max(length(ddx(grid)), length(ddy(grid)));
float aa = max(footprint * 0.5, 0.001);
float dot = 1.0 - smoothstep(radius-aa, radius+aa, dist);
// Average the subpixel pattern to reduce distant shimmer.
dot = lerp(dot, 3.14159265*radius*radius, smoothstep(0.65,1.5,footprint));
return lerp(1.0, dot, saturate(DotStrength)) * max(Brightness,0.0);
''')
inputs=[]
names=['UV','Columns','Rows','DotSize','DotStrength','Brightness']
for name in names:
    i=unreal.CustomInput(); i.set_editor_property('input_name',name); inputs.append(i)
custom.set_editor_property('inputs',inputs)
lib.connect_material_expressions(uv,'',custom,'UV')
scale=panel.get_actor_scale3d()
defaults={'Columns':320.,'Rows':max(1.,round(320*abs(scale.z/scale.x))),'DotSize':0.72,'DotStrength':1.,'Brightness':2.}
for index,(name,value) in enumerate(defaults.items()):
    p=node(unreal.MaterialExpressionScalarParameter,-600,150+index*150)
    p.set_editor_property('parameter_name',name); p.set_editor_property('default_value',value)
    lib.connect_material_expressions(p,'',custom,name)
mul=node(unreal.MaterialExpressionMultiply,100,0)
lib.connect_material_expressions(sample,'RGB',mul,'A')
lib.connect_material_expressions(custom,'',mul,'B')
lib.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
lib.recompile_material(mat)
mi=asset('MI_RearPanel_LED',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
lib.set_material_instance_parent(mi,mat)
for name,value in defaults.items(): lib.set_material_instance_scalar_parameter_value(mi,name,value)
surface=existing_surface or actors.spawn_actor_from_class(unreal.PJLiveVideoPanelActor,unreal.Vector())
surface.set_actor_label('PJ_RearPanel_Video')
surface.set_folder_path('Stage/Panel')
surface.attach_to_actor(panel,'',unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,unreal.AttachmentRule.KEEP_RELATIVE,False)
surface.set_actor_relative_location(unreal.Vector(0,51,0),False,False)
surface.set_actor_relative_rotation(unreal.Rotator(pitch=0,yaw=0,roll=-90),False,False)
# FTransform composes scale component-wise; compensate the rotated plane's Y/Z axes.
surface.set_actor_relative_scale3d(unreal.Vector(1,abs(scale.z/scale.y),abs(scale.y/scale.z)))
screen=surface.get_editor_property('screen')
screen.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'))
screen.set_material(0,mi)
surface.set_editor_property('media_source',source)
surface.set_editor_property('media_player',player)
surface.set_editor_property('media_texture',tex)
for a in (player,tex,source,mat,mi): assert unreal.EditorAssetLibrary.save_loaded_asset(a)
assert all(str(a.get_actor_transform())==before[a.get_name()] for a in all_actors if a!=surface)
assert level.save_current_level()
(root/'Saved/live-video-setup.json').write_text(json.dumps({'original_actors':len(all_actors),'panel_transform':str(panel.get_actor_transform()),'parameters':defaults,'source':source.get_url(),'backup':str(backup)},indent=2))
unreal.log('PJ_VIDEO_SETUP_PASS')




