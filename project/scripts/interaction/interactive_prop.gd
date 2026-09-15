extends Node3D

var used := false

func setup_from_import() -> void:
	add_to_group("interactive_props")

func interaction_text() -> String:
	match name:
		"interaction_emergency_button": return tr("[E] Нажать аварийную кнопку")
		"interaction_old_wall_clock": return tr("[E] Посмотреть на часы")
		"interaction_medical_cart": return tr("[E] Осмотреть медицинскую тележку")
		"interaction_mop_bucket": return tr("[E] Проверить ведро и швабру")
	return tr("[E] Осмотреть")

func interact(_actor: Node) -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	var state := get_tree().get_first_node_in_group("hospital_state")
	if state:
		state.record_observation("interactive_prop", name)
	if name == "interaction_emergency_button":
		used = not used
		if hud: hud.show_message(tr("Красная кнопка утопилась в стену.") if used else tr("Кнопка вернулась в исходное положение."), 2.5)
	elif name == "interaction_old_wall_clock":
		if hud: hud.show_message(tr("Секундная стрелка дёрнулась, но время не изменилось."), 2.5)
	elif name == "interaction_medical_cart":
		used = not used
		if hud: hud.show_message(tr("В верхнем ящике пусто. На дне лежит чужой ключ.") if used else tr("Ящик закрыт."), 2.5)
	elif name == "interaction_mop_bucket":
		used = not used
		if hud: hud.show_message(tr("Вода в синем ведре тихо плеснула.") if used else tr("Ведро снова неподвижно."), 2.5)
