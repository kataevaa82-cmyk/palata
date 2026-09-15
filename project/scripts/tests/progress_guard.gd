extends RefCounted

# Every test that actually starts a shift goes through yandex_sdk.gd, which
# persists to user://palata_0_progress.json - so a test run rewrites the
# player's saved night, ending and shift counters. That is not just untidy: the
# saved `selected_night` is read back by hud.gd on the next load, so one test
# leaving night 11 selected makes the *next* test start on the wrong night
# (which is how smoke_game.gd suddenly lost its 00:35 orderly).
#
# Snapshot before the first scene is instantiated, restore before quitting.

const SAVE_PATH := "user://palata_0_progress.json"

static var _existed := false
static var _contents := ""

static func snapshot() -> void:
	_existed = FileAccess.file_exists(SAVE_PATH)
	if not _existed:
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file:
		_contents = file.get_as_text()

static func restore() -> void:
	if not _existed:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		file.store_string(_contents)
