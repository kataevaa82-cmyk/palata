extends Node3D

func setup_from_import() -> void:
	add_to_group("hospital_exit")

func interaction_text() -> String:
	return tr("[E] Пожарный выход")

func interact(_actor: Node) -> void:
	var time_manager := get_tree().get_first_node_in_group("time_manager")
	var state := get_tree().get_first_node_in_group("hospital_state")
	var hud := get_tree().get_first_node_in_group("hud")
	if not time_manager or not state:
		return
	if bool(state.get_flag("handoff_ready", false)) or bool(state.get_flag("shift_complete", false)):
		# A finished shift must not be lost to the 05:57 trap door: the only way
		# out of a completed night is the handoff at the post.
		if hud:
			hud.show_message(tr("Смена не сдана. Сдайте журнал на посту."), 3.0)
		return
	if time_manager.total_minutes() < 357:
		if hud:
			hud.show_message(tr("Смена ещё не закончена."), 2.5)
		return
	if time_manager.total_minutes() < 360:
		state.request_ending("early_exit")
	else:
		state.request_ending("dawn")
