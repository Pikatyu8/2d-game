# editor/node_editor_parts/node_editor_io_import.py
import json
import os
import dearpygui.dearpygui as dpg
from config import TEMPLATES_FILE, resolve_json

class NodeEditorIOImportMixin:
    def import_json_to_graph(self, preset_data):
        dpg.clear_selected_nodes("editor_tag")
        dpg.clear_selected_links("editor_tag")
        dpg.delete_item("editor_tag", children_only=True)

        self.nodes_data.clear()
        self.links_data.clear()
        self.pins_registry.clear()
        self.pin_to_node.clear()

        templates = {}
        if os.path.exists(TEMPLATES_FILE):
            try:
                with open(TEMPLATES_FILE, "r", encoding="utf-8") as tf:
                    templates = json.load(tf)
            except Exception as e:
                print(f"[Node Editor] Error loading templates: {e}")

        resolved_data = resolve_json(preset_data, templates)

        # 1. Свойства Root-ноды
        body_cfg = resolved_data.get("body", {})
        body_w = body_cfg.get("w", 30)
        body_h = body_cfg.get("h", 50)

        root_props = {
            "hp": preset_data.get("hp", 3),
            "body_w": body_w,
            "body_h": body_h,
            "type_move": preset_data.get("movement_config", {}).get("type_move", "walking"),
            "speed": preset_data.get("movement_config", {}).get("speed", 1.2),
            "range_x": preset_data.get("movement_config", {}).get("range_x", 120),
            "stop_dist": preset_data.get("movement_config", {}).get("stop_dist", 60),
            "patrol_on_platform": preset_data.get("movement_config", {}).get("patrol_on_platform", False),
            "name": preset_data.get("name", "Enemy")
        }

        root_id = self.create_root_node(root_props)
        root_node = self.nodes_data[root_id]

        # 2. Восстановление хитбоксов тела противника (Root -> Body)
        body_shapes = preset_data.get("body_shapes", [])
        if not body_shapes and "body" in preset_data:
            b_cfg = preset_data["body"]
            body_shapes = [{
                "shape": {"template": b_cfg.get("template", "forms.rect"), "type": "rectangle", "w": b_cfg.get("w", 30), "h": b_cfg.get("h", 50)},
                "offset_x": 0, "offset_y": 0, "angle": 0
            }]

        for b_shape in body_shapes:
            geom = b_shape.get("shape", {})
            hb_id = self.create_hitbox_node({
                "shape_template": geom.get("template", "forms.rect"),
                "shape_type": geom.get("type", "rectangle"),
                "w": geom.get("w", 30), "h": geom.get("h", 50), "r": geom.get("r", 25),
                "offset_x": b_shape.get("offset_x", 0), "offset_y": b_shape.get("offset_y", 0),
                "angle": b_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": 0
            })
            p_out = root_node.properties["body_pin"]
            p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
            link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
            self.links_data[link_id] = (p_out, p_in)

        # 3. Восстановление хитбоксов детекции / зрения (Root -> Detection)
        det_shapes = preset_data.get("detection_shapes", [])
        if not det_shapes and "detection" in preset_data:
            det = preset_data["detection"]
            geom = det.get("shape", {})
            resolved_det = resolved_data.get("detection", {})
            det_type = resolved_det.get("type", "following")

            det_shapes = [{
                "shape": {"template": geom.get("template", "forms.rect"), "type": geom.get("type", "rectangle" if "w" in geom else "circle"), "w": geom.get("w", 220), "h": geom.get("h", 70), "r": geom.get("r", 110)},
                "offset_x": det.get("offset_x", 0), "offset_y": det.get("offset_y", -10),
                "angle": det.get("angle", 0), "type": det_type
            }]

        for d_shape in det_shapes:
            geom = d_shape.get("shape", {})
            hb_id = self.create_hitbox_node({
                "shape_template": geom.get("template", "forms.rect"),
                "shape_type": geom.get("type", "rectangle"),
                "w": geom.get("w", 220), "h": geom.get("h", 70), "r": geom.get("r", 110),
                "offset_x": d_shape.get("offset_x", 0), "offset_y": d_shape.get("offset_y", -10),
                "angle": d_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": 0,
                "sprite_dir": d_shape.get("type", "following")
            })
            p_out = root_node.properties["det_pin"]
            p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
            link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
            self.links_data[link_id] = (p_out, p_in)

        # 3.5 Восстановление хитбоксов остановки преследования (Root -> Stopping)
        stop_shapes = preset_data.get("stop_shapes", [])
        if not stop_shapes:
            old_stop_dist = preset_data.get("movement_config", {}).get("stop_dist", 60)
            stop_shapes = [{
                "shape": {"template": "forms.rect", "type": "rectangle", "w": old_stop_dist * 2, "h": body_h + 40},
                "offset_x": -old_stop_dist + body_w // 2, "offset_y": -20,
                "angle": 0, "type": "stationary"
            }]

        for s_shape in stop_shapes:
            geom = s_shape.get("shape", {})
            hb_id = self.create_hitbox_node({
                "shape_template": geom.get("template", "forms.rect"),
                "shape_type": geom.get("type", "rectangle"),
                "w": geom.get("w", body_w * 2), "h": geom.get("h", body_h + 40), "r": geom.get("r", 30),
                "offset_x": s_shape.get("offset_x", 0), "offset_y": s_shape.get("offset_y", 0),
                "angle": s_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": 0,
                "sprite_dir": s_shape.get("type", "stationary")
            })
            p_out = root_node.properties["stop_pin"]
            p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
            link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
            self.links_data[link_id] = (p_out, p_in)

        # 4. Атаки и их классические хитбоксы
        attack_nodes = []
        for atk_idx, atk in enumerate(resolved_data.get("attacks", [])):
            atk_props = {
                "name": atk.get("name", "Attack"),
                "cooldown": atk.get("cooldown", 45),
                "windup": atk.get("windup", 35)
            }
            atk_node_id = self.create_attack_node(atk_props)
            atk_node = self.nodes_data[atk_node_id]
            attack_nodes.append(atk_node)

            preset_atk_list = preset_data.get("attacks", [])
            preset_atk = preset_atk_list[atk_idx] if atk_idx < len(preset_atk_list) else {}
            preset_shapes = preset_atk.get("shapes", [])

            p_hitboxes_out = list(atk_node.output_pins.keys())[0]
            for shape_idx, shape in enumerate(atk.get("shapes", [])):
                preset_shape_item = preset_shapes[shape_idx] if shape_idx < len(preset_shapes) else {}
                preset_shape_geom = preset_shape_item.get("shape", {})

                hb_props = {
                    "shape_template": preset_shape_geom.get("template", "forms.rect"),
                    "shape_type": shape.get("shape", {}).get("type", "rectangle"),
                    "w": shape.get("shape", {}).get("w", 50),
                    "h": shape.get("shape", {}).get("h", 40),
                    "r": shape.get("shape", {}).get("r", 25),
                    "offset_x": shape.get("offset_x", 10),
                    "offset_y": shape.get("offset_y", 0),
                    "angle": shape.get("angle", 0),
                    "delay": shape.get("delay", 0),
                    "duration": shape.get("duration", 10),
                    "damage": shape.get("damage", 1),
                    "kb_angle_hit": shape.get("kb_angle_hit", 0),
                    "kb_force_hit": shape.get("kb_force_hit", 12.0),
                    "kb_angle_parry": shape.get("kb_angle_parry", 0),
                    "kb_force_parry": shape.get("kb_force_parry", 6.0),
                    "sprite_dir": shape.get("sprite_dir", "forward")
                }
                if "visual_box" in shape:
                    vbox = shape["visual_box"]
                    hb_props.update({
                        "vis_enabled": True,
                        "vis_type": vbox.get("type", "rectangle"),
                        "vis_w": vbox.get("w", 50),
                        "vis_h": vbox.get("h", 40),
                        "vis_r": vbox.get("r", 25),
                        "vis_offset_x": vbox.get("offset_x", 0),
                        "vis_offset_y": vbox.get("offset_y", 0)
                    })
                hb_node_id = self.create_hitbox_node(hb_props)
                p_hb_in = list(self.nodes_data[hb_node_id].input_pins.keys())[0]

                link_id = dpg.add_node_link(p_hitboxes_out, p_hb_in, parent="editor_tag")
                self.links_data[link_id] = (p_hitboxes_out, p_hb_in)

        # 5. Перемещения и зоны остановки действия (Movement -> Stop Area Hitboxes)
        movement_nodes = []
        for mov_idx, mov in enumerate(resolved_data.get("movements", [])):
            mov_props = {
                "name": mov.get("name", "Movement"),
                "stop_dist": mov.get("stop_dist", 0)
            }
            mov_node_id = self.create_movement_node(mov_props)
            mov_node = self.nodes_data[mov_node_id]
            movement_nodes.append(mov_node)

            # Восстанавливаем фазы перемещения
            p_phases_out = list(mov_node.output_pins.keys())[0]
            for phase in mov.get("phases", []):
                phase_props = {
                    "direction": phase.get("direction", "forward"),
                    "curve": phase.get("curve", "fade_out"),
                    "force_x": phase.get("force_x", 8.0),
                    "force_y": phase.get("force_y", 0.0),
                    "delay": phase.get("delay", 0),
                    "duration": phase.get("duration", 15)
                }
                phase_node_id = self.create_phase_node(phase_props)
                p_phase_in = list(self.nodes_data[phase_node_id].input_pins.keys())[0]
                link_id = dpg.add_node_link(p_phases_out, p_phase_in, parent="editor_tag")
                self.links_data[link_id] = (p_phases_out, p_phase_in)

            # Восстанавливаем зоны остановки
            preset_mov_list = preset_data.get("movements", [])
            preset_mov = preset_mov_list[mov_idx] if mov_idx < len(preset_mov_list) else {}
            stop_shapes_mov_list = preset_mov.get("stop_shapes", [])
            if not stop_shapes_mov_list and preset_mov.get("stop_dist", 0) > 0:
                stop_shapes_mov_list = [{
                    "shape": {"template": "forms.rect", "type": "rectangle", "w": preset_mov["stop_dist"] * 2, "h": 60},
                    "offset_x": 0, "offset_y": 0, "angle": 0
                }]

            for s_shape in stop_shapes_mov_list:
                geom = s_shape.get("shape", {})
                hb_id = self.create_hitbox_node({
                    "shape_template": geom.get("template", "forms.rect"),
                    "shape_type": geom.get("type", "rectangle"),
                    "w": geom.get("w", 120), "h": geom.get("h", 60), "r": geom.get("r", 30),
                    "offset_x": s_shape.get("offset_x", 0), "offset_y": s_shape.get("offset_y", 0),
                    "angle": s_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": 0
                })
                p_out = mov_node.properties["stop_pin"]
                p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
                link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
                self.links_data[link_id] = (p_out, p_in)

        # 6. Снаряды и их хитбоксы (Projectile -> Hitboxes)
        projectile_nodes = []
        for proj_idx, proj in enumerate(resolved_data.get("projectiles", [])):
            proj_props = {
                "name": proj.get("name", "Projectile"),
                "speed": proj.get("speed", 10.0),
                "angle": proj.get("angle", 0.0),
                "gravity": proj.get("gravity", 0.0),
                "damage": proj.get("damage", 1),
                "radius": proj.get("radius", 8),
                "aim_at_player": proj.get("aim_at_player", False),
                "homing": proj.get("homing", 0.0),
                "shoot_cooldown": proj.get("shoot_cooldown", 30)
            }
            proj_node_id = self.create_projectile_node(proj_props)
            proj_node = self.nodes_data[proj_node_id]
            projectile_nodes.append(proj_node)

            preset_proj_list = preset_data.get("projectiles", [])
            preset_proj = preset_proj_list[proj_idx] if proj_idx < len(preset_proj_list) else {}
            proj_shapes = preset_proj.get("shapes", [])
            if not proj_shapes:
                proj_shapes = [{
                    "shape": {"template": "forms.circle", "type": "circle", "r": proj_props["radius"]},
                    "offset_x": 0, "offset_y": 0, "angle": 0
                }]

            for p_shape in proj_shapes:
                geom = p_shape.get("shape", {})
                hb_id = self.create_hitbox_node({
                    "shape_template": geom.get("template", "forms.circle"),
                    "shape_type": geom.get("type", "circle"),
                    "w": geom.get("w", 16), "h": geom.get("h", 16), "r": geom.get("r", 8),
                    "offset_x": p_shape.get("offset_x", 0), "offset_y": p_shape.get("offset_y", 0),
                    "angle": p_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": proj_props["damage"]
                })
                p_out = proj_node.properties["hitbox_pin"]
                p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
                link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
                self.links_data[link_id] = (p_out, p_in)

        # 7. Последовательности и их триггерные хитбоксы (Sequence -> Trigger shapes)
        sequence_nodes = []
        p_root_seqs = list(root_node.output_pins.keys())[1]
        for seq_idx, seq in enumerate(resolved_data.get("sequences", [])):
            preset_seq_list = preset_data.get("sequences", [])
            preset_seq = preset_seq_list[seq_idx] if seq_idx < len(preset_seq_list) else {}
            preset_tz = preset_seq.get("trigger_zone", {})
            preset_shape = preset_tz.get("shape", {})

            seq_props = {
                "name": seq.get("name", "Sequence"),
                "chance": seq.get("chance", 0.5),
                "cooldown": seq.get("cooldown", 120),
                "post_cooldown": seq.get("post_cooldown", 30),
                "trig_type": seq.get("trigger_zone", {}).get("type", "following"),
                "trig_hold_time": seq.get("trigger_zone", {}).get("hold_time", 0),
                "trig_consecutive_limit": seq.get("trigger_zone", {}).get("consecutive_limit", 3),
                "trig_accumulate_hold": seq.get("trigger_zone", {}).get("accumulate_hold", True),
                "steps": seq.get("steps", [])
            }
            if "color" in seq:
                seq_props["color"] = seq["color"]
                seq_props["color_hex"] = '#{:02x}{:02x}{:02x}'.format(seq["color"][0], seq["color"][1], seq["color"][2])
            else:
                seq_props["color_hex"] = "#ff0000"

            seq_node_id = self.create_sequence_node(seq_props)
            seq_node = self.nodes_data[seq_node_id]
            sequence_nodes.append(seq_node)

            # Соединяем Root -> Sequence
            p_seq_in = list(seq_node.input_pins.keys())[0]
            link_id = dpg.add_node_link(p_root_seqs, p_seq_in, parent="editor_tag")
            self.links_data[link_id] = (p_root_seqs, p_seq_in)

            # Восстанавливаем триггерные хитбоксы последовательности
            trig_shapes = preset_seq.get("trigger_shapes", [])
            if not trig_shapes and preset_tz:
                trig_shapes = [{
                    "shape": {"template": preset_shape.get("template", "forms.rect"), "type": preset_shape.get("type", "rectangle" if "w" in preset_shape else "circle"), "w": preset_shape.get("w", 90), "h": preset_shape.get("h", 50), "r": preset_shape.get("r", 45)},
                    "offset_x": preset_tz.get("offset_x", 10), "offset_y": preset_tz.get("offset_y", 0),
                    "angle": preset_tz.get("angle", 0), "type": preset_tz.get("type", "following")
                }]

            for t_shape in trig_shapes:
                geom = t_shape.get("shape", {})
                hb_id = self.create_hitbox_node({
                    "shape_template": geom.get("template", "forms.rect"),
                    "shape_type": geom.get("type", "rectangle"),
                    "w": geom.get("w", 90), "h": geom.get("h", 50), "r": geom.get("r", 45),
                    "offset_x": t_shape.get("offset_x", 10), "offset_y": t_shape.get("offset_y", 0),
                    "angle": t_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": 0,
                    "sprite_dir": t_shape.get("type", "following")
                })
                p_out = seq_node.properties["trig_pin"]
                p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
                link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
                self.links_data[link_id] = (p_out, p_in)

            # Соединяем шаги последовательности с атаками/перемещениями
            steps_pins = seq_node.properties.get("steps_pins", [])
            for step_idx, step_pin_id in enumerate(steps_pins):
                step_data = seq_props["steps"][step_idx]
                is_attack = step_data.get("type", "attack") == "attack"
                is_movement = step_data.get("type") == "movement"
                is_projectile = step_data.get("type") == "projectile"

                sidx = step_data.get("idx", 0)
                target_node = None
                if is_attack and sidx < len(attack_nodes):
                    target_node = attack_nodes[sidx]
                elif is_movement and sidx < len(movement_nodes):
                    target_node = movement_nodes[sidx]
                elif is_projectile and sidx < len(projectile_nodes):
                    target_node = projectile_nodes[sidx]

                if target_node:
                    p_act_in = list(target_node.input_pins.keys())[0]
                    link_id = dpg.add_node_link(step_pin_id, p_act_in, parent="editor_tag")
                    self.links_data[link_id] = (step_pin_id, p_act_in)

        # 8. Потоки поведения и их триггерные хитбоксы (Flow -> Trigger shapes)
        flow_nodes = []
        p_root_flows = list(root_node.output_pins.keys())[0]
        for flow_idx, flow in enumerate(resolved_data.get("flows", [])):
            preset_flow_list = preset_data.get("flows", [])
            preset_flow = preset_flow_list[flow_idx] if flow_idx < len(preset_flow_list) else {}
            preset_tz = preset_flow.get("trigger_zone", {})
            preset_shape = preset_tz.get("shape", {})

            flow_props = {
                "name": flow.get("name", "Flow"),
                "chance": flow.get("chance", 0.5),
                "cooldown": flow.get("cooldown", 180),
                "post_cooldown": flow.get("post_cooldown", 30),
                "trig_type": flow.get("trigger_zone", {}).get("type", "following"),
                "trig_hold_time": flow.get("trigger_zone", {}).get("hold_time", 0),
                "trig_consecutive_limit": flow.get("trigger_zone", {}).get("consecutive_limit", 3),
                "trig_accumulate_hold": flow.get("trigger_zone", {}).get("accumulate_hold", True),
                "steps": flow.get("steps", [])
            }
            if "color" in flow:
                flow_props["color"] = flow["color"]
                flow_props["color_hex"] = '#{:02x}{:02x}{:02x}'.format(flow["color"][0], flow["color"][1], flow["color"][2])
            else:
                flow_props["color_hex"] = "#ff0000"

            flow_node_id = self.create_flow_node(flow_props)
            flow_node = self.nodes_data[flow_node_id]
            flow_nodes.append(flow_node)

            # Соединяем Root -> Flow
            p_flow_parent = list(flow_node.input_pins.keys())[0]
            link_id = dpg.add_node_link(p_root_flows, p_flow_parent, parent="editor_tag")
            self.links_data[link_id] = (p_root_flows, p_flow_parent)

            # Восстанавливаем триггерные хитбоксы потока
            trig_shapes = preset_flow.get("trigger_shapes", [])
            if not trig_shapes and preset_tz:
                trig_shapes = [{
                    "shape": {"template": preset_shape.get("template", "forms.rect"), "type": preset_shape.get("type", "rectangle" if "w" in preset_shape else "circle"), "w": preset_shape.get("w", 250), "h": preset_shape.get("h", 80), "r": preset_shape.get("r", 80)},
                    "offset_x": preset_tz.get("offset_x", 0), "offset_y": preset_tz.get("offset_y", 0),
                    "angle": preset_tz.get("angle", 0), "type": preset_tz.get("type", "following")
                }]

            for t_shape in trig_shapes:
                geom = t_shape.get("shape", {})
                hb_id = self.create_hitbox_node({
                    "shape_template": geom.get("template", "forms.rect"),
                    "shape_type": geom.get("type", "rectangle"),
                    "w": geom.get("w", 250), "h": geom.get("h", 80), "r": geom.get("r", 80),
                    "offset_x": t_shape.get("offset_x", 0), "offset_y": t_shape.get("offset_y", 0),
                    "angle": t_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": 0,
                    "sprite_dir": t_shape.get("type", "following")
                })
                p_out = flow_node.properties["trig_pin"]
                p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
                link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
                self.links_data[link_id] = (p_out, p_in)

            # Соединяем шаги поведения с последовательностями
            flow_steps_pins = flow_node.properties.get("steps_pins", [])
            for step_idx, step_pin_id in enumerate(flow_steps_pins):
                step_data = flow_props["steps"][step_idx]
                is_random = step_data.get("is_random", False)

                if is_random:
                    pool = step_data.get("seq_pool", [])
                    for sidx in pool:
                        if sidx < len(sequence_nodes):
                            p_seq_trigger = list(sequence_nodes[sidx].input_pins.keys())[0]
                            link_id = dpg.add_node_link(step_pin_id, p_seq_trigger, parent="editor_tag")
                            self.links_data[link_id] = (step_pin_id, p_seq_trigger)
                else:
                    sidx = step_data.get("seq_idx", 0)
                    if sidx < len(sequence_nodes):
                        p_seq_trigger = list(sequence_nodes[sidx].input_pins.keys())[0]
                        link_id = dpg.add_node_link(step_pin_id, p_seq_trigger, parent="editor_tag")
                        self.links_data[link_id] = (step_pin_id, p_seq_trigger)

        # 9. Цепочки Порядка и их триггерные хитбоксы (Order -> Trigger shapes)
        for order_idx, order_data in enumerate(resolved_data.get("orders", [])):
            preset_order_list = preset_data.get("orders", [])
            preset_order = preset_order_list[order_idx] if order_idx < len(preset_order_list) else {}
            preset_tz = preset_order.get("trigger_zone", {})
            preset_shape = preset_tz.get("shape", {})

            order_props = {
                "name": order_data.get("name", "Order"),
                "chance": order_data.get("chance", 1.0),
                "cooldown": order_data.get("cooldown", 120),
                "post_cooldown": order_data.get("post_cooldown", 30),
                "trig_type": order_data.get("trigger_zone", {}).get("type", "following"),
                "trig_hold_time": order_data.get("trigger_zone", {}).get("hold_time", 0),
                "trig_consecutive_limit": order_data.get("trigger_zone", {}).get("consecutive_limit", 3),
                "trig_accumulate_hold": order_data.get("trigger_zone", {}).get("accumulate_hold", True)
            }
            order_node_id = self.create_order_node(order_props)
            order_node = self.nodes_data[order_node_id]

            if "pos" in order_data:
                dpg.set_item_pos(order_node_id, order_data["pos"])

            # Восстанавливаем триггерные хитбоксы порядка
            trig_shapes = preset_order.get("trigger_shapes", [])
            if not trig_shapes and preset_tz:
                trig_shapes = [{
                    "shape": {"template": preset_shape.get("template", "forms.rect"), "type": preset_shape.get("type", "rectangle" if "w" in preset_shape else "circle"), "w": preset_shape.get("w", 150), "h": preset_shape.get("h", 60), "r": preset_shape.get("r", 75)},
                    "offset_x": preset_tz.get("offset_x", 0), "offset_y": preset_tz.get("offset_y", 0),
                    "angle": preset_tz.get("angle", 0), "type": preset_tz.get("type", "following")
                }]

            for t_shape in trig_shapes:
                geom = t_shape.get("shape", {})
                hb_id = self.create_hitbox_node({
                    "shape_template": geom.get("template", "forms.rect"),
                    "shape_type": geom.get("type", "rectangle"),
                    "w": geom.get("w", 150), "h": geom.get("h", 60), "r": geom.get("r", 75),
                    "offset_x": t_shape.get("offset_x", 0), "offset_y": t_shape.get("offset_y", 0),
                    "angle": t_shape.get("angle", 0), "delay": 0, "duration": 9999, "damage": 0,
                    "sprite_dir": t_shape.get("type", "following")
                })
                p_out = order_node.properties["trig_pin"]
                p_in = list(self.nodes_data[hb_id].input_pins.keys())[0]
                link_id = dpg.add_node_link(p_out, p_in, parent="editor_tag")
                self.links_data[link_id] = (p_out, p_in)

            # Восстанавливаем связи шагов
            for step_item in order_data.get("steps", []):
                self.add_order_step(order_node_id)
                step_pins = order_node.properties.get("steps_pins", [])
                if step_pins:
                    target_pin_in = step_pins[-1]

                    for conn in step_item.get("connections", []):
                        conn_type = conn.get("type")
                        conn_name = conn.get("name")

                        for match_node in self.nodes_data.values():
                            if match_node.type == conn_type and match_node.properties.get("name") == conn_name:
                                order_pin_out = match_node.properties.get("order_pin")
                                if order_pin_out:
                                    link_id = dpg.add_node_link(order_pin_out, target_pin_in, parent="editor_tag")
                                    self.links_data[link_id] = (order_pin_out, target_pin_in)

        self.auto_arrange()
        self.rebuild_all_order_buttons()