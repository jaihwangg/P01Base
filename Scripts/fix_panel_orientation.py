import unreal,json,shutil
from pathlib import Path
root=Path('C:/Work/PJ2DMX/P01Base')
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level('/Game/PJ2DMX/Maps/L_DemoStage2')
panel=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='PJ_RearPanel')
surface=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='PJ_RearPanel_Video')
verts,triangles,normals,uvs,tangents=unreal.ProceduralMeshLibrary.get_section_from_static_mesh(surface.get_editor_property('screen').static_mesh,0,0)
rows=[{'z':unreal.MathLibrary.transform_location(surface.get_actor_transform(),v).z,'u':uv.x,'v':uv.y} for v,uv in zip(verts,uvs)]
assert rows, 'No mesh geometry'
(root/'Saved/orientation-mesh-uv.json').write_text(json.dumps(rows,indent=2))
folder='/Game/PJ2DMX/Media/RearPanel'
tex=unreal.load_asset(folder+'/MT_RearPanel')
def asset(name,cls,factory):
    result=unreal.load_asset(folder+'/'+name)
    assert result
    return result
backup=root/'Saved/M_LEDPanel-before-orientation.uasset'
if not backup.exists():shutil.copy2(root/'Content/PJ2DMX/Media/RearPanel/M_LEDPanel.uasset',backup)
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

assert unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log('PJ_ORIENTATION_MATERIAL_SAVED')
