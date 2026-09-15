extends Node3D

var care_id := ""

func setup_from_import(id: String) -> void:
	care_id = id
	add_to_group("care_interactables")
	var manager := get_tree().get_first_node_in_group("care_manager")
	if manager:
		manager.register_interactable(care_id, self)

func interaction_text() -> String:
	var manager := get_tree().get_first_node_in_group("care_manager")
	return manager.get_interaction_text(care_id) if manager else tr("[E] Осмотреть")

func interact(_actor: Node) -> void:
	var manager := get_tree().get_first_node_in_group("care_manager")
	if manager:
		manager.interact_object(care_id, self)
