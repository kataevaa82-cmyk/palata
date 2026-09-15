extends Node

signal sdk_initialized(available: bool)
signal progress_changed
signal language_detected(language: String)
signal device_type_detected(device_type: String)
signal platform_pause_requested
signal platform_resume_requested

const SAVE_PATH := "user://palata_0_progress.json"
const SAVE_KEY := "palata0"
const SAVE_VERSION := 2

var available := false
var language := "ru"
var device_type := "desktop"
var progress: Dictionary = {}

var _bridge: Variant
var _bridge_callback: Variant
var _sdk_ready := false
var _game_ready_sent := false
var _gameplay_active := false
var _platform_paused := false
var _tree_was_paused := false
var _master_was_muted := false
var _ad_pending := false
var _after_interstitial: Callable
var _last_ad_msec := -1
var _ad_token := 0

# Yandex refuses a second fullscreen ad within roughly a minute of the last one,
# and a refused ad still has to hand the game back. Skipping the request
# ourselves keeps the "die, restart, start next night" chain from asking three
# times in twenty seconds and getting two silent refusals.
const AD_COOLDOWN_MSEC := 62000
# If the platform never reports the ad closing (offline, blocked frame, an SDK
# that simply never calls back), the game is left waiting on a callback that
# decides whether the ending panel appears at all. This is the black-screen
# insurance, not a nicety.
const AD_WATCHDOG_SECONDS := 10.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("yandex_sdk")
	progress = _default_progress()
	_load_local_progress()
	_detect_local_platform()
	if OS.has_feature("web"):
		_connect_web_bridge()
	else:
		call_deferred("_finish_native_initialization")


func _default_progress() -> Dictionary:
	return {
		"version": SAVE_VERSION,
		"selected_night": 0,
		"completed_nights": [],
		"shifts_finished": 0,
		"successful_shifts": 0,
		"last_ending": "",
		"results_by_night": {},
		"language": "",
		"updated_at": 0,
	}


func _detect_local_platform() -> void:
	var touch := DisplayServer.is_touchscreen_available() or OS.has_feature("mobile")
	if OS.has_feature("web"):
		var browser_touch: Variant = JavaScriptBridge.eval(
			"navigator.maxTouchPoints > 0 || matchMedia('(pointer: coarse)').matches", true)
		touch = touch or bool(browser_touch)
	device_type = "mobile" if touch else "desktop"


func _connect_web_bridge() -> void:
	_bridge = JavaScriptBridge.get_interface("YandexGamesBridge")
	if _bridge == null:
		call_deferred("_finish_native_initialization")
		return
	_bridge_callback = JavaScriptBridge.create_callback(_on_bridge_event)
	_bridge.connectGodot(_bridge_callback)


func _finish_native_initialization() -> void:
	sdk_initialized.emit(false)
	# Outside the browser nothing reports a language, so the standalone build
	# used to open in Russian on an English machine and stay there until the
	# player found the menu toggle. The system language stands in for the
	# platform payload; like it, it only decides the FIRST run, because
	# selected_language() prefers whatever is saved in progress.
	var system := OS.get_locale_language().to_lower()
	if system in SUPPORTED_LOCALES:
		language = system
	# Desktop and editor runs never see the platform payload, so the saved
	# choice has to be applied here or the menu toggle would not survive a
	# restart outside the browser.
	apply_locale()
	language_detected.emit(language)
	device_type_detected.emit(device_type)
	progress_changed.emit()


func _on_bridge_event(arguments: Array) -> void:
	if arguments.is_empty():
		return
	var event_name := String(arguments[0])
	var payload := String(arguments[1]) if arguments.size() > 1 else ""
	match event_name:
		"sdk_ready":
			_sdk_ready = true
			available = true
			_apply_environment_payload(payload)
			sdk_initialized.emit(true)
			if _game_ready_sent:
				_bridge.loadingReady()
			_bridge.setGameplayActive(_gameplay_active)
		"sdk_unavailable":
			available = false
			sdk_initialized.emit(false)
			if _ad_pending:
				_finish_interstitial()
		"cloud_data":
			_merge_cloud_progress(payload)
		"platform_pause", "ad_open":
			_apply_platform_pause()
		"platform_resume":
			_apply_platform_resume()
		"ad_close":
			_apply_platform_resume()
			_finish_interstitial()


func _apply_environment_payload(payload: String) -> void:
	var parsed: Variant = JSON.parse_string(payload)
	if not parsed is Dictionary:
		return
	var data := parsed as Dictionary
	var detected_language := String(data.get("language", "ru")).to_lower()
	if detected_language.length() >= 2:
		language = detected_language.left(2)
	# The platform language only decides the FIRST run: once the player has
	# picked a language in the menu it is stored in progress and wins, or
	# reopening the game on a Russian browser would silently undo their choice.
	apply_locale(String(progress.get("language", "")))
	var detected_device := String(data.get("device_type", device_type)).to_lower()
	if detected_device in ["desktop", "mobile", "tablet", "tv"]:
		device_type = detected_device
	language_detected.emit(language)
	device_type_detected.emit(device_type)


func notify_game_ready() -> void:
	if _game_ready_sent:
		return
	_game_ready_sent = true
	if _sdk_ready and _bridge != null:
		_bridge.loadingReady()


func set_gameplay_active(value: bool) -> void:
	if _gameplay_active == value:
		return
	_gameplay_active = value
	if _sdk_ready and _bridge != null:
		_bridge.setGameplayActive(value)


func is_mobile_device() -> bool:
	return device_type in ["mobile", "tablet"]


func selected_night() -> int:
	return clampi(int(progress.get("selected_night", 0)), 0, 10)


const SUPPORTED_LOCALES := ["ru", "en"]


func selected_language() -> String:
	# An empty saved value means "never chosen": fall back to what the platform
	# reported, and to Russian for anything the game does not ship.
	var saved := String(progress.get("language", ""))
	if saved in SUPPORTED_LOCALES:
		return saved
	return language if language in SUPPORTED_LOCALES else "ru"


func apply_locale(preferred := "") -> String:
	var locale := preferred if preferred in SUPPORTED_LOCALES else selected_language()
	TranslationServer.set_locale(locale)
	return locale


func set_language(locale: String) -> void:
	if not locale in SUPPORTED_LOCALES or String(progress.get("language", "")) == locale:
		TranslationServer.set_locale(locale if locale in SUPPORTED_LOCALES else selected_language())
		return
	progress["language"] = locale
	TranslationServer.set_locale(locale)
	_touch_progress()
	_save_progress(false)


func is_night_completed(index: int) -> bool:
	return index in _completed_nights()


func set_selected_night(index: int) -> void:
	index = clampi(index, 0, 10)
	if selected_night() == index:
		return
	progress["selected_night"] = index
	_touch_progress()
	_save_progress(false)


func record_shift_result(index: int, ending_id: String, success: bool, details: Dictionary = {}) -> void:
	progress["selected_night"] = clampi(index, 0, 10)
	progress["shifts_finished"] = int(progress.get("shifts_finished", 0)) + 1
	progress["last_ending"] = ending_id
	var results: Dictionary = progress.get("results_by_night", {})
	var night_key := "night_%d" % (index + 1)
	var result: Dictionary = {
		"ending": ending_id,
		"success": success,
		"saved_version": SAVE_VERSION,
		"recorded_at": int(Time.get_unix_time_from_system())
	}
	for key in details:
		result[String(key)] = details[key]
	results[night_key] = result
	progress["results_by_night"] = results
	if success:
		progress["successful_shifts"] = int(progress.get("successful_shifts", 0)) + 1
		var completed := _completed_nights()
		if not index in completed:
			completed.append(index)
			completed.sort()
		progress["completed_nights"] = completed
	_touch_progress()
	# A completed shift and any state immediately before an ad are flushed to the
	# server so refreshing the page or following an ad cannot lose progress.
	_save_progress(true)


func show_interstitial(after: Callable) -> void:
	# Every early exit here MUST still run `after`. The callback is what reveals
	# the ending panel or reloads the scene, so dropping it - which the old
	# `if _ad_pending: return` did - leaves the player on a dead screen.
	if _ad_pending:
		_run_after_ad(after)
		return
	var now := Time.get_ticks_msec()
	if _last_ad_msec >= 0 and now - _last_ad_msec < AD_COOLDOWN_MSEC:
		_run_after_ad(after)
		return
	_after_interstitial = after
	set_gameplay_active(false)
	_save_progress(true)
	if not OS.has_feature("web") or not available or _bridge == null:
		call_deferred("_finish_interstitial")
		return
	_ad_pending = true
	_last_ad_msec = now
	_ad_token += 1
	var token := _ad_token
	# process_always, because showing an ad pauses the tree.
	get_tree().create_timer(AD_WATCHDOG_SECONDS, true).timeout.connect(_on_ad_watchdog.bind(token))
	_bridge.showInterstitial()


func _on_ad_watchdog(token: int) -> void:
	if _ad_pending and token == _ad_token:
		push_warning("Interstitial never reported closing; continuing without it.")
		_apply_platform_resume()
		_finish_interstitial()


func _run_after_ad(after: Callable) -> void:
	if after.is_valid():
		after.call_deferred()


func _finish_interstitial() -> void:
	_ad_pending = false
	var callback := _after_interstitial
	_after_interstitial = Callable()
	if callback.is_valid():
		callback.call()


func _apply_platform_pause() -> void:
	if _platform_paused:
		return
	_platform_paused = true
	_tree_was_paused = get_tree().paused
	_master_was_muted = AudioServer.is_bus_mute(0)
	AudioServer.set_bus_mute(0, true)
	get_tree().paused = true
	platform_pause_requested.emit()


func _apply_platform_resume() -> void:
	if not _platform_paused:
		return
	_platform_paused = false
	AudioServer.set_bus_mute(0, _master_was_muted)
	get_tree().paused = _tree_was_paused
	platform_resume_requested.emit()


func _load_local_progress() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if not file:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		progress = _normalized_progress(parsed as Dictionary)


func _merge_cloud_progress(payload: String) -> void:
	var parsed: Variant = JSON.parse_string(payload)
	if not parsed is Dictionary:
		progress_changed.emit()
		return
	var cloud := _normalized_progress(parsed as Dictionary)
	var completed := _completed_nights()
	for value in cloud.get("completed_nights", []):
		var index := clampi(int(value), 0, 10)
		if not index in completed:
			completed.append(index)
	completed.sort()
	var local_updated := int(progress.get("updated_at", 0))
	var cloud_updated := int(cloud.get("updated_at", 0))
	if cloud_updated > local_updated:
		progress["selected_night"] = int(cloud.get("selected_night", 0))
		progress["last_ending"] = String(cloud.get("last_ending", ""))
		progress["language"] = String(cloud.get("language", progress.get("language", "")))
	progress["results_by_night"] = _merge_results_by_night(
		progress.get("results_by_night", {}), cloud.get("results_by_night", {}), local_updated, cloud_updated)
	progress["completed_nights"] = completed
	progress["shifts_finished"] = maxi(
		int(progress.get("shifts_finished", 0)), int(cloud.get("shifts_finished", 0)))
	progress["successful_shifts"] = maxi(
		int(progress.get("successful_shifts", 0)), int(cloud.get("successful_shifts", 0)))
	progress["updated_at"] = maxi(local_updated, cloud_updated)
	_save_progress(false)


func _completed_nights() -> Array[int]:
	var result: Array[int] = []
	for value in progress.get("completed_nights", []):
		var index := int(value)
		if index >= 0 and index <= 10 and not index in result:
			result.append(index)
	result.sort()
	return result


func _merge_results_by_night(local: Variant, cloud: Variant, local_updated: int, cloud_updated: int) -> Dictionary:
	var merged: Dictionary = {}
	if local is Dictionary:
		merged = local.duplicate(true)
	if not cloud is Dictionary:
		return merged
	for night_id in cloud:
		var cloud_result: Variant = cloud[night_id]
		if not cloud_result is Dictionary:
			continue
		var local_result: Variant = merged.get(night_id)
		var local_time := local_updated
		if local_result is Dictionary:
			local_time = int(local_result.get("recorded_at", local_updated))
		var cloud_time := int(cloud_result.get("recorded_at", cloud_updated))
		if not local_result is Dictionary or cloud_time >= local_time:
			merged[night_id] = cloud_result.duplicate(true)
	return merged


func _normalized_progress(source: Dictionary) -> Dictionary:
	var normalized := _default_progress()
	normalized["selected_night"] = clampi(int(source.get("selected_night", 0)), 0, 10)
	normalized["completed_nights"] = []
	for value in source.get("completed_nights", []):
		var index := clampi(int(value), 0, 10)
		if not index in normalized["completed_nights"]:
			normalized["completed_nights"].append(index)
	normalized["completed_nights"].sort()
	normalized["shifts_finished"] = maxi(0, int(source.get("shifts_finished", 0)))
	normalized["successful_shifts"] = maxi(0, int(source.get("successful_shifts", 0)))
	normalized["language"] = String(source.get("language", ""))
	var saved_results: Variant = source.get("results_by_night", {})
	if saved_results is Dictionary:
		normalized["results_by_night"] = saved_results.duplicate(true)
	normalized["last_ending"] = String(source.get("last_ending", ""))
	normalized["updated_at"] = maxi(0, int(source.get("updated_at", 0)))
	return normalized


func _touch_progress() -> void:
	progress["version"] = SAVE_VERSION
	progress["updated_at"] = int(Time.get_unix_time_from_system())


func _save_progress(flush_cloud: bool) -> void:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(progress))
		file.close()
	if OS.has_feature("web"):
		JavaScriptBridge.force_fs_sync()
	if _sdk_ready and _bridge != null:
		_bridge.saveData(JSON.stringify(progress), flush_cloud)
	progress_changed.emit()
