extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var audio := Node.new()
	audio.set_script(load("res://scripts/systems/audio_manager.gd"))
	root.add_child(audio)
	await process_frame
	audio.set_process(false)

	var failures: Array[String] = []
	var peaks: Array[float] = []
	for style in audio.AMBIENT_EVENT_COUNT:
		audio._begin_ambient_event(style)
		var total: int = audio.ambient_event_total_samples
		var peak := 0.0
		for sample_index in 512:
			audio.ambient_event_samples = maxi(
				1, total - int(float(total - 1) * float(sample_index) / 511.0))
			peak = maxf(peak, absf(audio._ambient_event_sample()))
		peaks.append(peak)
		if peak < 0.005:
			failures.append("silent_style_%d" % style)

	audio.ambient_wait_samples = 0
	audio._start_random_ambient_event()
	if audio.ambient_event_samples <= 0 or audio.ambient_wait_samples <= 0:
		failures.append("scheduler")
	if absf(audio.ambient_event_pan) > 0.83:
		failures.append("pan_range")

	print("AUDIO_AMBIENCE styles=", peaks.size(), " peaks=", peaks, " failures=", failures.size())
	quit(0 if failures.is_empty() else 1)
