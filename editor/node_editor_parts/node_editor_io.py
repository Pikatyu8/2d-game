# editor/node_editor_parts/node_editor_io.py
import json
import os
import dearpygui.dearpygui as dpg
from config import TEMPLATES_FILE, resolve_json

class NodeEditorIOMixin:
    def load_preset_file(self, sender, app_data):
        filepath = dpg.get_value("preset_combo")
        if not filepath or not os.path.exists(filepath):
            return
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current_loaded_file_path = filepath
            self.import_json_to_graph(data)
            dpg.delete_item("properties_panel", children_only=True)
            print(f"[Успешно] Загружен физический файл пресета: {filepath}")
        except Exception as e:
            print(f"[Ошибка] Сбой разбора JSON в {filepath}: {e}")

    def save_preset_file(self, sender, app_data):
        if not self.current_loaded_file_path:
            print("[Экспорт] Ошибка: Не выбран целевой файл для сохранения.")
            return
            
        self.sync_with_dpg()
        data = self.export_graph_to_json()
        if data:
            try:
                with open(self.current_loaded_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                self.last_file_mod_time = os.path.getmtime(self.current_loaded_file_path)
                print(f"[Успешно] Изменения зафиксированы в файл: {self.current_loaded_file_path}")
            except Exception as e:
                print(f"[Ошибка] Сбой записи в {self.current_loaded_file_path}: {e}")

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
        
        raw_det = resolved_data.get("detection", {})
        raw_det_preset = preset_data.get("detection", {})
        raw_shape_preset = raw_det_preset.get("shape", {})
        
        raw_shape = raw_det.get("shape", {})
        det_shape_type = raw_shape.get("type", "rectangle")
        det_type = raw_det.get("type", "following")
        
        root_props = {
            "hp": preset_data.get("hp", 3),
            "body_template": preset_data.get("body", {}).get("template", "forms.rect"),
            "body_w": preset_data.get("body", {}).get("w", 30),
            "body_h": preset_data.get("body", {}).get("h", 50),
            "type_move": preset_data.get("movement_config", {}).get("type_move", "walking"),
            "speed": preset_data.get("movement_config", {}).get("speed", 1.2),
            "range_x": preset_data.get("movement_config", {}).get("range_x", 120),
            "stop_dist": preset_data.get("movement_config", {}).get("stop_dist", 60),
            "patrol_on_platform": preset_data.get("movement_config", {}).get("patrol_on_platform", False),
            "det_template": raw_det_preset.get("template", "detections.front_view"),
            "det_shape_template": raw_shape_preset.get("template", "forms.rect"),
            "det_shape_type": det_shape_type,
            "det_type": det_type,
            "det_w": raw_shape.get("w", 220),
            "det_h": raw_shape.get("h", 70),
            "det_r": raw_shape.get("r", 110),
            "det_offset_x": raw_det.get("offset_x", 0),
            "det_offset_y": raw_det.get("offset_y", -10),
            "det_angle": raw_det.get("angle", 0)
        }
        root_id = self.create_root_node(root_props)
        root_node = self.nodes_data[root_id]
        
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
                hb_node = self.nodes_data[hb_node_id]
                p_hb_in = list(hb_node.input_pins.keys())[0]
                
                link_id = dpg.add_node_link(p_hitboxes_out, p_hb_in, parent="editor_tag")
                self.links_data[link_id] = (p_hitboxes_out, p_hb_in)
                
        movement_nodes = []
        for mov in resolved_data.get("movements", []):
            mov_props = {
                "name": mov.get("name", "Movement"),
                "stop_dist": mov.get("stop_dist", 0)
            }
            mov_node_id = self.create_movement_node(mov_props)
            mov_node = self.nodes_data[mov_node_id]
            movement_nodes.append(mov_node)
            
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
                phase_node = self.nodes_data[phase_node_id]
                p_phase_in = list(phase_node.input_pins.keys())[0]
                
                link_id = dpg.add_node_link(p_phases_out, p_phase_in, parent="editor_tag")
                self.links_data[link_id] = (p_phases_out, p_phase_in)
                
        projectile_nodes = []
        for proj in resolved_data.get("projectiles", []):
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
            projectile_nodes.append(self.nodes_data[proj_node_id])

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
                "trig_shape_template": preset_shape.get("template", "forms.rect"),
                "trig_shape_type": seq.get("trigger_zone", {}).get("shape", {}).get("type", "rectangle"),
                "trig_w": seq.get("trigger_zone", {}).get("shape", {}).get("w", 90),
                "trig_h": seq.get("trigger_zone", {}).get("shape", {}).get("h", 50),
                "trig_r": seq.get("trigger_zone", {}).get("shape", {}).get("r", 45),
                "trig_offset_x": seq.get("trigger_zone", {}).get("offset_x", 10),
                "trig_offset_y": seq.get("trigger_zone", {}).get("offset_y", 0),
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

            p_seq_in = list(seq_node.input_pins.keys())[0]
            link_id = dpg.add_node_link(p_root_seqs, p_seq_in, parent="editor_tag")
            self.links_data[link_id] = (p_root_seqs, p_seq_in)
            
            steps_pins = seq_node.properties.get("steps_pins", [])
            for step_idx, step_pin_id in enumerate(steps_pins):
                step_data = seq_props["steps"][step_idx]
                stype = step_data.get("type", "attack")
                sidx = step_data.get("idx", 0)
                
                target_node = None
                if stype == "attack" and sidx < len(attack_nodes):
                    target_node = attack_nodes[sidx]
                elif stype == "movement" and sidx < len(movement_nodes):
                    target_node = movement_nodes[sidx]
                elif stype == "projectile" and sidx < len(projectile_nodes):
                    target_node = projectile_nodes[sidx]
                    
                if target_node:
                    p_act_in = list(target_node.input_pins.keys())[0]
                    link_id = dpg.add_node_link(step_pin_id, p_act_in, parent="editor_tag")
                    self.links_data[link_id] = (step_pin_id, p_act_in)

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
                "trigger_zone": {
                    "shape": {
                        "template": preset_shape.get("template", "forms.rect"),
                        "type": flow.get("trigger_zone", {}).get("shape", {}).get("type", "rectangle"),
                        "w": flow.get("trigger_zone", {}).get("shape", {}).get("w", 250),
                        "h": flow.get("trigger_zone", {}).get("shape", {}).get("h", 80),
                        "r": flow.get("trigger_zone", {}).get("shape", {}).get("r", 80)
                    },
                    "offset_x": flow.get("trigger_zone", {}).get("offset_x", 0),
                    "offset_y": flow.get("trigger_zone", {}).get("offset_y", 0),
                    "type": flow.get("trigger_zone", {}).get("type", "following"),
                    "hold_time": flow.get("trigger_zone", {}).get("hold_time", 0),
                    "consecutive_limit": flow.get("trigger_zone", {}).get("consecutive_limit", 3),
                    "accumulate_hold": flow.get("trigger_zone", {}).get("accumulate_hold", True)
                },
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
            
            p_flow_parent = list(flow_node.input_pins.keys())[0]
            link_id = dpg.add_node_link(p_root_flows, p_flow_parent, parent="editor_tag")
            self.links_data[link_id] = (p_root_flows, p_flow_parent)
            
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
                "trig_shape_template": preset_shape.get("template", "forms.rect"),
                "trig_shape_type": order_data.get("trigger_zone", {}).get("shape", {}).get("type", "rectangle"),
                "trig_w": order_data.get("trigger_zone", {}).get("shape", {}).get("w", 150),
                "trig_h": order_data.get("trigger_zone", {}).get("shape", {}).get("h", 60),
                "trig_r": order_data.get("trigger_zone", {}).get("shape", {}).get("r", 75),
                "trig_offset_x": order_data.get("trigger_zone", {}).get("offset_x", 0),
                "trig_offset_y": order_data.get("trigger_zone", {}).get("offset_y", 0),
                "trig_type": order_data.get("trigger_zone", {}).get("type", "following"),
                "trig_hold_time": order_data.get("trigger_zone", {}).get("hold_time", 0),
                "trig_consecutive_limit": order_data.get("trigger_zone", {}).get("consecutive_limit", 3),
                "trig_accumulate_hold": order_data.get("trigger_zone", {}).get("accumulate_hold", True)
            }
            order_node_id = self.create_order_node(order_props)
            order_node = self.nodes_data[order_node_id]
            
            if "pos" in order_data:
                dpg.set_item_pos(order_node_id, order_data["pos"])
                
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
            
        det_shape_type = root_node.properties.get("det_shape_type", "rectangle")
        det_template = "forms.circle" if det_shape_type == "circle" else "forms.rect"
        det_shape = {
            "template": det_template,
            "type": det_shape_type
        }
        if det_shape_type == "circle":
            det_shape["r"] = root_node.properties.get("det_r", 110)
        else:
            det_shape["w"] = root_node.properties.get("det_w", 220)
            det_shape["h"] = root_node.properties.get("det_h", 70)

        export_data = {
            "hp": root_node.properties.get("hp", 3),
            "body": {
                "template": root_node.properties.get("body_template", "forms.rect"),
                "w": root_node.properties.get("body_w", 30),
                "h": root_node.properties.get("body_h", 50)
            },
            "movement_config": {
                "type_move": root_node.properties.get("type_move", "walking"),
                "speed": root_node.properties.get("speed", 1.2),
                "range_x": root_node.properties.get("range_x", 120),
                "stop_dist": root_node.properties.get("stop_dist", 60),
                "patrol_on_platform": root_node.properties.get("patrol_on_platform", False)
            },
            "detection": {
                "template": root_node.properties.get("det_template", "detections.front_view"),
                "shape": det_shape,
                "offset_x": root_node.properties.get("det_offset_x", 0),
                "offset_y": root_node.properties.get("det_offset_y", -10),
                "angle": root_node.properties.get("det_angle", 0)
            },
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

        sorted_flows = sorted(
            [self.nodes_data[nid] for nid in connected_flow_ids if self.nodes_data[nid].type == "Flow"],
            key=lambda x: dpg.get_item_pos(x.id)[1]
        )
        sorted_sequences = sorted(
            [self.nodes_data[nid] for nid in connected_seq_ids if self.nodes_data[nid].type == "Sequence"],
            key=lambda x: dpg.get_item_pos(x.id)[1]
        )

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
                hb_template = "forms.circle" if hb_shape_type == "circle" else "forms.rect"
                hb_shape = {
                    "template": hb_template,
                    "type": hb_shape_type
                }
                if hb_shape_type == "circle":
                    hb_shape["r"] = hb.properties.get("r", 25)
                else:
                    hb_shape["w"] = hb.properties.get("w", 50)
                    hb_shape["h"] = hb.properties.get("h", 40)

                hb_dict = {
                    "shape": hb_shape,
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
                    vbox = {
                        "type": vis_type,
                        "offset_x": hb.properties.get("vis_offset_x", 0),
                        "offset_y": hb.properties.get("vis_offset_y", 0)
                    }
                    if vis_type == "circle":
                        vbox["r"] = hb.properties.get("vis_r", 25)
                    else:
                        vbox["w"] = hb.properties.get("vis_w", 50)
                        vbox["h"] = hb.properties.get("vis_h", 40)
                    hb_dict["visual_box"] = vbox
                    
                atk_dict["shapes"].append(hb_dict)
            export_data["attacks"].append(atk_dict)

        for mov_node in sorted_movements:
            mov_dict = {
                "name": mov_node.properties.get("name", "Movement"),
                "stop_dist": mov_node.properties.get("stop_dist", 0),
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
                phase_dict = {
                    "direction": ph.properties.get("direction", "forward"),
                    "curve": ph.properties.get("curve", "fade_out"),
                    "force_x": ph.properties.get("force_x", 8.0),
                    "force_y": ph.properties.get("force_y", 0.0),
                    "delay": ph.properties.get("delay", 0),
                    "duration": ph.properties.get("duration", 15)
                }
                mov_dict["phases"].append(phase_dict)
            export_data["movements"].append(mov_dict)

        for proj_node in sorted_projectiles:
            proj_dict = {
                "name": proj_node.properties.get("name", "Projectile"),
                "speed": proj_node.properties.get("speed", 10.0),
                "angle": proj_node.properties.get("angle", 0.0),
                "gravity": proj_node.properties.get("gravity", 0.0),
                "damage": proj_node.properties.get("damage", 1),
                "radius": proj_node.properties.get("radius", 8),
                "aim_at_player": proj_node.properties.get("aim_at_player", False),
                "homing": proj_node.properties.get("homing", 0.0),
                "shoot_cooldown": proj_node.properties.get("shoot_cooldown", 30)
            }
            export_data["projectiles"].append(proj_dict)

        for seq_node in sorted_sequences:
            seq_shape_type = seq_node.properties.get("trig_shape_type", "rectangle")
            seq_template = "forms.circle" if seq_shape_type == "circle" else "forms.rect"
            seq_shape = {
                "template": seq_template,
                "type": seq_shape_type
            }
            if seq_shape_type == "circle":
                seq_shape["r"] = seq_node.properties.get("trig_r", 45)
            else:
                seq_shape["w"] = seq_node.properties.get("trig_w", 90)
                seq_shape["h"] = seq_node.properties.get("trig_h", 50)

            seq_dict = {
                "name": seq_node.properties.get("name", "Sequence"),
                "chance": seq_node.properties.get("chance", 0.5),
                "cooldown": seq_node.properties.get("cooldown", 120),
                "post_cooldown": seq_node.properties.get("post_cooldown", 30),
                "trigger_zone": {
                    "shape": seq_shape,
                    "offset_x": seq_node.properties.get("trig_offset_x", 10),
                    "offset_y": seq_node.properties.get("trig_offset_y", 0),
                    "type": seq_node.properties.get("trig_type", "following"),
                    "hold_time": seq_node.properties.get("trig_hold_time", 0),
                    "consecutive_limit": seq_node.properties.get("trig_consecutive_limit", 3),
                    "accumulate_hold": seq_node.properties.get("trig_accumulate_hold", True)
                },
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

        for flow_node in sorted_flows:
            flow_shape_type = flow_node.properties.get("trig_shape_type", "rectangle")
            flow_template = "forms.circle" if flow_shape_type == "circle" else "forms.rect"
            flow_shape = {
                "template": flow_template,
                "type": flow_shape_type
            }
            if flow_shape_type == "circle":
                flow_shape["r"] = flow_node.properties.get("trig_r", 80)
            else:
                flow_shape["w"] = flow_node.properties.get("trig_w", 250)
                flow_shape["h"] = flow_node.properties.get("trig_h", 80)

            flow_dict = {
                "name": flow_node.properties.get("name", "Flow"),
                "chance": flow_node.properties.get("chance", 0.5),
                "cooldown": flow_node.properties.get("cooldown", 180),
                "post_cooldown": flow_node.properties.get("post_cooldown", 30),
                "trigger_zone": {
                    "shape": flow_shape,
                    "offset_x": flow_node.properties.get("trig_offset_x", 0),
                    "offset_y": flow_node.properties.get("trig_offset_y", 0),
                    "type": flow_node.properties.get("trig_type", "following"),
                    "hold_time": flow_node.properties.get("trig_hold_time", 0),
                    "consecutive_limit": flow_node.properties.get("trig_consecutive_limit", 3),
                    "accumulate_hold": flow_node.properties.get("trig_accumulate_hold", True)
                },
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

        for node_id, node in self.nodes_data.items():
            if node.type == "Order":
                pos = dpg.get_item_pos(node_id)
                order_shape_type = node.properties.get("trig_shape_type", "rectangle")
                order_template = "forms.circle" if order_shape_type == "circle" else "forms.rect"
                order_shape = {
                    "template": order_template,
                    "type": order_shape_type
                }
                if order_shape_type == "circle":
                    order_shape["r"] = node.properties.get("trig_r", 75)
                else:
                    order_shape["w"] = node.properties.get("trig_w", 150)
                    order_shape["h"] = node.properties.get("trig_h", 60)

                order_dict = {
                    "name": node.properties.get("name", "Order"),
                    "pos": pos,
                    "chance": node.properties.get("chance", 1.0),
                    "cooldown": node.properties.get("cooldown", 120),
                    "post_cooldown": node.properties.get("post_cooldown", 30),
                    "trigger_zone": {
                        "shape": order_shape,
                        "offset_x": node.properties.get("trig_offset_x", 0),
                        "offset_y": node.properties.get("trig_offset_y", 0),
                        "type": node.properties.get("trig_type", "following"),
                        "hold_time": node.properties.get("trig_hold_time", 0),
                        "consecutive_limit": node.properties.get("trig_consecutive_limit", 3),
                        "accumulate_hold": node.properties.get("trig_accumulate_hold", True)
                    },
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