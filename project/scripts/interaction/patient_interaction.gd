extends Node3D

var patient_id := ""
var patient_name := ""
var room := 0
var bed := 1

func setup_from_import(id: String, display_name: String, room_number: int, bed_number: int) -> void:
	patient_id = id
	patient_name = display_name
	room = room_number
	bed = bed_number
	add_to_group("care_patients")

func interaction_text() -> String:
	return tr("[E] %s — палата %d, кровать %d") % [tr(patient_name), room, bed]

func interact(_actor: Node) -> void:
	var manager := get_tree().get_first_node_in_group("care_manager")
	if manager:
		manager.interact_patient(patient_id, patient_name, room, bed, self)
