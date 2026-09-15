extends Node3D

var called := false

func setup_from_import() -> void:
	add_to_group("hospital_elevator")

func interaction_text() -> String:
	return tr("[E] Вызвать лифт")

func interact(_actor: Node) -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if called:
		if hud:
			hud.show_message(tr("За дверями лифта кто-то ждёт."), 2.5)
		return
	called = true
	var anomalies := get_tree().get_first_node_in_group("anomaly_manager")
	if anomalies:
		anomalies.activate("elevator_minus_one")
	if hud:
		hud.show_message(tr("Индикатор лифта загорелся: −1"), 3.5)
