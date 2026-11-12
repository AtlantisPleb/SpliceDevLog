; Splice game state: inventory, edit bay slots, film strip, HUD and screens.
(event `self.ReceiveBeginPlay`
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (`Actor.EnableInput` self pc)
  (bind hud (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_HUD.WBP_HUD_C" :`OwningPlayer` pc))
  (set `self.HUD` hud)
  (`UserWidget.AddToViewport` :`self` hud)
  (`self.RefreshHUD`)
  (`self.ShowMessage` "Find the Digger's parts in the scrap room."))

; E opens or closes the edit bay when the player is at the rover.
(event `Key|E`
  (params (Key))
  (:`Pressed` (`self.ToggleEditBay`))
  (:`Released`))

; TAB does the same (the key on Kiki's UI board). E stays as a second key in case a
; browser takes TAB for itself.
(event `Key|Tab`
  (params (Key))
  (:`Pressed` (`self.ToggleEditBay`))
  (:`Released`))

(event `ToggleEditBay`
  (if (`self.BayOpen`)
    (`self.CloseEditBay`)
    (else
      (if (`self.NearRover`)
        (`self.OpenEditBay`)))))

(event `OpenEditBay`
  (if (`self.BotRunning`)
    (return))
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (bind bay (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_EditBay.WBP_EditBay_C" :`OwningPlayer` pc))
  (set `self.EditBay` bay)
  (`UserWidget.AddToViewport` :`self` bay)
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnArm` bay) (`|CreateDelegate` :!event `ClickArm`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnTreads` bay) (`|CreateDelegate` :!event `ClickTreads`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnBattery` bay) (`|CreateDelegate` :!event `ClickBattery`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnMove` bay) (`|CreateDelegate` :!event `ClickMove`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnDrill` bay) (`|CreateDelegate` :!event `ClickDrill`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnClear` bay) (`|CreateDelegate` :!event `ClearStrip`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnDeploy` bay) (`|CreateDelegate` :!event `Deploy`))
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_EditBay.BtnClose` bay) (`|CreateDelegate` :!event `CloseEditBay`))
  (set `PlayerController.bShowMouseCursor` :`self` pc :`bShowMouseCursor` true)
  (`WidgetBlueprintLibrary.SetInputMode_GameAndUIEx` :`PlayerController` pc)
  (set `self.BayOpen` true)
  (`self.RefreshEditBay`)
  (`self.RefreshHUD`))

(event `CloseEditBay`
  (bind bay (`self.EditBay`))
  (if (`KismetSystemLibrary.IsValid` bay)
    (`Widget.RemoveFromParent` bay))
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (set `PlayerController.bShowMouseCursor` :`self` pc :`bShowMouseCursor` false)
  (`WidgetBlueprintLibrary.SetInputMode_GameOnly` pc)
  (set `self.BayOpen` false)
  (`self.RefreshHUD`))

(event `ClickArm` (`self.PlaceItem` "Drill Arm"))
(event `ClickTreads` (`self.PlaceItem` "Treads"))
(event `ClickBattery` (`self.PlaceItem` "Battery"))
(event `ClickMove` (`self.PlaceItem` "MOVE"))
(event `ClickDrill` (`self.PlaceItem` "DRILL"))

; Pickups add to the inventory.
(event `PickUp`
  (params (Item :type String))
  (`KismetArrayLibrary.Array_AddUnique` (`self.Inventory`) Item)
  (`self.ShowMessage` (`KismetStringLibrary.Concat_StrStr` "Picked up: " Item))
  (`self.RefreshHUD`))

; Hardware fills its matching slot. Cards go into the next empty strip slot.
(event `PlaceItem`
  (params (Item :type String))
  (if (not (`KismetArrayLibrary.Array_Contains` (`self.Inventory`) Item))
    (return))
  (if (== Item "Drill Arm")
    (set `self.SlotArm` Item)
    (elif (== Item "Treads")
      (set `self.SlotTreads` Item)
      (elif (== Item "Battery")
        (set `self.SlotBattery` Item)
        (else
          (if (< (`KismetArrayLibrary.Array_Length` (`self.Strip`)) 2)
            (`KismetArrayLibrary.Array_Add` (`self.Strip`) Item))))))
  (`self.RefreshEditBay`))

(event `ClearStrip`
  (`KismetArrayLibrary.Array_Clear` (`self.Strip`))
  (`self.RefreshEditBay`))

; DEPLOY works only when all 3 hardware slots and both strip slots are full.
(event `Deploy`
  (if (not (and
             (not (`KismetStringLibrary.IsEmpty` (`self.SlotArm`)))
             (not (`KismetStringLibrary.IsEmpty` (`self.SlotTreads`)))
             (not (`KismetStringLibrary.IsEmpty` (`self.SlotBattery`)))
             (== (`KismetArrayLibrary.Array_Length` (`self.Strip`)) 2)))
    (return))
  (`self.CloseEditBay`)
  (bind bot (`|SpawnActorFromClass`
    :`Class` "/Game/Splice/Blueprints/BP_Bot.BP_Bot_C"
    :`SpawnTransform` (`Actor.GetTransform` (`self.BotSpawn`))
    :`CollisionHandlingOverride` "AlwaysSpawn"))
  (set `self.Bot` bot)
  (set `self.BotRunning` true)
  (set `/Game/Splice/Blueprints/BP_Bot.Cards` :`self` bot :`Cards` (`self.Strip`))
  (set `/Game/Splice/Blueprints/BP_Bot.Game` :`self` bot :`Game` self)
  (`/Game/Splice/Blueprints/BP_Bot.Run` bot)
  (`self.ShowMessage` "Deploying the Digger...")
  (`self.RefreshHUD`))

(event `BotFinished`
  (params (Success :type Boolean))
  (set `self.BotRunning` false)
  (if Success
    (`self.ShowMessage` "Scene cut clean. The tunnel is open!")
    (else
      (`self.ShowMessage` "Bad cut. Re-edit at the rover.")))
  (`self.RefreshHUD`))

(event `ShowMessage`
  (params (Msg :type String))
  (bind msgText (`/Game/Splice/UI/WBP_HUD.MessageText` (`self.HUD`)))
  (`TextBlock.SetText` msgText (`KismetTextLibrary.Conv_StringToText` Msg))
  (`KismetSystemLibrary.Delay` 3.5)
  (`TextBlock.SetText` msgText ""))

(event `SetNearRover`
  (params (Near :type Boolean))
  (set `self.NearRover` Near)
  (`self.RefreshHUD`))

(event `RefreshHUD`
  (bind hud (`self.HUD`))
  (if (not (`KismetSystemLibrary.IsValid` hud))
    (return))
  (bind inv (`self.Inventory`))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_HUD.CarryText` hud)
    (`KismetTextLibrary.Conv_StringToText`
      (`KismetStringLibrary.Concat_StrStr` "Carrying: "
        (select `bool` (== (`KismetArrayLibrary.Array_Length` inv) 0)
          :`true` "nothing"
          :`false` (`KismetStringLibrary.JoinStringArray` inv ", ")))))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_HUD.PromptText` hud)
    (`KismetTextLibrary.Conv_StringToText`
      (select `bool` (and (`self.NearRover`) (not (`self.BayOpen`)) (not (`self.BotRunning`)))
        :`true` "[TAB] or [E]  ·  Open the edit bay"
        :`false` ""))))

(event `RefreshEditBay`
  (bind bay (`self.EditBay`))
  (if (not (`KismetSystemLibrary.IsValid` bay))
    (return))
  (bind inv (`self.Inventory`))
  (bind arm (`self.SlotArm`))
  (bind treads (`self.SlotTreads`))
  (bind battery (`self.SlotBattery`))
  (bind strip (`self.Strip`))
  (bind ready (and
    (not (`KismetStringLibrary.IsEmpty` arm))
    (not (`KismetStringLibrary.IsEmpty` treads))
    (not (`KismetStringLibrary.IsEmpty` battery))
    (== (`KismetArrayLibrary.Array_Length` strip) 2)))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_EditBay.SlotsText` bay)
    (`KismetTextLibrary.Conv_StringToText`
      (`KismetStringLibrary.Concat_StrStr` "ARM: "
        (`KismetStringLibrary.Concat_StrStr` (select `bool` (`KismetStringLibrary.IsEmpty` arm) :`true` "-" :`false` arm)
          (`KismetStringLibrary.Concat_StrStr` "     TREADS: "
            (`KismetStringLibrary.Concat_StrStr` (select `bool` (`KismetStringLibrary.IsEmpty` treads) :`true` "-" :`false` treads)
              (`KismetStringLibrary.Concat_StrStr` "     BATTERY: "
                (select `bool` (`KismetStringLibrary.IsEmpty` battery) :`true` "-" :`false` battery))))))))
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_EditBay.StripText` bay)
    (`KismetTextLibrary.Conv_StringToText`
      (`KismetStringLibrary.Concat_StrStr` "FILM STRIP:  "
        (select `bool` (== (`KismetArrayLibrary.Array_Length` strip) 0)
          :`true` "(empty)  - click MOVE / DRILL in the order the bot should run them"
          :`false` (`KismetStringLibrary.JoinStringArray` strip "  ->  ")))))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnArm` bay) (`KismetArrayLibrary.Array_Contains` inv "Drill Arm"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnTreads` bay) (`KismetArrayLibrary.Array_Contains` inv "Treads"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnBattery` bay) (`KismetArrayLibrary.Array_Contains` inv "Battery"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnMove` bay) (`KismetArrayLibrary.Array_Contains` inv "MOVE"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnDrill` bay) (`KismetArrayLibrary.Array_Contains` inv "DRILL"))
  (`Widget.SetIsEnabled` (`/Game/Splice/UI/WBP_EditBay.BtnDeploy` bay) ready)
  (`TextBlock.SetText` (`/Game/Splice/UI/WBP_EditBay.StatusText` bay)
    (`KismetTextLibrary.Conv_StringToText`
      (select `bool` ready
        :`true` "Ready. Press DEPLOY."
        :`false` "Fill ARM, TREADS and BATTERY, and put 2 cards on the strip."))))

; The exit trigger calls this.
(event `ShowEnd`
  (bind pc (`GameplayStatics.GetPlayerController` 0))
  (bind endw (`|CreateWidget` :`Class` "/Game/Splice/UI/WBP_End.WBP_End_C" :`OwningPlayer` pc))
  (set `self.EndScreen` endw)
  (`UserWidget.AddToViewport` :`self` endw)
  (add `Button.OnClicked` (`/Game/Splice/UI/WBP_End.BtnRestart` endw) (`|CreateDelegate` :!event `ClickRestart`))
  (set `PlayerController.bShowMouseCursor` :`self` pc :`bShowMouseCursor` true)
  (`WidgetBlueprintLibrary.SetInputMode_UIOnlyEx` :`PlayerController` pc))

(event `ClickRestart`
  (`GameplayStatics.OpenLevel` :`LevelName` "L_Mine"))
