; Time of day: four presets (dawn, day, dusk, night). Each has a tint for the whole
; picture and a fog colour (alpha = fog strength). The world is unlit, so the presets
; drive the ink post-process through the MPC_Splice material parameters.
(event `Apply`
  (params (Index :type Integer))
  (if (== Index 0)
    (`self.SetLook` (`self.DawnTint`) (`self.DawnFog`))
    (elif (== Index 1)
      (`self.SetLook` (`self.DayTint`) (`self.DayFog`))
      (elif (== Index 2)
        (`self.SetLook` (`self.DuskTint`) (`self.DuskFog`))
        (else
          (`self.SetLook` (`self.NightTint`) (`self.NightFog`)))))))

(event `SetLook`
  (params (Tint :type "LinearColor Structure") (Fog :type "LinearColor Structure"))
  (`KismetMaterialLibrary.SetVectorParameterValue`
    :`Collection` "/Game/Splice/Materials/MPC_Splice.MPC_Splice" :`ParameterName` "Tint" :`ParameterValue` Tint)
  (`KismetMaterialLibrary.SetVectorParameterValue`
    :`Collection` "/Game/Splice/Materials/MPC_Splice.MPC_Splice" :`ParameterName` "Fog" :`ParameterValue` Fog))
