# editor/node_editor_parts/node_editor_io_export.py
import dearpygui.dearpygui as dpg

class NodeEditorIOExportMixin:
    def export_graph_to_json(self):
        self.sync_with_dpg()

        root_node = None
        for node in self.nodes_data.values():
            if node.type == "Root":
                root_node = node
                break

        if not root_node:
            print("[Экспорт Error] Узел Root не обнаружен!")
            return None

        # Определение связанных хитбоксов для Root -> Body
        body_shapes_list = []
        body_pin = root_node.properties.get("body_pin")
        for _, (p_out, p_in) in self.links_data.items():
            if p_out == body_pin:
                hb_node_id = self.pin_to_node.get(p_in)
                if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                    hb = self.nodes_data[hb_node_id]
                    stype = hb.properties.get("shape_type", "rectangle")
                    body_shapes_list.append({
                        "shape": {
                            "template": hb.properties.get("shape_template", "forms.rect"),
                            "type": stype,
                            **({"r": hb.properties.get("r", 25)} if stype == "circle" else {"w": hb.properties.get("w", 30), "h": hb.properties.get("h", 50)})
                        },
                        "offset_x": hb.properties.get("offset_x", 0),
                        "offset_y": hb.properties.get("offset_y", 0),
                        "angle": hb.properties.get("angle", 0)
                    })

        # Определение связанных хитбоксов для Root -> Detection
        detection_shapes_list = []
        det_pin = root_node.properties.get("det_pin")
        for _, (p_out, p_in) in self.links_data.items():
            if p_out == det_pin:
                hb_node_id = self.pin_to_node.get(p_in)
                if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                    hb = self.nodes_data[hb_node_id]
                    stype = hb.properties.get("shape_type", "rectangle")
                    detection_shapes_list.append({
                        "shape": {
                            "template": hb.properties.get("shape_template", "forms.rect"),
                            "type": stype,
                            **({"r": hb.properties.get("r", 110)} if stype == "circle" else {"w": hb.properties.get("w", 220), "h": hb.properties.get("h", 70)})
                        },
                        "offset_x": hb.properties.get("offset_x", 0),
                        "offset_y": hb.properties.get("offset_y", -10),
                        "angle": hb.properties.get("angle", 0),
                        "type": hb.properties.get("sprite_dir", "following")
                    })

        # Определение связанных хитбоксов для Root -> Stopping (Зона остановки преследования)
        stop_shapes_list = []
        stop_pin = root_node.properties.get("stop_pin")
        for _, (p_out, p_in) in self.links_data.items():
            if p_out == stop_pin:
                hb_node_id = self.pin_to_node.get(p_in)
                if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                    hb = self.nodes_data[hb_node_id]
                    stype = hb.properties.get("shape_type", "rectangle")
                    stop_shapes_list.append({
                        "shape": {
                            "template": hb.properties.get("shape_template", "forms.rect"),
                            "type": stype,
                            **({"r": hb.properties.get("r", 40)} if stype == "circle" else {"w": hb.properties.get("w", 120), "h": hb.properties.get("h", 70)})
                        },
                        "offset_x": hb.properties.get("offset_x", 0),
                        "offset_y": hb.properties.get("offset_y", 0),
                        "angle": hb.properties.get("angle", 0),
                        "type": hb.properties.get("sprite_dir", "stationary")
                    })

        # Формируем fallback-значения для старого классического движка
        fallback_body = body_shapes_list[0]["shape"] if body_shapes_list else {"template": "forms.rect", "w": 30, "h": 50}
        if body_shapes_list:
            fallback_body["w"] = body_shapes_list[0]["shape"].get("w", 30)
            fallback_body["h"] = body_shapes_list[0]["shape"].get("h", 50)

        fallback_det = {
            "template": "detections.front_view",
            "shape": detection_shapes_list[0]["shape"] if detection_shapes_list else {"template": "forms.rect", "w": 220, "h": 70},
            "offset_x": detection_shapes_list[0]["offset_x"] if detection_shapes_list else 0,
            "offset_y": detection_shapes_list[0]["offset_y"] if detection_shapes_list else -10,
            "type": detection_shapes_list[0]["type"] if detection_shapes_list else "following"
        }

        # Вычисляем математический fallback_stop_dist из первого полигона остановки
        fallback_stop_dist = root_node.properties.get("stop_dist", 60)
        if stop_shapes_list:
            first_shape = stop_shapes_list[0]["shape"]
            if first_shape.get("type") == "circle":
                fallback_stop_dist = first_shape.get("r", 40)
            else:
                fallback_stop_dist = int(first_shape.get("w", 120) / 2)

        export_data = {
            "hp": root_node.properties.get("hp", 3),
            "body": fallback_body,
            "body_shapes": body_shapes_list,
            "movement_config": {
                "type_move": root_node.properties.get("type_move", "walking"),
                "speed": root_node.properties.get("speed", 1.2),
                "range_x": root_node.properties.get("range_x", 120),
                "stop_dist": fallback_stop_dist,
                "patrol_on_platform": root_node.properties.get("patrol_on_platform", False)
            },
            "detection": fallback_det,
            "detection_shapes": detection_shapes_list,
            "stop_shapes": stop_shapes_list,
            "projectiles": [],
            "attacks": [],
            "movements": [],
            "sequences": [],
            "flows": [],
            "orders": []
        }

        sorted_attacks = sorted([n for n in self.nodes_data.values() if n.type == "Attack"], key=lambda x: dpg.get_item_pos(x.id)[1])
        sorted_movements = sorted([n for n in self.nodes_data.values() if n.type == "Movement"], key=lambda x: dpg.get_item_pos(x.id)[1])
        sorted_projectiles = sorted([n for n in self.nodes_data.values() if n.type == "Projectile"], key=lambda x: dpg.get_item_pos(x.id)[1])

        p_root_flows = list(root_node.output_pins.keys())[0]
        p_root_seqs = list(root_node.output_pins.keys())[1]

        # Сбор связанных Flows и Sequences
        connected_flow_ids = []
        for _, (p_out, p_in) in self.links_data.items():
            if p_out == p_root_flows:
                flow_node_id = self.pin_to_node.get(p_in)
                if flow_node_id and flow_node_id in self.nodes_data:
                    connected_flow_ids.append(flow_node_id)

        connected_seq_ids = []
        for _, (p_out, p_in) in self.links_data.items():
            if p_out == p_root_seqs:
                seq_node_id = self.pin_to_node.get(p_in)
                if seq_node_id and seq_node_id in self.nodes_data:
                    connected_seq_ids.append(seq_node_id)

        sorted_flows = sorted([self.nodes_data[nid] for nid in connected_flow_ids if self.nodes_data[nid].type == "Flow"], key=lambda x: dpg.get_item_pos(x.id)[1])
        sorted_sequences = sorted([self.nodes_data[nid] for nid in connected_seq_ids if self.nodes_data[nid].type == "Sequence"], key=lambda x: dpg.get_item_pos(x.id)[1])

        # 10. Экспорт атак (Attacks)
        for atk_node in sorted_attacks:
            atk_dict = {
                "name": atk_node.properties.get("name", "Attack"),
                "cooldown": atk_node.properties.get("cooldown", 45),
                "windup": atk_node.properties.get("windup", 35),
                "shapes": []
            }

            p_hitboxes_out = list(atk_node.output_pins.keys())[0]
            connected_hitboxes = []
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == p_hitboxes_out:
                    hb_node_id = self.pin_to_node.get(p_in)
                    if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                        connected_hitboxes.append(self.nodes_data[hb_node_id])

            connected_hitboxes.sort(key=lambda x: x.properties.get("delay", 0))
            for hb in connected_hitboxes:
                hb_shape_type = hb.properties.get("shape_type", "rectangle")
                hb_dict = {
                    "shape": {
                        "template": hb.properties.get("shape_template", "forms.rect"),
                        "type": hb_shape_type,
                        **({"r": hb.properties.get("r", 25)} if hb_shape_type == "circle" else {"w": hb.properties.get("w", 50), "h": hb.properties.get("h", 40)})
                    },
                    "offset_x": hb.properties.get("offset_x", 10),
                    "offset_y": hb.properties.get("offset_y", 0),
                    "angle": hb.properties.get("angle", 0),
                    "delay": hb.properties.get("delay", 0),
                    "duration": hb.properties.get("duration", 10),
                    "damage": hb.properties.get("damage", 1),
                    "kb_angle_hit": hb.properties.get("kb_angle_hit", 0),
                    "kb_force_hit": hb.properties.get("kb_force_hit", 12.0),
                    "kb_angle_parry": hb.properties.get("kb_angle_parry", 0),
                    "kb_force_parry": hb.properties.get("kb_force_parry", 6.0),
                    "sprite_dir": hb.properties.get("sprite_dir", "forward")
                }
                if hb.properties.get("vis_enabled", False):
                    vis_type = hb.properties.get("vis_type", "rectangle")
                    hb_dict["visual_box"] = {
                        "type": vis_type,
                        "offset_x": hb.properties.get("vis_offset_x", 0),
                        "offset_y": hb.properties.get("vis_offset_y", 0),
                        **({"r": hb.properties.get("vis_r", 25)} if vis_type == "circle" else {"w": hb.properties.get("vis_w", 50), "h": hb.properties.get("vis_h", 40)})
                    }
                atk_dict["shapes"].append(hb_dict)
            export_data["attacks"].append(atk_dict)

        # 11. Экспорт перемещений (Movements)
        for mov_node in sorted_movements:
            stop_shapes_mov_list = []
            stop_pin_mov = mov_node.properties.get("stop_pin")
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == stop_pin_mov:
                    hb_node_id = self.pin_to_node.get(p_in)
                    if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                        hb = self.nodes_data[hb_node_id]
                        stype = hb.properties.get("shape_type", "rectangle")
                        stop_shapes_mov_list.append({
                            "shape": {
                                "template": hb.properties.get("shape_template", "forms.rect"),
                                "type": stype,
                                **({"r": hb.properties.get("r", 30)} if stype == "circle" else {"w": hb.properties.get("w", 120), "h": hb.properties.get("h", 60)})
                            },
                            "offset_x": hb.properties.get("offset_x", 0),
                            "offset_y": hb.properties.get("offset_y", 0),
                            "angle": hb.properties.get("angle", 0)
                        })

            fallback_mov_stop_dist = mov_node.properties.get("stop_dist", 0)
            if stop_shapes_mov_list and stop_shapes_mov_list[0]["shape"].get("type") == "rectangle":
                fallback_mov_stop_dist = int(stop_shapes_mov_list[0]["shape"].get("w", 120) / 2)

            mov_dict = {
                "name": mov_node.properties.get("name", "Movement"),
                "stop_dist": fallback_mov_stop_dist,
                "stop_shapes": stop_shapes_mov_list,
                "phases": []
            }

            p_phases_out = list(mov_node.output_pins.keys())[0]
            connected_phases = []
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == p_phases_out:
                    phase_node_id = self.pin_to_node.get(p_in)
                    if phase_node_id and self.nodes_data[phase_node_id].type == "Phase":
                        connected_phases.append(self.nodes_data[phase_node_id])

            connected_phases.sort(key=lambda x: x.properties.get("delay", 0))
            for ph in connected_phases:
                mov_dict["phases"].append({
                    "direction": ph.properties.get("direction", "forward"),
                    "curve": ph.properties.get("curve", "fade_out"),
                    "force_x": ph.properties.get("force_x", 8.0),
                    "force_y": ph.properties.get("force_y", 0.0),
                    "delay": ph.properties.get("delay", 0),
                    "duration": ph.properties.get("duration", 15)
                })
            export_data["movements"].append(mov_dict)

        # 12. Экспорт снарядов (Projectiles)
        for proj_node in sorted_projectiles:
            proj_shapes_list = []
            hitbox_pin = proj_node.properties.get("hitbox_pin")
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == hitbox_pin:
                    hb_node_id = self.pin_to_node.get(p_in)
                    if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                        hb = self.nodes_data[hb_node_id]
                        stype = hb.properties.get("shape_type", "rectangle")
                        proj_shapes_list.append({
                            "shape": {
                                "template": hb.properties.get("shape_template", "forms.circle"),
                                "type": stype,
                                **({"r": hb.properties.get("r", 8)} if stype == "circle" else {"w": hb.properties.get("w", 16), "h": hb.properties.get("h", 16)})
                            },
                            "offset_x": hb.properties.get("offset_x", 0),
                            "offset_y": hb.properties.get("offset_y", 0),
                            "angle": hb.properties.get("angle", 0)
                        })

            fallback_radius = proj_node.properties.get("radius", 8)
            if proj_shapes_list and proj_shapes_list[0]["shape"].get("type") == "circle":
                fallback_radius = proj_shapes_list[0]["shape"].get("r", 8)

            export_data["projectiles"].append({
                "name": proj_node.properties.get("name", "Projectile"),
                "speed": proj_node.properties.get("speed", 10.0),
                "angle": proj_node.properties.get("angle", 0.0),
                "gravity": proj_node.properties.get("gravity", 0.0),
                "damage": proj_node.properties.get("damage", 1),
                "radius": fallback_radius,
                "aim_at_player": proj_node.properties.get("aim_at_player", False),
                "homing": proj_node.properties.get("homing", 0.0),
                "shoot_cooldown": proj_node.properties.get("shoot_cooldown", 30),
                "shapes": proj_shapes_list
            })

        # 13. Экспорт последовательностей (Sequences)
        for seq_node in sorted_sequences:
            trig_shapes_list = []
            trig_pin = seq_node.properties.get("trig_pin")
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == trig_pin:
                    hb_node_id = self.pin_to_node.get(p_in)
                    if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                        hb = self.nodes_data[hb_node_id]
                        stype = hb.properties.get("shape_type", "rectangle")
                        trig_shapes_list.append({
                            "shape": {
                                "template": hb.properties.get("shape_template", "forms.rect"),
                                "type": stype,
                                **({"r": hb.properties.get("r", 45)} if stype == "circle" else {"w": hb.properties.get("w", 90), "h": hb.properties.get("h", 50)})
                            },
                            "offset_x": hb.properties.get("offset_x", 10),
                            "offset_y": hb.properties.get("offset_y", 0),
                            "angle": hb.properties.get("angle", 0),
                            "type": hb.properties.get("sprite_dir", "following")
                        })

            fallback_tz = {
                "shape": trig_shapes_list[0]["shape"] if trig_shapes_list else {"template": "forms.rect", "w": 90, "h": 50},
                "offset_x": trig_shapes_list[0]["offset_x"] if trig_shapes_list else 10,
                "offset_y": trig_shapes_list[0]["offset_y"] if trig_shapes_list else 0,
                "type": trig_shapes_list[0]["type"] if trig_shapes_list else "following",
                "hold_time": seq_node.properties.get("trig_hold_time", 0),
                "consecutive_limit": seq_node.properties.get("trig_consecutive_limit", 3),
                "accumulate_hold": seq_node.properties.get("trig_accumulate_hold", True)
            }

            seq_dict = {
                "name": seq_node.properties.get("name", "Sequence"),
                "chance": seq_node.properties.get("chance", 0.5),
                "cooldown": seq_node.properties.get("cooldown", 120),
                "post_cooldown": seq_node.properties.get("post_cooldown", 30),
                "trigger_zone": fallback_tz,
                "trigger_shapes": trig_shapes_list,
                "steps": []
            }
            if "color" in seq_node.properties:
                seq_dict["color"] = seq_node.properties["color"]

            for pin_id in seq_node.properties.get("steps_pins", []):
                pin_prop = seq_node.output_pins[pin_id].properties
                step_delay = pin_prop["delay"]

                linked_act = None
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == pin_id:
                        act_node_id = self.pin_to_node.get(p_in)
                        if act_node_id and self.nodes_data[act_node_id].type in ("Attack", "Movement", "Projectile"):
                            linked_act = self.nodes_data[act_node_id]
                            break

                if linked_act:
                    atype = linked_act.type.lower()
                    aidx = 0
                    if linked_act.type == "Attack" and linked_act in sorted_attacks:
                        aidx = sorted_attacks.index(linked_act)
                    elif linked_act.type == "Movement" and linked_act in sorted_movements:
                        aidx = sorted_movements.index(linked_act)
                    elif linked_act.type == "Projectile" and linked_act in sorted_projectiles:
                        aidx = sorted_projectiles.index(linked_act)

                    step_dict = {
                        "type": atype,
                        "idx": aidx,
                        "delay": step_delay
                    }
                    if atype == "attack":
                        step_dict["trigger"] = "time"
                    seq_dict["steps"].append(step_dict)

            seq_dict["steps"].sort(key=lambda x: x["delay"])
            export_data["sequences"].append(seq_dict)

        # 14. Экспорт потоков поведения (Flows)
        for flow_node in sorted_flows:
            trig_shapes_list = []
            trig_pin = flow_node.properties.get("trig_pin")
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == trig_pin:
                    hb_node_id = self.pin_to_node.get(p_in)
                    if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                        hb = self.nodes_data[hb_node_id]
                        stype = hb.properties.get("shape_type", "rectangle")
                        trig_shapes_list.append({
                            "shape": {
                                "template": hb.properties.get("shape_template", "forms.rect"),
                                "type": stype,
                                **({"r": hb.properties.get("r", 80)} if stype == "circle" else {"w": hb.properties.get("w", 250), "h": hb.properties.get("h", 80)})
                            },
                            "offset_x": hb.properties.get("offset_x", 0),
                            "offset_y": hb.properties.get("offset_y", 0),
                            "angle": hb.properties.get("angle", 0),
                            "type": hb.properties.get("sprite_dir", "following")
                        })

            fallback_tz = {
                "shape": trig_shapes_list[0]["shape"] if trig_shapes_list else {"template": "forms.rect", "w": 250, "h": 80},
                "offset_x": trig_shapes_list[0]["offset_x"] if trig_shapes_list else 0,
                "offset_y": trig_shapes_list[0]["offset_y"] if trig_shapes_list else 0,
                "type": trig_shapes_list[0]["type"] if trig_shapes_list else "following",
                "hold_time": flow_node.properties.get("trig_hold_time", 0),
                "consecutive_limit": flow_node.properties.get("trig_consecutive_limit", 3),
                "accumulate_hold": flow_node.properties.get("trig_accumulate_hold", True)
            }

            flow_dict = {
                "name": flow_node.properties.get("name", "Flow"),
                "chance": flow_node.properties.get("chance", 0.5),
                "cooldown": flow_node.properties.get("cooldown", 180),
                "post_cooldown": flow_node.properties.get("post_cooldown", 30),
                "trigger_zone": fallback_tz,
                "trigger_shapes": trig_shapes_list,
                "steps": []
            }
            if "color" in flow_node.properties:
                flow_dict["color"] = flow_node.properties["color"]

            for pin_id in flow_node.properties.get("steps_pins", []):
                pin_prop = flow_node.output_pins[pin_id].properties
                step_delay = pin_prop["delay"]
                is_random = pin_prop["is_random"]

                linked_seqs = []
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == pin_id:
                        seq_id = self.pin_to_node.get(p_in)
                        if seq_id and seq_id in self.nodes_data and self.nodes_data[seq_id].type == "Sequence":
                            seq_node = self.nodes_data[seq_id]
                            if seq_node in sorted_sequences:
                                linked_seqs.append(sorted_sequences.index(seq_node))

                step_dict = {
                    "delay": step_delay,
                    "is_random": is_random
                }
                if is_random:
                    step_dict["seq_pool"] = sorted(linked_seqs) if linked_seqs else [0]
                else:
                    step_dict["seq_idx"] = linked_seqs[0] if linked_seqs else 0
                flow_dict["steps"].append(step_dict)

            flow_dict["steps"].sort(key=lambda x: x["delay"])
            export_data["flows"].append(flow_dict)

        # 15. Экспорт цепочек порядка (Orders)
        for node_id, node in self.nodes_data.items():
            if node.type == "Order":
                trig_shapes_list = []
                trig_pin = node.properties.get("trig_pin")
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == trig_pin:
                        hb_node_id = self.pin_to_node.get(p_in)
                        if hb_node_id and self.nodes_data[hb_node_id].type == "Hitbox":
                            hb = self.nodes_data[hb_node_id]
                            stype = hb.properties.get("shape_type", "rectangle")
                            trig_shapes_list.append({
                                "shape": {
                                    "template": hb.properties.get("shape_template", "forms.rect"),
                                    "type": stype,
                                    **({"r": hb.properties.get("r", 75)} if stype == "circle" else {"w": hb.properties.get("w", 150), "h": hb.properties.get("h", 60)})
                                },
                                "offset_x": hb.properties.get("offset_x", 0),
                                "offset_y": hb.properties.get("offset_y", 0),
                                "angle": hb.properties.get("angle", 0),
                                "type": hb.properties.get("sprite_dir", "following")
                            })

                fallback_tz = {
                    "shape": trig_shapes_list[0]["shape"] if trig_shapes_list else {"template": "forms.rect", "w": 150, "h": 60},
                    "offset_x": trig_shapes_list[0]["offset_x"] if trig_shapes_list else 0,
                    "offset_y": trig_shapes_list[0]["offset_y"] if trig_shapes_list else 0,
                    "type": trig_shapes_list[0]["type"] if trig_shapes_list else "following",
                    "hold_time": node.properties.get("trig_hold_time", 0),
                    "consecutive_limit": node.properties.get("trig_consecutive_limit", 3),
                    "accumulate_hold": node.properties.get("trig_accumulate_hold", True)
                }

                pos = dpg.get_item_pos(node_id)
                order_dict = {
                    "name": node.properties.get("name", "Order"),
                    "pos": pos,
                    "chance": node.properties.get("chance", 1.0),
                    "cooldown": node.properties.get("cooldown", 120),
                    "post_cooldown": node.properties.get("post_cooldown", 30),
                    "trigger_zone": fallback_tz,
                    "trigger_shapes": trig_shapes_list,
                    "steps": []
                }
                for pin_id in node.properties.get("steps_pins", []):
                    pin_prop = node.input_pins[pin_id].properties
                    step_idx = pin_prop["index"]

                    linked_connections = []
                    for _, (p_out, p_in) in self.links_data.items():
                        if p_in == pin_id:
                            out_node_id = self.pin_to_node.get(p_out)
                            if out_node_id and out_node_id in self.nodes_data:
                                out_node = self.nodes_data[out_node_id]
                                linked_connections.append({
                                    "type": out_node.type,
                                    "name": out_node.properties.get("name")
                                })
                    order_dict["steps"].append({
                        "index": step_idx,
                        "connections": linked_connections
                    })
                export_data["orders"].append(order_dict)

        return export_data