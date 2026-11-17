#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Blueprint/UserWidget.h"
#include "PJCrowdInputActor.generated.h"

class UProgressBar;
class UTextBlock;

UENUM(BlueprintType)
enum class EPJCrowdInputMode : uint8 { TestSteps, WavFile };

UCLASS()
class PJLIVEDMX_API UPJCrowdMeterWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void UpdateDisplay(float Level, float RMS, const FString& Status);
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    UPROPERTY(Transient) TObjectPtr<UProgressBar> Bar;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusText;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ValueText;
};

UCLASS(Blueprintable)
class PJLIVEDMX_API APJCrowdInputActor : public AActor
{
    GENERATED_BODY()
public:
    APJCrowdInputActor();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Crowd Input") EPJCrowdInputMode InputMode = EPJCrowdInputMode::TestSteps;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Crowd Input", meta=(ToolTip="PCM16 WAV, maximum 256 MiB. Absolute path or relative to the project directory. Analysis only, no speaker output.")) FString WaveFile;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Crowd Input") bool bLoopFile = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Crowd Input") bool bAutoStart = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Meter") bool bShowMeter = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Meter", meta=(ClampMin="0")) float Gain = 3.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Meter", meta=(ClampMin="0",ClampMax="1")) float NoiseFloor = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Meter", meta=(ClampMin="0.001")) float AttackSeconds = 0.05f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Meter", meta=(ClampMin="0.001")) float ReleaseSeconds = 0.2f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Monitor") float RawRMS = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Monitor") float CrowdLevel = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Monitor") float PlaybackSeconds = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Monitor") float DurationSeconds = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Monitor") FString InputStatus = TEXT("Stopped - raw audience level, no separation");
    UFUNCTION(BlueprintCallable, CallInEditor, Category="Crowd Input") void StartInput();
    UFUNCTION(BlueprintCallable, CallInEditor, Category="Crowd Input") void StopInput();
    UFUNCTION(BlueprintCallable, Category="Crowd Input") void AdvanceMeasurement(float DeltaSeconds);
    virtual void Tick(float DeltaSeconds) override;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    bool LoadWave();
    void UpdateMeter();
    bool bRunning = false;
    EPJCrowdInputMode ActiveMode = EPJCrowdInputMode::TestSteps;
    TArray<float> WaveLevels;
    float WindowSeconds = 0.02f;
    UPROPERTY(Transient) TObjectPtr<UPJCrowdMeterWidget> Meter;
};
