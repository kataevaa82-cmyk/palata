extends Node

signal minute_changed(hour: int, minute: int, formatted: String)
signal phase_changed(phase: String)
signal reached_time(hour: int, minute: int)

@export var real_seconds_per_game_minute := 4.0
# Shift runs 00:00 -> 06:00 = 360 game minutes (24 real minutes at 4 s/min).
# It used to start at 03:17, i.e. 163 minutes, which left too little time to
# finish the medical round. Every scheduled beat in game_director.gd was
# stretched by the same 360/163 factor so the pacing is unchanged, just slower.
var hour := 0
var minute := 0
var accumulator := 0.0
var running := false
var reverse := false
var current_phase := "DOUBT"

func _ready() -> void:
	add_to_group("time_manager")
	minute_changed.emit(hour, minute, formatted_time())

func start_clock() -> void:
	running = true

func reset_clock() -> void:
	hour = 0
	minute = 0
	accumulator = 0.0
	reverse = false
	current_phase = "DOUBT"
	minute_changed.emit(hour, minute, formatted_time())

func _process(delta: float) -> void:
	if not running:
		return
	accumulator += delta
	while accumulator >= real_seconds_per_game_minute:
		accumulator -= real_seconds_per_game_minute
		advance_minute(-1 if reverse else 1)

func advance_minute(amount: int) -> void:
	minute += amount
	while minute >= 60:
		minute -= 60
		hour += 1
	while minute < 0:
		minute += 60
		hour -= 1
	minute_changed.emit(hour, minute, formatted_time())
	reached_time.emit(hour, minute)
	_update_phase()

func formatted_time() -> String:
	return "%02d:%02d" % [hour, minute]

func total_minutes() -> int:
	return hour * 60 + minute

func set_reverse(value: bool) -> void:
	reverse = value

func pause_clock(value: bool) -> void:
	running = not value

func _update_phase() -> void:
	var next := "DOUBT"
	var t := total_minutes()
	# Phase borders scaled from the old 03:17-06:00 shift by 360/163:
	# 04:00 -> 01:35, 05:00 -> 03:47, 05:40 -> 05:16.
	if t >= 316:
		next = "SILENCE"
	elif t >= 227:
		next = "PROVOCATION"
	elif t >= 95:
		next = "ESCALATION"
	if next != current_phase:
		current_phase = next
		phase_changed.emit(current_phase)
