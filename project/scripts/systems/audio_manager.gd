extends Node

var silence := false
var phase := 0.0
var generator: AudioStreamGenerator
var player: AudioStreamPlayer
var playback: AudioStreamGeneratorPlayback
var sample_time := 0.0
var ring_samples := 0
var step_samples := 0
var tv_noise := false
var echo_steps := false
var noise_seed := 0.137
var anomaly_samples := 0
var anomaly_total_samples := 1
var anomaly_style := 0
var ambient_event_samples := 0
var ambient_event_total_samples := 1
var ambient_event_style := 0
var ambient_wait_samples := 0
var ambient_event_pan := 0.0
var ambient_seed := 0.731

const AMBIENT_EVENT_DURATIONS := [0.85, 2.10, 0.62, 2.45, 1.35, 1.65, 1.05]
const AMBIENT_EVENT_COUNT := 7

func _ready() -> void:
	add_to_group("audio_manager")
	generator = AudioStreamGenerator.new()
	generator.mix_rate = 22050.0
	generator.buffer_length = 0.35
	player = AudioStreamPlayer.new()
	player.stream = generator
	# AudioStreamGenerator cannot use the Web export's default Sample path.
	# Force Stream so the procedural ambience remains audible in browsers.
	player.playback_type = AudioServer.PLAYBACK_TYPE_STREAM
	player.volume_db = -18.0
	add_child(player)
	player.play()
	playback = player.get_stream_playback()
	ambient_wait_samples = int(generator.mix_rate * 3.0)

func _process(_delta: float) -> void:
	if not playback:
		return
	var frames := playback.get_frames_available()
	for _i in frames:
		var sample := 0.0
		var ambient_sample := 0.0
		if not silence:
			sample = sin(phase * TAU * 50.0) * 0.022 + sin(phase * TAU * 100.0) * 0.008
			var monitor_cycle := fmod(sample_time, 3.2)
			if monitor_cycle < 0.055:
				sample += sin(sample_time * TAU * 930.0) * 0.12 * (1.0 - monitor_cycle / 0.055)
			if tv_noise:
				noise_seed = fmod(noise_seed * 17.17 + 0.31, 1.0)
				sample += (noise_seed - 0.5) * 0.055 + sin(sample_time * TAU * 156.0) * 0.025
			if ring_samples > 0:
				sample += (sin(sample_time * TAU * 440.0) + sin(sample_time * TAU * 480.0)) * 0.12
				ring_samples -= 1
			if step_samples > 0:
				sample += sin(sample_time * TAU * 72.0) * 0.18 * float(step_samples) / 1700.0
				step_samples -= 1
			if ambient_event_samples > 0:
				ambient_sample = _ambient_event_sample()
				ambient_event_samples -= 1
			elif ambient_wait_samples > 0:
				ambient_wait_samples -= 1
			else:
				_start_random_ambient_event()
		if anomaly_samples > 0:
			var elapsed := float(anomaly_total_samples - anomaly_samples) / generator.mix_rate
			var progress := 1.0 - float(anomaly_samples) / float(anomaly_total_samples)
			var envelope := pow(1.0 - progress, 1.35)
			noise_seed = fmod(noise_seed * 19.31 + 0.271, 1.0)
			var low_frequency := 34.0 + float(anomaly_style) * 7.0 + sin(elapsed * 2.3) * 5.0
			var dissonance := 67.0 + float(anomaly_style) * 13.0
			sample += sin(elapsed * TAU * low_frequency) * 0.30 * envelope
			sample += sin(elapsed * TAU * dissonance + sin(elapsed * 9.0) * 2.0) * 0.13 * envelope
			if anomaly_style % 2 == 0:
				sample += (noise_seed - 0.5) * 0.20 * envelope
			else:
				sample += sin(elapsed * elapsed * TAU * 115.0) * 0.15 * envelope
			if fmod(elapsed, 0.43 + float(anomaly_style) * 0.05) < 0.035:
				sample += sin(elapsed * TAU * 820.0) * 0.22 * envelope
			anomaly_samples -= 1
		phase += 1.0 / generator.mix_rate
		sample_time += 1.0 / generator.mix_rate
		# Rare room sounds are gently panned; the continuous electrical bed and
		# gameplay cues remain centred so important information stays readable.
		var left_gain := 1.0 - maxf(ambient_event_pan, 0.0) * 0.58
		var right_gain := 1.0 + minf(ambient_event_pan, 0.0) * 0.58
		playback.push_frame(Vector2(
			sample + ambient_sample * left_gain,
			sample + ambient_sample * right_gain))

func _next_ambient_random() -> float:
	ambient_seed = fmod(ambient_seed * 29.71 + 0.173, 1.0)
	return ambient_seed

func _start_random_ambient_event() -> void:
	_begin_ambient_event(int(floor(_next_ambient_random() * AMBIENT_EVENT_COUNT)))
	ambient_event_pan = lerpf(-0.82, 0.82, _next_ambient_random())
	# Long, uneven gaps keep the sounds surprising instead of turning them into
	# a recognisable loop.
	ambient_wait_samples = int(generator.mix_rate * lerpf(7.0, 19.0, _next_ambient_random()))

func _begin_ambient_event(style: int) -> void:
	ambient_event_style = posmod(style, AMBIENT_EVENT_COUNT)
	ambient_event_total_samples = int(
		generator.mix_rate * float(AMBIENT_EVENT_DURATIONS[ambient_event_style]))
	ambient_event_samples = ambient_event_total_samples

func _ambient_event_sample() -> float:
	var elapsed := float(ambient_event_total_samples - ambient_event_samples) / generator.mix_rate
	var progress := clampf(elapsed / float(AMBIENT_EVENT_DURATIONS[ambient_event_style]), 0.0, 1.0)
	match ambient_event_style:
		0: # Two hollow heating-pipe knocks.
			var strike_time := fmod(elapsed, 0.31)
			if elapsed < 0.72 and strike_time < 0.12:
				var strike_envelope := exp(-strike_time * 26.0) * (1.0 - progress)
				return (sin(strike_time * TAU * 176.0) + sin(strike_time * TAU * 263.0) * 0.55) * 0.15 * strike_envelope
		1: # A distant metal door slowly dragging on its hinges.
			noise_seed = fmod(noise_seed * 17.17 + 0.31, 1.0)
			var creak_envelope := pow(sin(progress * PI), 1.25)
			var creak_frequency := 82.0 + progress * 215.0 + sin(elapsed * 4.7) * 19.0
			return (sin(elapsed * TAU * creak_frequency + sin(elapsed * 15.0) * 1.8) * 0.075 + (noise_seed - 0.5) * 0.025) * creak_envelope
		2: # Water drop with a small pipe resonance.
			var drip_envelope := exp(-elapsed * 17.0)
			return (sin(elapsed * TAU * 1180.0) * 0.12 + sin(elapsed * TAU * 410.0) * 0.08) * drip_envelope
		3: # A trolley rolling somewhere beyond the ward doors.
			var trolley_envelope := pow(sin(progress * PI), 0.65)
			var wheel := sin(elapsed * TAU * 47.0) * 0.052 + sin(elapsed * TAU * 94.0) * 0.021
			var joint := 0.0
			var joint_time := fmod(elapsed, 0.39)
			if joint_time < 0.045:
				joint = sin(joint_time * TAU * 310.0) * exp(-joint_time * 38.0) * 0.075
			return (wheel + joint) * trolley_envelope
		4: # Fluorescent starter sputtering before it catches.
			noise_seed = fmod(noise_seed * 23.83 + 0.191, 1.0)
			var flicker_gate := 1.0 if fmod(elapsed, 0.17) < 0.09 else 0.18
			var flicker_envelope := sin(progress * PI)
			return (sin(elapsed * TAU * 100.0) * 0.07 + sin(elapsed * TAU * 200.0) * 0.025 + (noise_seed - 0.5) * 0.028) * flicker_gate * flicker_envelope
		5: # The layered metallic clang of the old lift settling.
			var clang_envelope := exp(-elapsed * 2.65)
			return (sin(elapsed * TAU * 229.0) * 0.11 + sin(elapsed * TAU * 353.0) * 0.075 + sin(elapsed * TAU * 517.0) * 0.045) * clang_envelope
		6: # A muffled cough/cloth movement from a distant room.
			noise_seed = fmod(noise_seed * 19.31 + 0.271, 1.0)
			var cough_time := fmod(elapsed, 0.43)
			var cough_envelope := exp(-cough_time * 10.0) if elapsed < 0.86 else 0.0
			return ((noise_seed - 0.5) * 0.105 + sin(cough_time * TAU * 91.0) * 0.052) * cough_envelope
	return 0.0

func set_silence(value: bool) -> void:
	silence = value

func play_phone_ring() -> void:
	ring_samples = int(generator.mix_rate * 0.72)

func set_tv_noise(value: bool) -> void:
	tv_noise = value

func set_echo_steps(value: bool) -> void:
	echo_steps = value

func play_anomaly_sting(id: String) -> void:
	anomaly_style = absi(id.hash()) % 4
	anomaly_total_samples = int(generator.mix_rate * (2.1 + float(anomaly_style) * 0.18))
	anomaly_samples = anomaly_total_samples

func player_step(_position: Vector3) -> void:
	step_samples = 1700
	if echo_steps:
		var timer := get_tree().create_timer(1.0)
		timer.timeout.connect(func(): step_samples = 1500)
