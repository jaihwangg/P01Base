#include "PJLiveVideoPanelActor.h"
#include "Components/StaticMeshComponent.h"
#include "MediaPlayer.h"
#include "MediaSource.h"
#include "MediaTexture.h"

APJLiveVideoPanelActor::APJLiveVideoPanelActor()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.25f;
    Screen = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Screen"));
    SetRootComponent(Screen);
    Screen->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Screen->SetCastShadow(false);
}

void APJLiveVideoPanelActor::BeginPlay()
{
    Super::BeginPlay();
    if (bAutoOpen) OpenVideo();
}

void APJLiveVideoPanelActor::OpenVideo()
{
    if (!MediaPlayer || !MediaSource || !MediaTexture)
    {
        InputStatus = TEXT("Missing Media Source, Player or Texture");
        return;
    }
    MediaPlayer->Close();
    MediaTexture->SetMediaPlayer(MediaPlayer);
    MediaTexture->UpdateResource();
    MediaPlayer->PlayOnOpen = true;
    InputStatus = MediaPlayer->OpenSource(MediaSource)
        ? TEXT("Opening NDI - waiting for sender") : TEXT("Open failed - check NDI configuration/runtime");
}

void APJLiveVideoPanelActor::CloseVideo()
{
    if (MediaPlayer) MediaPlayer->Close();
    InputStatus = TEXT("Stopped");
}

void APJLiveVideoPanelActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!MediaPlayer) return;
    if (MediaPlayer->HasError()) InputStatus = TEXT("Input error - check sender and reopen");
    else if (MediaPlayer->IsPreparing()) InputStatus = TEXT("Waiting for NDI sender");
    else if (MediaPlayer->IsPlaying()) InputStatus = TEXT("Media player running (check picture for live signal)");
}

void APJLiveVideoPanelActor::EndPlay(const EEndPlayReason::Type Reason)
{
    CloseVideo();
    Super::EndPlay(Reason);
}
