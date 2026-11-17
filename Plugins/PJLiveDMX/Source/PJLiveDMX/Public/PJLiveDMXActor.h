#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AudioCaptureCore.h"
#include "HAL/CriticalSection.h"
#include "PJLiveDMXActor.generated.h"
class UDMXEntityFixturePatch;

UCLASS(Blueprintable)
class PJLIVEDMX_API APJLiveDMXActor : public AActor
{
    GENERATED_BODY()
public:
    APJLiveDMXActor();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="DJ Input")
    int32 DeviceIndex = -1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="DJ Input")
    bool bUseTestSignal = true;
    UFUNCTION(BlueprintCallable, Category="Monitor")
    TArray<int32> ReadDimmerValues();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="DJ Input", meta=(ClampMin="0"))
    int32 FirstChannel = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="DJ Input", meta=(ClampMin="1"))
    int32 ChannelCount = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Response", meta=(ClampMin="0"))
    float Gain = 4.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Response", meta=(ClampMin="0",ClampMax="1"))
    float NoiseFloor = 0.01f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Response", meta=(ClampMin="0.001"))
    float AttackSeconds = 0.03f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Response", meta=(ClampMin="0.001"))
    float ReleaseSeconds = 0.2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="DMX")
    TArray<TObjectPtr<AActor>> TargetFixtures;
    UPROPERTY(Transient, BlueprintReadWrite, Category="DMX")
    TArray<TObjectPtr<UDMXEntityFixturePatch>> Patches;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Monitor")
    FString InputStatus;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Monitor")
    float MusicLevel = 0;
    UFUNCTION(BlueprintCallable, Category="DJ Input")
    TArray<FString> ListInputDevices();
    UFUNCTION(BlueprintCallable, Category="DJ Input")
    void StartInput();
    UFUNCTION(BlueprintCallable, Category="DJ Input")
    void StopInput();
    UFUNCTION(BlueprintCallable, Category="DMX")
    void ApplyMusicLevel(float Level);
    virtual void Tick(float DeltaSeconds) override;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    Audio::FAudioCapture Capture;
    FCriticalSection SampleLock;
    float CapturedRMS = 0;
    double LastCaptureTime = 0;
    bool bInputOpen = false;
    float SendElapsed = 0;

};
