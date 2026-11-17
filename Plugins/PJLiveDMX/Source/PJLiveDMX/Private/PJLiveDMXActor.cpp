#include "PJLiveDMXActor.h"
#include "Library/DMXEntityFixturePatch.h"
#include "Library/DMXEntityFixtureType.h"
#include "Misc/ScopeLock.h"
#include "Game/DMXComponent.h"

APJLiveDMXActor::APJLiveDMXActor()
{
    PrimaryActorTick.bCanEverTick = true;
}
TArray<FString> APJLiveDMXActor::ListInputDevices()
{
    TArray<Audio::FCaptureDeviceInfo> Devices;
    Capture.GetCaptureDevicesAvailable(Devices);
    TArray<FString> Names;
    for (int32 Index=0; Index<Devices.Num(); ++Index)
        Names.Add(FString::Printf(TEXT("%d | %s | %d channels"), Index, *Devices[Index].DeviceName, Devices[Index].InputChannels));
    return Names;
}
void APJLiveDMXActor::BeginPlay()
{
    Super::BeginPlay();
    Patches.Reset();
    for (AActor* Fixture : TargetFixtures)
    {
        if (!IsValid(Fixture)) continue;
        if (UDMXComponent* Component = Fixture->FindComponentByClass<UDMXComponent>())
            if (UDMXEntityFixturePatch* Patch = Component->GetFixturePatch()) Patches.AddUnique(Patch);
    }
    for (UDMXEntityFixturePatch* Patch : Patches)
    {
        if (!IsValid(Patch)) continue;
        auto Defaults = Patch->GetAttributeDefaultMap();
        for (const TCHAR* Name : {TEXT("Red"), TEXT("Green"), TEXT("Blue")})
        {
            FDMXAttributeName Attribute;
            Attribute.Name = Name;
            if (const FDMXFixtureFunction* Function = Patch->GetAttributeFunction(Attribute))
            {
                const double Maximum = FMath::Min(FMath::Pow(2.0, 8*(static_cast<int32>(Function->DataType)+1))-1.0, double(MAX_int32));
                Defaults.Add(Attribute, int32(Maximum));
            }
        }
        Patch->SendDMX(Defaults);
    }
    StartInput();
}
void APJLiveDMXActor::StartInput()
{
    StopInput();
    if (bUseTestSignal)
    {
        InputStatus=TEXT("TEST SIGNAL - 120 BPM");
        return;
    }
    Audio::FCaptureDeviceInfo Info;
    if (!Capture.GetCaptureDeviceInfo(Info, DeviceIndex) || FirstChannel<0 || ChannelCount<1 ||
        FirstChannel>=Info.InputChannels || ChannelCount>Info.InputChannels-FirstChannel)
    {
        InputStatus=TEXT("Input unavailable or channel range invalid");
        UE_LOG(LogTemp, Warning, TEXT("PJLiveDMX: %s"), *InputStatus);
        return;
    }
    Audio::FAudioCaptureDeviceParams Params;
    Params.DeviceIndex=DeviceIndex;
    Params.NumInputChannels=Info.InputChannels;
    const int32 StartChannel=FirstChannel;
    const int32 NumSelected=ChannelCount;
    const bool Opened=Capture.OpenAudioCaptureStream(Params,
        [this,StartChannel,NumSelected](const void* Data,int32 Frames,int32 Channels,int32 Rate,double Time,bool Overflow)
        {
            if (!Data || Frames<=0 || Channels<StartChannel+NumSelected) return;
            const float* Samples=static_cast<const float*>(Data);
            double Sum=0;
            for (int32 Frame=0; Frame<Frames; ++Frame)
                for (int32 Channel=StartChannel; Channel<StartChannel+NumSelected; ++Channel)
                {
                    const float Sample=Samples[Frame*Channels+Channel];
                    if (FMath::IsFinite(Sample)) Sum+=double(Sample)*Sample;
                }
            FScopeLock Lock(&SampleLock);
            CapturedRMS=FMath::Sqrt(Sum/(double(Frames)*NumSelected));
            LastCaptureTime=FPlatformTime::Seconds();
        }, 512);
    if (!Opened || !Capture.StartStream())
    {
        Capture.AbortStream();
        InputStatus=TEXT("Capture could not start");
        return;
    }
    bInputOpen=true;
    InputStatus=Info.DeviceName;
    UE_LOG(LogTemp, Display, TEXT("PJLiveDMX: capturing %s, channels %d..%d"), *InputStatus, FirstChannel, FirstChannel+ChannelCount-1);
}
void APJLiveDMXActor::StopInput()
{
    if (Capture.IsStreamOpen()) Capture.AbortStream();
    bInputOpen=false;
    {
        FScopeLock Lock(&SampleLock);
        CapturedRMS=0;
        LastCaptureTime=0;
    }
    MusicLevel=0;
    ApplyMusicLevel(0);
    InputStatus=TEXT("Stopped");
}
void APJLiveDMXActor::ApplyMusicLevel(float Level)
{
    if (Patches.IsEmpty())
    {
        for (AActor* Fixture : TargetFixtures)
        {
            if (!IsValid(Fixture)) continue;
            if (UDMXComponent* Component = Fixture->FindComponentByClass<UDMXComponent>())
                if (UDMXEntityFixturePatch* Patch = Component->GetFixturePatch()) Patches.AddUnique(Patch);
        }
    }
    for (UDMXEntityFixturePatch* Patch:Patches)
    {
        if (!IsValid(Patch)) continue;
        FDMXAttributeName Attribute;
        Attribute.Name=TEXT("Dimmer");
        const FDMXFixtureFunction* Function=Patch->GetAttributeFunction(Attribute);
        if (!Function) continue;
        const int32 Bits=8*(static_cast<int32>(Function->DataType)+1);
        const double Maximum=FMath::Min(FMath::Pow(2.0,Bits)-1.0,double(MAX_int32));
        TMap<FDMXAttributeName,int32> Values;
        Values.Add(Attribute,int32(FMath::Min(FMath::FloorToDouble(FMath::Clamp(double(Level),0.0,1.0)*Maximum+0.5),double(MAX_int32))));
        Patch->SendDMX(Values);
    }
}
void APJLiveDMXActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    float RMS;
    double Last;
    {
        FScopeLock Lock(&SampleLock);
        RMS=CapturedRMS;
        Last=LastCaptureTime;
    }
    if (bUseTestSignal)
    {
        const double Phase=FMath::Fmod(GetWorld()->GetTimeSeconds(),0.5);
        RMS=0.25f*FMath::Exp(-float(Phase)*12.f);
        Last=FPlatformTime::Seconds();
    }
    const bool Fresh=(bInputOpen || bUseTestSignal) && Last>0 && FPlatformTime::Seconds()-Last<0.5;
    const float Target=Fresh ? FMath::Clamp((RMS-NoiseFloor)*Gain,0.f,1.f) : 0.f;
    const float Seconds=Target>MusicLevel ? AttackSeconds:ReleaseSeconds;
    MusicLevel=Fresh ? FMath::Lerp(MusicLevel,Target,1.f-FMath::Exp(-DeltaSeconds/FMath::Max(Seconds,0.001f))) : 0.f;
    SendElapsed+=DeltaSeconds;
    if (SendElapsed>=1.f/30.f)
    {
        SendElapsed=0;
        ApplyMusicLevel(MusicLevel);
    }
}
void APJLiveDMXActor::EndPlay(const EEndPlayReason::Type Reason)
{
    StopInput();
    Super::EndPlay(Reason);
}

TArray<int32> APJLiveDMXActor::ReadDimmerValues()
{
    TArray<int32> Values;
    FDMXAttributeName Attribute;
    Attribute.Name=TEXT("Dimmer");
    for (UDMXEntityFixturePatch* Patch : Patches)
    {
        if (!IsValid(Patch)) { Values.Add(-1); continue; }
        static_cast<FTickableGameObject*>(Patch)->Tick(0);
        bool Success=false;
        const int32 Value=Patch->GetAttributeValue(Attribute,Success);
        Values.Add(Success ? Value : -1);
    }
    return Values;
}

