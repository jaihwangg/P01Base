#include "PJCrowdInputActor.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/ProgressBar.h"
#include "Brushes/SlateColorBrush.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "GameFramework/PlayerController.h"

TSharedRef<SWidget> UPJCrowdMeterWidget::RebuildWidget()
{
    if (!WidgetTree) WidgetTree = NewObject<UWidgetTree>(this, TEXT("WidgetTree"));
    UBorder* Root = WidgetTree->ConstructWidget<UBorder>();
    Root->SetBrushColor(FLinearColor(0.015f,0.025f,0.045f,0.94f));
    Root->SetPadding(FMargin(16));
    UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>();
    Root->SetContent(Box);
    UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>();
    Title->SetText(FText::FromString(TEXT("AUDIENCE INPUT / RAW LEVEL")));
    Title->SetColorAndOpacity(FSlateColor(FLinearColor(0.3f,0.95f,0.8f)));
    FSlateFontInfo Font = Title->GetFont(); Font.Size = 18; Title->SetFont(Font);
    Box->AddChildToVerticalBox(Title);
    StatusText = WidgetTree->ConstructWidget<UTextBlock>();
    Font.Size=13; StatusText->SetFont(Font); StatusText->SetAutoWrapText(true);
    Box->AddChildToVerticalBox(StatusText);
    USizeBox* BarSize = WidgetTree->ConstructWidget<USizeBox>(); BarSize->SetHeightOverride(24);
    Bar = WidgetTree->ConstructWidget<UProgressBar>();
    FProgressBarStyle BarStyle;
    BarStyle.SetBackgroundImage(FSlateColorBrush(FLinearColor(0.04f,0.07f,0.10f)));
    BarStyle.SetFillImage(FSlateColorBrush(FLinearColor::White));
    Bar->SetWidgetStyle(BarStyle);
    Bar->SetBarFillStyle(EProgressBarFillStyle::Scale);
    Bar->SetFillColorAndOpacity(FLinearColor(0.1f,0.8f,0.6f));
    BarSize->SetContent(Bar); Box->AddChildToVerticalBox(BarSize);
    ValueText = WidgetTree->ConstructWidget<UTextBlock>(); ValueText->SetFont(Font);
    Box->AddChildToVerticalBox(ValueText);
    WidgetTree->RootWidget = Root;
    return Super::RebuildWidget();
}

void UPJCrowdMeterWidget::UpdateDisplay(float Level, float RMS, const FString& Status)
{
    if (!Bar || !StatusText || !ValueText) return;
    Bar->SetPercent(Level);
    StatusText->SetText(FText::FromString(Status));
    ValueText->SetText(FText::FromString(FString::Printf(TEXT("Level %.0f%%  |  RMS %.4f\nNo music removal / no scoring / analysis only"),Level*100,RMS)));
}

APJCrowdInputActor::APJCrowdInputActor() { PrimaryActorTick.bCanEverTick = true; }

bool APJCrowdInputActor::LoadWave()
{
    FString Path = WaveFile;
    if (FPaths::IsRelative(Path)) Path = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), Path);
    const int64 Size = IFileManager::Get().FileSize(*Path);
    if (Size<=0 || Size>256ll*1024*1024)
    {
        InputStatus=TEXT("ERROR: select an existing PCM16 WAV (maximum 256 MiB)"); return false;
    }
    TArray<uint8> Bytes;
    if (!FFileHelper::LoadFileToArray(Bytes,*Path)) return false;
    auto U16=[&](int64 P)->uint16 { return uint16(Bytes[P]) | (uint16(Bytes[P+1])<<8); };
    auto U32=[&](int64 P)->uint32 { return uint32(U16(P)) | (uint32(U16(P+2))<<16); };
    auto Tag=[&](int64 P,const char* T) { return FMemory::Memcmp(Bytes.GetData()+P,T,4)==0; };
    InputStatus=TEXT("ERROR: malformed or unsupported PCM16 WAV");
    if (Bytes.Num()<12 || !Tag(0,"RIFF") || !Tag(8,"WAVE")) return false;
    const int64 Limit=int64(U32(4))+8;
    if (Limit<12 || Limit>Bytes.Num()) return false;
    int32 Channels=0,Rate=0; int64 DataOffset=0,DataSize=0;
    bool HasFormat=false;
    for (int64 P=12;P<Limit;)
    {
        if (Limit-P<8) return false;
        const int64 N=U32(P+4), Body=P+8;
        if (N>Limit-Body || N+(N&1)>Limit-Body) return false;
        if (Tag(P,"fmt "))
        {
            if (HasFormat || N<16) return false;
            Channels=U16(Body+2); Rate=U32(Body+4);
            if (U16(Body)!=1 || U16(Body+14)!=16 || Channels<1 || Channels>8 ||
                Rate<8000 || Rate>192000 || U16(Body+12)!=2*Channels ||
                U32(Body+8)!=uint32(Rate*2*Channels)) return false;
            HasFormat=true;
        }
        else if (Tag(P,"data"))
        {
            if (DataOffset) return false;
            DataOffset=Body; DataSize=N;
        }
        P=Body+N+(N&1);
    }
    if (!HasFormat || !DataOffset || DataSize==0 || DataSize%(2*Channels)!=0) return false;
    const int32 Frames=DataSize/(2*Channels);
    const int32 Window=FMath::Max(1,FMath::RoundToInt(Rate*0.02f));
    WindowSeconds=float(Window)/Rate; DurationSeconds=float(Frames)/Rate;
    for (int32 Start=0;Start<Frames;Start+=Window)
    {
        const int32 End=FMath::Min(Start+Window,Frames); double Sum=0;
        for (int32 Frame=Start;Frame<End;++Frame)
            for (int32 Channel=0;Channel<Channels;++Channel)
            {
                int16 Sample; FMemory::Memcpy(&Sample,Bytes.GetData()+DataOffset+2*(Frame*Channels+Channel),2);
                const double Value=double(Sample)/32768.0; Sum+=Value*Value;
            }
        WaveLevels.Add(FMath::Sqrt(Sum/((End-Start)*Channels)));
    }
    InputStatus=TEXT("WAV FILE / ")+FPaths::GetCleanFilename(Path);
    return !WaveLevels.IsEmpty();
}

void APJCrowdInputActor::StartInput()
{
    StopInput(); WaveLevels.Reset(); DurationSeconds=0; ActiveMode=InputMode;
    if (ActiveMode==EPJCrowdInputMode::WavFile) bRunning=LoadWave();
    else { bRunning=true; DurationSeconds=12; InputStatus=TEXT("TEST STEPS / synthetic level (not cheering)"); }
    UpdateMeter();
}

void APJCrowdInputActor::StopInput()
{
    bRunning=false; RawRMS=0; CrowdLevel=0; PlaybackSeconds=0;
    InputStatus=TEXT("STOPPED / raw audience level"); UpdateMeter();
}

void APJCrowdInputActor::AdvanceMeasurement(float DeltaSeconds)
{
    if (!bRunning || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds<0) return;
    PlaybackSeconds+=DeltaSeconds;
    if (ActiveMode==EPJCrowdInputMode::TestSteps)
    {
        constexpr float Levels[]={0.f,0.025f,0.1f,0.2f,0.35f,0.05f};
        PlaybackSeconds=FMath::Fmod(PlaybackSeconds,12.f);
        RawRMS=Levels[FMath::Clamp(int32(PlaybackSeconds/2.f),0,5)];
    }
    else
    {
        if (PlaybackSeconds>=DurationSeconds)
        {
            if (!bLoopFile) { StopInput(); InputStatus=TEXT("END OF WAV / press Start Input to restart"); UpdateMeter(); return; }
            PlaybackSeconds=FMath::Fmod(PlaybackSeconds,DurationSeconds);
        }
        RawRMS=WaveLevels[FMath::Clamp(int32(PlaybackSeconds/WindowSeconds),0,WaveLevels.Num()-1)];
    }
    const float Target=FMath::Clamp((RawRMS-NoiseFloor)*Gain,0.f,1.f);
    const float Seconds=Target>CrowdLevel?AttackSeconds:ReleaseSeconds;
    CrowdLevel=FMath::Lerp(CrowdLevel,Target,1.f-FMath::Exp(-DeltaSeconds/FMath::Max(Seconds,0.001f)));
    UpdateMeter();
}

void APJCrowdInputActor::UpdateMeter() { if (Meter) Meter->UpdateDisplay(CrowdLevel,RawRMS,InputStatus); }
void APJCrowdInputActor::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoStart) StartInput();
}
void APJCrowdInputActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bShowMeter && !Meter)
    {
        if (APlayerController* PC=GetWorld()->GetFirstPlayerController())
        {
            Meter=CreateWidget<UPJCrowdMeterWidget>(PC,UPJCrowdMeterWidget::StaticClass());
            if (Meter) { Meter->AddToViewport(20); Meter->SetPositionInViewport(FVector2D(24,24)); Meter->SetDesiredSizeInViewport(FVector2D(460,160)); }
        }
    }
    if (Meter) Meter->SetVisibility(bShowMeter?ESlateVisibility::HitTestInvisible:ESlateVisibility::Collapsed);
    AdvanceMeasurement(DeltaSeconds); UpdateMeter();
}
void APJCrowdInputActor::EndPlay(const EEndPlayReason::Type Reason)
{
    StopInput(); if (Meter) { Meter->RemoveFromParent(); Meter=nullptr; }
    Super::EndPlay(Reason);
}
