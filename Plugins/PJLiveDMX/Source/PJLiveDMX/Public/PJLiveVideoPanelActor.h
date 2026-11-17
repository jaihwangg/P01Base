#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PJLiveVideoPanelActor.generated.h"

class UStaticMeshComponent;
class UMediaSource;
class UMediaPlayer;
class UMediaTexture;

UCLASS(Blueprintable)
class PJLIVEDMX_API APJLiveVideoPanelActor : public AActor
{
    GENERATED_BODY()
public:
    APJLiveVideoPanelActor();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Panel") TObjectPtr<UStaticMeshComponent> Screen;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Live Video") TObjectPtr<UMediaSource> MediaSource;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Live Video") TObjectPtr<UMediaPlayer> MediaPlayer;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Live Video") TObjectPtr<UMediaTexture> MediaTexture;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Live Video") bool bAutoOpen = true;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Live Video") FString InputStatus = TEXT("Stopped - select NDI source, then Open Video");
    UFUNCTION(BlueprintCallable, CallInEditor, Category="Live Video") void OpenVideo();
    UFUNCTION(BlueprintCallable, CallInEditor, Category="Live Video") void CloseVideo();
    virtual void Tick(float DeltaSeconds) override;
    virtual bool ShouldTickIfViewportsOnly() const override { return true; }
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
};
