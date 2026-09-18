extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	# This test drives real ads and real endings, both of which write the
	# player's saved progress. Without the guard it overwrites their shift
	# counters and selected night for good.
	ProgressGuard.snapshot()
	var failures: Array[String] = []
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game := packed.instantiate()
	root.add_child(game)
	for _frame in 6:
		await process_frame

	var platform := game.get_node_or_null("YandexSDK")
	var controls := game.get_node_or_null("MobileControls")
	var hud := game.get_node_or_null("HUD")
	var player := game.get_node_or_null("Player")
	var audio := game.get_node_or_null("AudioManager")
	if not platform or not platform.is_in_group("yandex_sdk"):
		failures.append("sdk_node")
	if not controls or not controls.is_in_group("mobile_controls"):
		failures.append("mobile_controls_node")
	if audio and audio.player and audio.player.playback_type != AudioServer.PLAYBACK_TYPE_STREAM:
		failures.append("web_audio_not_stream")
	if platform:
		# v1 saves had no per-night result payload. Migration must retain the
		# old completion/language fields and add an empty, safe result map.
		var migrated: Dictionary = platform._normalized_progress({
			"version": 1, "selected_night": 4, "completed_nights": [0, 4],
			"shifts_finished": 3, "successful_shifts": 2, "language": "ru"
		})
		if migrated.get("selected_night") != 4 or migrated.get("results_by_night", null) != {}:
			failures.append("progress_v1_migration")
		platform.progress = platform._default_progress()
		platform.record_shift_result(4, "dawn", true, {
			"task_count": 8, "task_total": 8, "medical_errors": 0,
			"patient_outcomes": {"saveliev": {"outcome": "transfusion"}}
		})
		var saved_result: Variant = platform.progress.get("results_by_night", {}).get("night_5", {})
		if not saved_result is Dictionary or int(saved_result.get("task_count", 0)) != 8 \
			or String(saved_result.get("ending", "")) != "dawn":
			failures.append("progress_result_recording")
		var merged: Dictionary = platform._merge_results_by_night(
			{"night_5": {"recorded_at": 10, "ending": "unfinished_shift"}},
			{"night_5": {"recorded_at": 11, "ending": "dawn"}, "night_6": {"ending": "dawn"}}, 10, 11)
		if String(merged.get("night_5", {}).get("ending", "")) != "dawn" or not merged.has("night_6"):
			failures.append("progress_result_cloud_merge")
		platform.progress["language"] = "ru"
		platform.progress["updated_at"] = 10
		platform._merge_cloud_progress(JSON.stringify({
			"version": 2, "language": "en", "updated_at": 11,
			"selected_night": 1, "results_by_night": {}
		}))
		if String(platform.progress.get("language", "")) != "en":
			failures.append("progress_language_cloud_merge")

	if controls and hud and player:
		controls.set_mobile_enabled_for_test(true)
		game.get_node("HospitalState").shift_started = true
		hud.start_panel.visible = false
		controls._refresh_visibility()
		if not controls.interact_button.visible or not controls.pause_button.visible:
			failures.append("mobile_buttons_hidden")
		if controls.interact_button.size.y < 80.0 or controls.joystick_base.size.x < 170.0:
			failures.append("mobile_touch_targets_too_small")
		controls.joystick_origin = Vector2(128.0, 592.0)
		controls._update_stick(controls.joystick_origin + Vector2(88.0, 0.0))
		if controls.movement_vector.x < 0.95:
			failures.append("joystick_vector")
		var old_rotation: float = player.rotation.y
		player.apply_touch_look_delta(Vector2(25.0, 0.0), 0.0042)
		if is_equal_approx(old_rotation, player.rotation.y):
			failures.append("touch_look")
		var flashlight_before: bool = player.flashlight.visible
		player.mobile_toggle_flashlight()
		if player.flashlight.visible == flashlight_before:
			failures.append("touch_flashlight")

	# --- touch controls ------------------------------------------------------
	if controls and hud and player:
		# Dead zone: a thumb resting on the stick must not walk the player.
		controls.joystick_origin = Vector2(128.0, 592.0)
		controls._update_stick(controls.joystick_origin + Vector2(9.0, 0.0))
		if controls.movement_vector != Vector2.ZERO:
			failures.append("stick_dead_zone_ignored")
		# ...and full tilt must still mean full speed.
		controls._update_stick(controls.joystick_origin + Vector2(140.0, 0.0))
		if controls.movement_vector.x < 0.98:
			failures.append("stick_full_tilt_%f" % controls.movement_vector.x)
		controls._release_move_touch()

		# ...and the tilt has to survive the trip into the player. Everything
		# above measures the STICK; this measures the WALK. player.gd normalised
		# the direction and threw the magnitude away, so half a tilt and a full
		# tilt both walked at 3.15 m/s and the whole analogue curve above was
		# decoration. Drive real physics frames and compare the two speeds.
		var frozen_before: bool = not player.can_move
		var where_before: Vector3 = player.global_position
		var facing_before: float = player.rotation.y
		player.set_frozen(false)
		var speeds: Array[float] = []
		for tilt in [0.45, 1.0]:
			# where_before, not safe_spawn: the player has already settled onto
			# the floor here, so neither run starts with a drop that the
			# below-the-world guard would turn into a velocity reset.
			player.global_position = where_before
			player.rotation.y = facing_before
			player.velocity = Vector3.ZERO
			controls.movement_vector = Vector2(0.0, -tilt)
			var peak := 0.0
			# walk_speed / acceleration = 0.225 s to saturate; 24 ticks is 0.4 s
			# at the 60 Hz physics step, enough for both tilts to settle.
			for _frame in 24:
				await physics_frame
				peak = maxf(peak, Vector2(player.velocity.x, player.velocity.z).length())
			speeds.append(peak)
		controls.movement_vector = Vector2.ZERO
		player.global_position = where_before
		player.rotation.y = facing_before
		player.velocity = Vector3.ZERO
		player.set_frozen(frozen_before)
		if speeds[1] < player.walk_speed * 0.9:
			failures.append("full_tilt_does_not_reach_walk_speed_%f" % speeds[1])
		if speeds[0] > speeds[1] * 0.75:
			failures.append("stick_tilt_ignored_by_player_%f_vs_%f" % [speeds[0], speeds[1]])

		# Button captions must follow the language in both directions. They used
		# to bake tr() at build time, which stuck them in whichever language the
		# scene happened to load in.
		var before_ru: String = controls.interact_button.atr(controls.interact_button.text)
		TranslationServer.set_locale("en")
		var in_english: String = controls.interact_button.atr(controls.interact_button.text)
		TranslationServer.set_locale("ru")
		var back_to_ru: String = controls.interact_button.atr(controls.interact_button.text)
		if in_english == before_ru:
			failures.append("mobile_button_not_translated")
		if back_to_ru != before_ru:
			failures.append("mobile_button_stuck_in_english_%s" % back_to_ru)

		# A tap on the look half means "use what I am aiming at"; a drag is a
		# look, not a use. Aimed at the ward journal, the tap has to tick its
		# task and the drag has to leave it alone.
		var state := game.get_node("HospitalState")
		state.reset_shift()
		var journal := get_first_node_in_group("documents") as Node3D
		if not journal:
			failures.append("no_journal_for_tap_test")
		elif await _aim_player_at(player, journal):
			var tap_point := Vector2(960.0, 360.0)
			state.tasks["journal_checked"] = false
			controls._input(_touch(tap_point, true, 1))
			controls._input(_drag(tap_point + Vector2(120.0, 0.0), Vector2(120.0, 0.0), 1))
			controls._input(_touch(tap_point + Vector2(120.0, 0.0), false, 1))
			if state.tasks.get("journal_checked", false):
				failures.append("drag_counted_as_tap")
			controls._input(_touch(tap_point, true, 1))
			controls._input(_touch(tap_point, false, 1))
			if not state.tasks.get("journal_checked", false):
				failures.append("tap_did_not_interact")
			hud.close_document()

			# The action button dims when there is nothing to use. It mirrors the
			# player's own prompt, so this only works while that prompt is
			# actually cleared when the ray hits nothing - assert both states.
			# Wait on PHYSICS frames, not idle ones: the prompt is refreshed in
			# the player's _physics_process, and the ray is a child node whose
			# query resolves after it, so the prompt trails the ray by a tick.
			# Headless idle frames run far faster than the physics step, so
			# awaiting process_frame could step physics zero times and leave the
			# journal's prompt standing - the button then read "lit" over
			# nothing, at about one run in three.
			for _frame in 8:
				await physics_frame
			controls._refresh_interact_hint()
			if controls.interact_button.modulate.a < 0.9:
				failures.append("interact_hint_dim_on_target")
			player.rotation.y += PI
			player.head.rotation = Vector3.ZERO
			for _frame in 8:
				await physics_frame
			controls._refresh_interact_hint()
			if controls.interact_button.modulate.a > 0.6:
				failures.append("interact_hint_stayed_lit_on_nothing")
		else:
			failures.append("could_not_aim_at_journal")

	# --- interstitials -------------------------------------------------------
	# Every one of these paths ends with the game waiting on the ad callback to
	# reveal an ending or start a night, so a dropped callback is a dead screen,
	# not a missing ad. Each case below dropped it before this suite existed.
	if platform:
		var delivered: Array[String] = []
		platform.show_interstitial(func(): delivered.append("first"))
		await process_frame
		await process_frame
		if not "first" in delivered:
			failures.append("ad_callback_never_ran")

		# ...requested again while one is already up.
		platform._ad_pending = true
		platform.show_interstitial(func(): delivered.append("while_pending"))
		await process_frame
		await process_frame
		if not "while_pending" in delivered:
			failures.append("ad_callback_dropped_when_pending")
		platform._ad_pending = false

		# ...refused by our own cooldown (Yandex allows one a minute).
		platform._last_ad_msec = Time.get_ticks_msec()
		platform.show_interstitial(func(): delivered.append("cooldown"))
		await process_frame
		await process_frame
		if not "cooldown" in delivered:
			failures.append("ad_callback_dropped_by_cooldown")
		platform._last_ad_msec = -1

		# ...and the platform never reporting the ad closed at all.
		platform._ad_pending = true
		platform._after_interstitial = func(): delivered.append("watchdog")
		platform._on_ad_watchdog(platform._ad_token)
		if not "watchdog" in delivered:
			failures.append("ad_watchdog_did_not_release")

	# A lost shift shows the ad and then the ending panel. If the panel never
	# appears the player is stuck looking at the frozen ward.
	if hud and platform:
		platform._last_ad_msec = -1
		hud.ending_panel.visible = false
		game.get_node("HospitalState").request_ending("killed_by_patient")
		for _frame in 4:
			await process_frame
		if not hud.ending_panel.visible:
			failures.append("loss_ad_swallowed_the_ending")
		hud.ending_panel.visible = false
		# show_ending() pauses the tree; the checks below need it running again.
		paused = false

	# ...and the same for the ad between nights: the shift has to actually start.
	if hud and platform:
		platform._last_ad_msec = -1
		platform.progress["shifts_finished"] = 1
		hud.loading_complete = true
		hud.start_panel.visible = true
		hud._start_pressed()
		for _frame in 4:
			await process_frame
		var director := game.get_node("GameDirector")
		if not director.started:
			failures.append("level_ad_swallowed_the_start")
		if hud.start_button.disabled:
			failures.append("start_button_left_disabled")

	# The custom HTML shell is a build-time template: the exporter folds it into
	# index.html and does not ship the source. So it can only be checked when
	# this runs against the project. From inside an exported pack the equivalent
	# check lives in tools/build/pack_yandex_zip.py, which reads the produced
	# index.html. project.godot becomes project.binary in a pack, which is how
	# the two cases are told apart.
	var running_from_project := FileAccess.file_exists("res://project.godot")
	var shell := FileAccess.open("res://web/yandex_shell.html", FileAccess.READ)
	if not shell:
		if running_from_project:
			failures.append("shell_missing")
		else:
			print("YANDEX_INTEGRATION shell check skipped (exported pack)")
	else:
		var html := shell.get_as_text()
		for required in [
			"src=\"/sdk.js\"", "YaGames.init()", "LoadingAPI?.ready()",
			"GameplayAPI?.start()", "game_api_pause", "showFullscreenAdv",
			"player.getData", "player.setData", "contextmenu",
			"orientation: portrait", "mobile-device", "rotate-notice"]:
			if not required in html:
				failures.append("shell:" + required)

	print("YANDEX_INTEGRATION sdk=", platform != null,
		" mobile_controls=", controls != null, " failures=", failures.size())
	if not failures.is_empty():
		print("YANDEX_FAILURES ", failures)
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)


# --- touch event helpers ------------------------------------------------------
# The controls read raw touch events, so the only honest way to test them is to
# feed them raw touch events rather than calling the handlers they end up in.

func _touch(position: Vector2, pressed: bool, index: int) -> InputEventScreenTouch:
	var event := InputEventScreenTouch.new()
	event.position = position
	event.pressed = pressed
	event.index = index
	return event


func _drag(position: Vector2, relative: Vector2, index: int) -> InputEventScreenDrag:
	var event := InputEventScreenDrag.new()
	event.position = position
	event.relative = relative
	event.index = index
	return event


func _aim_player_at(player: Node, target: Node3D) -> bool:
	# Same search validate_level_reach.gd uses: stand on whichever side the
	# interaction ray actually resolves to the target.
	var centre: Vector3 = target.global_position
	for direction in [Vector3.FORWARD, Vector3.BACK, Vector3.LEFT, Vector3.RIGHT]:
		for distance in [1.0, 1.5]:
			var stand: Vector3 = centre + direction * distance
			var eye_offset: float = player.camera.global_position.y - player.global_position.y
			player.global_position = Vector3(stand.x, 1.62 - eye_offset, stand.z)
			player.rotation = Vector3.ZERO
			player.head.rotation = Vector3.ZERO
			player.camera.look_at(centre, Vector3.UP)
			await process_frame
			player.ray.force_raycast_update()
			if player._find_interactable() == target:
				return true
	return false
