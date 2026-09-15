extends Node3D

var document_type := "journal"

const ROSTER := [
	{"id": "morozov", "text": "Морозов И. П. — палата 1, кровать 1"},
	{"id": "levchenko", "text": "Левченко А. Н. — палата 2, кровать 1"},
	{"id": "orlova", "text": "Орлова Н. Д. — палата 3, кровать 1"},
	{"id": "saveliev", "text": "Савельев П. М. — палата 4, кровать 1"},
	{"id": "demina", "text": "Демина В. Р. — палата 5, кровать 1"},
	{"id": "yudin", "text": "Юдин С. К. — палата 6, кровать 1"},
	{"id": "klimova", "text": "Климова Т. С. — палата 6, кровать 2"}
]

func setup_from_import(type: String) -> void:
	document_type = type
	add_to_group("documents")

func interaction_text() -> String:
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state and bool(state.get_flag("handoff_ready", false)):
		return tr("[E] Сдать смену на посту")
	return tr("[E] Открыть журнал")

func interact(_actor: Node) -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if not hud:
		return
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state and bool(state.get_flag("handoff_ready", false)):
		state.complete_task("final_call")
		state.set_flag("handoff_ready", false)
		state.request_ending("dawn")
		return
	if state:
		state.complete_task("journal_checked")
	var journal := tr("ЖУРНАЛ ОТДЕЛЕНИЯ") + "\n"
	var listed_count := 0
	for entry in ROSTER:
		var patient_id := String(entry.id)
		var presence: Dictionary = state.patient_presence.get(patient_id, {}) if state else {}
		if not presence.is_empty() and not bool(presence.get("present", true)):
			continue
		listed_count += 1
		journal += "\n%d. %s" % [listed_count, tr(String(entry.text))]
	if state and state.get_flag("player_name_journal"):
		journal += tr("\n8. Дежурный — палата 0")
	journal += tr("\n\nВсего пациентов: %d") % (state.patient_count if state else listed_count)
	hud.open_document(journal)
