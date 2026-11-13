import sys
from uemcp import py
prop, val = sys.argv[1], sys.argv[2]
print(py(f'''
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
r = "none"
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PP_Mine":
        st = a.settings
        if "{prop}" == "dump":
            r = str([(p, st.get_editor_property(p)) for p in ("bloom_dirt_mask_intensity","bloom_dirt_mask","lens_flare_intensity","vignette_intensity","film_grain_intensity","local_exposure_method","bloom_method","bloom_intensity","override_bloom_dirt_mask_intensity","override_vignette_intensity","auto_exposure_bias")])
            r += str(len(st.get_editor_property("weighted_blendables").get_editor_property("array")))
        elif "{prop}" == "blend":
            arr = st.get_editor_property("weighted_blendables"); a2 = arr.get_editor_property("array")
            for w in a2: w.set_editor_property("weight", {val})
            arr.set_editor_property("array", a2); st.set_editor_property("weighted_blendables", arr); a.set_editor_property("settings", st); r="blend set"
        else:
            st.set_editor_property("override_{prop}", True); st.set_editor_property("{prop}", {val}); a.set_editor_property("settings", st); r = "set"
r
'''))
