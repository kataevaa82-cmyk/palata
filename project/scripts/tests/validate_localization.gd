extends SceneTree

const ProgressGuard := preload("res://scripts/tests/progress_guard.gd")

# The Russian source text is the translation key, so a localisation bug here is
# silent: a msgid that did not survive the CSV import (an em dash, «ёлочки», ё,
# or an embedded \n turning into a literal backslash-n) simply returns the
# Russian string unchanged, which looks exactly like "not wired up yet".
#
# So this asserts the opposite of the usual test: under locale "en" the sample
# strings must NOT equal their Russian source, and the ones with punctuation the
# CSV can mangle are checked character by character.

const SAMPLES := [
	"ЗДОРОВЬЕ",
	"ЕЩЁ ОДНА СМЕНА",
	"%s — палата %d, кровать %d. Браслет и карточка совпадают.",
	"«Тогда один лишний». Линия оборвалась.",
	"Обычная ночь. Семь пациентов, журнал, доска назначений.\nСверяйте браслеты и доживите до 06:00.",
]

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	ProgressGuard.snapshot()
	var failures: Array[String] = []
	var locales := TranslationServer.get_loaded_locales()
	if not "en" in locales:
		failures.append("no_en_translation_loaded (%s)" % ", ".join(locales))

	TranslationServer.set_locale("en")
	for source in SAMPLES:
		var translated := tr(source)
		if translated == source:
			failures.append("untranslated: %s" % source.replace("\n", "\\n"))
		elif _has_cyrillic(translated):
			failures.append("still_cyrillic: %s" % translated.replace("\n", "\\n"))

	# Formatting must survive translation: the English string has to keep the
	# same placeholders in the same order, or the % operator throws at runtime.
	var formatted: String = tr(SAMPLES[2]) % ["Klimova T. S.", 6, 2]
	if "%" in formatted or formatted.is_empty():
		failures.append("format_broken: %s" % formatted)

	# The multi-line brief must come back with a real newline, not "\\n".
	var brief := tr(SAMPLES[4])
	if "\\n" in brief or not "\n" in brief:
		failures.append("newline_broken: %s" % brief.replace("\n", "<LF>"))

	# ...and Russian must still be Russian.
	TranslationServer.set_locale("ru")
	for source in SAMPLES:
		if tr(source) != source:
			failures.append("ru_changed: %s" % source.replace("\n", "\\n"))

	failures.append_array(await _check_menu_toggle())

	print("VALIDATE_LOCALIZATION samples=%d locales=[%s] failures=%d" % [
		SAMPLES.size(), ", ".join(TranslationServer.get_loaded_locales()), failures.size()])
	if failures.is_empty():
		print("VALIDATE_LOCALIZATION OK")
	else:
		for failure in failures:
			print("  FAIL ", failure)
	ProgressGuard.restore()
	quit(0 if failures.is_empty() else 1)

func _check_menu_toggle() -> Array[String]:
	# The button in the start panel is the only way a player on a Russian
	# browser reaches English, so press it the way they would and check the
	# menu actually rebuilt itself: the night list and the brief are built in
	# code and do NOT auto-translate on a locale change.
	var failures: Array[String] = []
	var packed: PackedScene = load("res://scenes/hospital/main.tscn")
	var game: Node = packed.instantiate()
	root.add_child(game)
	for _frame in 6:
		await process_frame

	var hud := game.get_node("HUD")
	var button := hud.get_node("StartPanel/LanguageButton") as Button
	var level_select := hud.get_node("StartPanel/LevelSelect") as OptionButton
	var brief := hud.get_node("StartPanel/LevelBrief") as Label
	if not button:
		failures.append("no_language_button")
		game.free()
		return failures

	if TranslationServer.get_locale().begins_with("ru") and button.text != "EN":
		failures.append("button_label_ru_%s" % button.text)
	button.pressed.emit()
	await process_frame
	if TranslationServer.get_locale().begins_with("ru"):
		failures.append("locale_did_not_switch")
	if _has_cyrillic(level_select.get_item_text(0)):
		failures.append("night_list_not_rebuilt: %s" % level_select.get_item_text(0))
	if _has_cyrillic(brief.atr(brief.text)):
		failures.append("brief_not_rebuilt")
	# In English the button offers the way back. It used to read "РУС", which an
	# English player cannot read; what matters is that it says something and
	# says it in Latin script, not that it says one exact word.
	if button.text.is_empty() or _has_cyrillic(button.text):
		failures.append("button_label_en_%s" % button.text)
	# Substitutions must be translated too. The format string can be English
	# while a Russian patient name inserted into it still leaks onto the HUD.
	for patient in get_nodes_in_group("care_patients"):
		var prompt := String(patient.interaction_text())
		if _has_cyrillic(prompt):
			failures.append("patient_prompt_not_translated: %s" % prompt)
			break

	# ...and back, because the switch has to work in both directions.
	button.pressed.emit()
	await process_frame
	if not TranslationServer.get_locale().begins_with("ru"):
		failures.append("locale_did_not_switch_back")
	if not _has_cyrillic(level_select.get_item_text(0)):
		failures.append("night_list_stuck_in_english")

	game.free()
	await process_frame
	return failures

func _has_cyrillic(text: String) -> bool:
	for index in text.length():
		var code := text.unicode_at(index)
		if code >= 0x0400 and code <= 0x04FF:
			return true
	return false
