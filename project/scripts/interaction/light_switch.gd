extends Node3D

var enabled := true

func setup_from_import() -> void:
	add_to_group("light_switches")

func interaction_text() -> String:
	return tr("[E] Выключить свет") if enabled else tr("[E] Включить свет")

func interact(_actor: Node) -> void:
	enabled = not enabled
	var lights := get_tree().get_nodes_in_group("hospital_lights")
	for light in lights:
		if global_position.distance_to(light.global_position) < 8.0:
			light.visible = enabled

