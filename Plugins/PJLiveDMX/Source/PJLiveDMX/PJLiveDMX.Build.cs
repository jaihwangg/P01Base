using UnrealBuildTool;
public class PJLiveDMX : ModuleRules
{
    public PJLiveDMX(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "AudioCaptureCore", "DMXRuntime", "DMXProtocol", "MediaAssets" });
    }
}
