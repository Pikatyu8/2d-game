# editor/node_editor_parts/node_editor_inspector.py
import dearpygui.dearpygui as dpg

def safe_int(val, default=0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        if val.startswith("$"):
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default
    return default

def safe_float(val, default=0.0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        if val.startswith("$"):
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return default

class NodeEditorInspectorMixin:
    def update_property(self, sender, app_data, user_data):
        node_id, prop_key = user_data
        self.nodes_data[node_id].properties[prop_key] = app_data
        if prop_key == "name" and self.nodes_data[node_id].type in ("Flow", "Sequence", "Attack", "Movement", "Projectile", "Order"):
            dpg.configure_item(node_id, label=f"{self.nodes_data[node_id].type}: {app_data}")

    def update_flow_color_hex(self, sender, app_data, user_data):
        node_id, prop_key = user_data
        self.nodes_data[node_id].properties[prop_key] = app_data
        hex_str = app_data.strip().lstrip('#')
        if len(hex_str) == 6:
            try:
                r = int(hex_str[0:2], 16)
                g = int(hex_str[2:4], 16)
                b = int(hex_str[4:6], 16)
                self.nodes_data[node_id].properties["color"] = [r, g, b]
            except ValueError:
                pass

    def update_step_delay(self, sender, app_data, user_data):
        node_id, pin_id = user_data
        self.nodes_data[node_id].output_pins[pin_id].properties["delay"] = app_data

    def update_flow_step_delay(self, sender, app_data, user_data):
        node_id, pin_id = user_data
        self.nodes_data[node_id].output_pins[pin_id].properties["delay"] = app_data

    def update_flow_step_random(self, sender, app_data, user_data):
        node_id, pin_id = user_data
        self.nodes_data[node_id].output_pins[pin_id].properties["is_random"] = app_data

    def add_flow_step_pin(self, sender, app_data, user_data):
        node_id = user_data
        self.add_flow_step_pin_ui(node_id)
        self.rebuild_inspector(node_id)

    def add_sequence_step_pin(self, sender, app_data, user_data):
        node_id = user_data
        self.add_sequence_step_pin_ui(node_id)
        self.rebuild_inspector(node_id)

    def link_callback(self, sender, app_data):
        pin_1, pin_2 = app_data
        p1 = self.pins_registry.get(pin_1)
        p2 = self.pins_registry.get(pin_2)

        if not p1 or not p2:
            return

        if p1["type"] == p2["type"] and p1["direction"] != p2["direction"]:
            pin_out = pin_1 if p1["direction"] == "Output" else pin_2
            pin_in = pin_2 if p1["direction"] == "Output" else pin_1

            if p1["type"] != "Order":
                for lid, (old_out, old_in) in list(self.links_data.items()):
                    if old_in == pin_in:
                        if dpg.does_item_exist(lid):
                            dpg.delete_item(lid)
                        self.links_data.pop(lid, None)

            link_id = dpg.add_node_link(pin_out, pin_in, parent=sender)
            self.links_data[link_id] = (pin_out, pin_in)
        else:
            print(f"[Валидация] Соединение заблокировано: {p1['type']} ({p1['direction']}) -> {p2['type']} ({p2['direction']})")

    def delink_callback(self, sender, app_data):
        if app_data in self.links_data:
            del self.links_data[app_data]
        dpg.delete_item(app_data)

    def auto_arrange(self):
        parent_to_children = {}  # node_id -> list of (child_node_id, pin_out, pin_in)
        child_to_parents = {}    # node_id -> list of (parent_node_id, pin_out, pin_in)

        for lid, (p_out, p_in) in list(self.links_data.items()):
            parent_id = self.pin_to_node.get(p_out)
            child_id = self.pin_to_node.get(p_in)
            if parent_id and child_id:
                parent_to_children.setdefault(parent_id, []).append((child_id, p_out, p_in))
                child_to_parents.setdefault(child_id, []).append((parent_id, p_out, p_in))

        root_node = None
        for node in self.nodes_data.values():
            if node.type == "Root":
                root_node = node
                break

        if not root_node:
            spacing_x = {
                "Root": 50, "Order": 300, "Flow": 580, "Sequence": 860,
                "Attack": 1140, "Movement": 1140, "Projectile": 1140,
                "Hitbox": 1420, "Phase": 1420
            }
            col_counters = {}
            for node_id, node in self.nodes_data.items():
                node_type = node.type
                col_key = node_type
                if node_type in ("Attack", "Movement", "Projectile"):
                    col_key = "Attack"
                elif node_type in ("Hitbox", "Phase"):
                    col_key = "Hitbox"

                col_counters[col_key] = col_counters.get(col_key, 0) + 1
                col_idx = col_counters[col_key]
                x = spacing_x.get(col_key, 50)
                y = 50 + col_idx * 180
                if dpg.does_item_exist(node_id):
                    dpg.set_item_pos(node_id, [x, y])
            return

        positioned_nodes = {}

        # Базовая позиция для Root
        root_x, root_y = 50, 320
        positioned_nodes[root_node.id] = (root_x, root_y)

        # 3. Распределение хитбоксов тела, зрения и остановки преследования (Root -> Hitboxes)
        body_pin = root_node.properties.get("body_pin")
        det_pin = root_node.properties.get("det_pin")
        stop_pin = root_node.properties.get("stop_pin")

        body_hitboxes = []
        det_hitboxes = []
        stop_hitboxes = []

        if root_node.id in parent_to_children:
            for child_id, p_out, p_in in parent_to_children[root_node.id]:
                child_node = self.nodes_data.get(child_id)
                if child_node and child_node.type == "Hitbox":
                    if p_out == body_pin:
                        body_hitboxes.append(child_node)
                    elif p_out == det_pin:
                        det_hitboxes.append(child_node)
                    elif p_out == stop_pin:
                        stop_hitboxes.append(child_node)

        current_y = 40
        for hb in body_hitboxes:
            positioned_nodes[hb.id] = (300, current_y)
            current_y += 85

        for hb in det_hitboxes:
            positioned_nodes[hb.id] = (300, current_y)
            current_y += 85

        for hb in stop_hitboxes:
            positioned_nodes[hb.id] = (300, current_y)
            current_y += 85

        # 4. Размещение нод Order ниже хитбоксов Root
        order_nodes = [n for n in self.nodes_data.values() if n.type == "Order"]
        current_y = max(current_y, 250)
        for order in order_nodes:
            positioned_nodes[order.id] = (300, current_y)

            trig_pin = order.properties.get("trig_pin")
            o_hitboxes = []
            if order.id in parent_to_children:
                for child_id, p_out, p_in in parent_to_children[order.id]:
                    child_node = self.nodes_data.get(child_id)
                    if child_node and child_node.type == "Hitbox" and p_out == trig_pin:
                        o_hitboxes.append(child_node)

            hb_y = current_y - 20
            for hb in o_hitboxes:
                positioned_nodes[hb.id] = (550, hb_y)
                hb_y += 85

            current_y += 180

        # 5. Размещение Behaviors (Sequence, Flow)
        behaviors = [n for n in self.nodes_data.values() if n.type in ("Sequence", "Flow")]
        behaviors.sort(key=lambda n: n.properties.get("name", ""))

        behavior_start_y = 120
        for i, b in enumerate(behaviors):
            b_y = behavior_start_y + i * 260
            positioned_nodes[b.id] = (550, b_y)

            trig_pin = b.properties.get("trig_pin")
            b_hitboxes = []
            if b.id in parent_to_children:
                for child_id, p_out, p_in in parent_to_children[b.id]:
                    child_node = self.nodes_data.get(child_id)
                    if child_node and child_node.type == "Hitbox" and p_out == trig_pin:
                        b_hitboxes.append(child_node)

            hb_y = b_y - 40
            for hb in b_hitboxes:
                positioned_nodes[hb.id] = (800, hb_y)
                hb_y += 85

            # Шаги
            steps_pins = b.properties.get("steps_pins", [])
            for step_idx, step_pin in enumerate(steps_pins):
                if b.id in parent_to_children:
                    for child_id, p_out, p_in in parent_to_children[b.id]:
                        if p_out == step_pin:
                            action_node = self.nodes_data.get(child_id)
                            if action_node and action_node.type in ("Attack", "Movement", "Projectile"):
                                if action_node.id not in positioned_nodes:
                                    act_y = b_y + step_idx * 110
                                    positioned_nodes[action_node.id] = (1000, act_y)

                                    action_components = []
                                    if action_node.id in parent_to_children:
                                        for comp_id, a_out, a_in in parent_to_children[action_node.id]:
                                            comp_node = self.nodes_data.get(comp_id)
                                            if comp_node and comp_node.type in ("Hitbox", "Phase"):
                                                action_components.append(comp_node)

                                    comp_y = act_y - 20
                                    for comp in action_components:
                                        positioned_nodes[comp.id] = (1250, comp_y)
                                        comp_y += 85

        unpositioned = []
        for node in self.nodes_data.values():
            if node.id not in positioned_nodes:
                unpositioned.append(node)

        if unpositioned:
            unpositioned.sort(key=lambda n: (n.type, n.id))
            col_x = 1500
            row_y = 50
            for node in unpositioned:
                positioned_nodes[node.id] = (col_x, row_y)
                row_y += 180
                if row_y > 800:
                    row_y = 50
                    col_x += 250

        for node_id, (x, y) in positioned_nodes.items():
            if dpg.does_item_exist(node_id):
                dpg.set_item_pos(node_id, [x, y])

    def spawn_flow_btn(self):
        self.create_flow_node()

    def spawn_sequence_btn(self):
        self.create_sequence_node()

    def spawn_attack_btn(self):
        self.create_attack_node()

    def spawn_hitbox_btn(self):
        self.create_hitbox_node()

    def spawn_movement_btn(self):
        self.create_movement_node()

    def spawn_phase_btn(self):
        self.create_phase_node()

    def spawn_projectile_btn(self):
        self.create_projectile_node()

    def delete_selected_nodes(self, sender=None, app_data=None):
        selected_nodes = dpg.get_selected_nodes("editor_tag")
        if not selected_nodes:
            return

        nodes_to_delete = []
        for node_id in selected_nodes:
            node = self.nodes_data.get(node_id)
            if node:
                if node.type == "Root":
                    print("[Warning] Deleting the Root node is not allowed.")
                    continue
                nodes_to_delete.append(node_id)

        if not nodes_to_delete:
            return

        for node_id in nodes_to_delete:
            node = self.nodes_data[node_id]
            node_pins = list(node.input_pins.keys()) + list(node.output_pins.keys())

            for lid, (p_out, p_in) in list(self.links_data.items()):
                if p_out in node_pins or p_in in node_pins:
                    if dpg.does_item_exist(lid):
                        dpg.delete_item(lid)
                    self.links_data.pop(lid, None)

            for pin_id in node_pins:
                self.pins_registry.pop(pin_id, None)
                self.pin_to_node.pop(pin_id, None)

            if dpg.does_item_exist(node_id):
                dpg.delete_item(node_id)

            self.nodes_data.pop(node_id, None)

            if self.active_selected_node_id == node_id:
                self.active_selected_node_id = None
                dpg.delete_item("properties_panel", children_only=True)
                dpg.add_text("Select a node on the canvas to inspect its properties.", parent="properties_panel")

        self.rebuild_all_order_buttons()
        self.save_preset_file(None, None)
        print(f"[Success] Deleted {len(nodes_to_delete)} selected node(s).")

    def rebuild_inspector(self, node_id):
        self.active_selected_node_id = node_id
        dpg.delete_item("properties_panel", children_only=True)

        node = self.nodes_data.get(node_id)
        if not node:
            return

        dpg.add_text(f"Node Type: {node.type}", parent="properties_panel")
        dpg.add_text("Properties Inspector:", parent="properties_panel")
        dpg.add_separator(parent="properties_panel")

        if node.type == "Root":
            dpg.add_input_text(label="Enemy Name", default_value=node.properties.get("name", "Enemy"), callback=self.update_property, user_data=(node_id, "name"), parent="properties_panel")
            dpg.add_input_int(label="Base HP", default_value=safe_int(node.properties.get("hp"), 3), callback=self.update_property, user_data=(node_id, "hp"), parent="properties_panel")
            dpg.add_input_int(label="Body Width", default_value=safe_int(node.properties.get("body_w"), 30), callback=self.update_property, user_data=(node_id, "body_w"), parent="properties_panel")
            dpg.add_input_int(label="Body Height", default_value=safe_int(node.properties.get("body_h"), 50), callback=self.update_property, user_data=(node_id, "body_h"), parent="properties_panel")
            dpg.add_separator(parent="properties_panel")
            dpg.add_text("Patrol Configuration", parent="properties_panel")
            dpg.add_combo(label="Movement Type", items=["walking", "flying"], default_value=node.properties.get("type_move", "walking"), callback=self.update_property, user_data=(node_id, "type_move"), parent="properties_panel")
            dpg.add_input_float(label="Speed", default_value=safe_float(node.properties.get("speed"), 1.2), callback=self.update_property, user_data=(node_id, "speed"), parent="properties_panel")
            dpg.add_input_int(label="Patrol Range X", default_value=safe_int(node.properties.get("range_x"), 120), callback=self.update_property, user_data=(node_id, "range_x"), parent="properties_panel")
            dpg.add_input_int(label="Stop Distance (Fallback)", default_value=safe_int(node.properties.get("stop_dist"), 60), callback=self.update_property, user_data=(node_id, "stop_dist"), parent="properties_panel")
            dpg.add_checkbox(label="Patrol On Platform", default_value=node.properties.get("patrol_on_platform", False), callback=self.update_property, user_data=(node_id, "patrol_on_platform"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_text("Detection Trigger (Vision)", parent="properties_panel")
            dpg.add_combo(label="Vision Shape", items=["rectangle", "circle"], default_value=node.properties.get("det_shape_type", "rectangle"), callback=self.update_property, user_data=(node_id, "det_shape_type"), parent="properties_panel")
            dpg.add_input_int(label="Vision Width", default_value=safe_int(node.properties.get("det_w"), 220), callback=self.update_property, user_data=(node_id, "det_w"), parent="properties_panel")
            dpg.add_input_int(label="Vision Height", default_value=safe_int(node.properties.get("det_h"), 70), callback=self.update_property, user_data=(node_id, "det_h"), parent="properties_panel")
            dpg.add_input_int(label="Vision Radius", default_value=safe_int(node.properties.get("det_r"), 110), callback=self.update_property, user_data=(node_id, "det_r"), parent="properties_panel")
            dpg.add_input_int(label="Offset X", default_value=safe_int(node.properties.get("det_offset_x"), 0), callback=self.update_property, user_data=(node_id, "det_offset_x"), parent="properties_panel")
            dpg.add_input_int(label="Offset Y", default_value=safe_int(node.properties.get("det_offset_y"), -10), callback=self.update_property, user_data=(node_id, "det_offset_y"), parent="properties_panel")
            dpg.add_input_float(label="Angle", default_value=safe_float(node.properties.get("det_angle"), 0.0), callback=self.update_property, user_data=(node_id, "det_angle"), parent="properties_panel")

        elif node.type == "Flow":
            dpg.add_input_text(label="Flow Name", default_value=node.properties.get("name", "Flow"), callback=self.update_property, user_data=(node_id, "name"), parent="properties_panel")
            dpg.add_input_float(label="Chance", default_value=safe_float(node.properties.get("chance"), 0.5), callback=self.update_property, user_data=(node_id, "chance"), parent="properties_panel")
            dpg.add_input_int(label="Cooldown", default_value=safe_int(node.properties.get("cooldown"), 180), callback=self.update_property, user_data=(node_id, "cooldown"), parent="properties_panel")
            dpg.add_input_int(label="Post Cooldown", default_value=safe_int(node.properties.get("post_cooldown"), 30), callback=self.update_property, user_data=(node_id, "post_cooldown"), parent="properties_panel")
            dpg.add_input_text(label="Telegraph Color (Hex)", default_value=node.properties.get("color_hex", "#ff0000"), callback=self.update_flow_color_hex, user_data=(node_id, "color_hex"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_text("Trigger Zone", parent="properties_panel")
            dpg.add_combo(label="Trigger Shape", items=["rectangle", "circle"], default_value=node.properties.get("trig_shape_type", "rectangle"), callback=self.update_property, user_data=(node_id, "trig_shape_type"), parent="properties_panel")
            dpg.add_input_int(label="Trigger W", default_value=safe_int(node.properties.get("trig_w"), 250), callback=self.update_property, user_data=(node_id, "trig_w"), parent="properties_panel")
            dpg.add_input_int(label="Trigger H", default_value=safe_int(node.properties.get("trig_h"), 80), callback=self.update_property, user_data=(node_id, "trig_h"), parent="properties_panel")
            dpg.add_input_int(label="Trigger R", default_value=safe_int(node.properties.get("trig_r"), 80), callback=self.update_property, user_data=(node_id, "trig_r"), parent="properties_panel")
            dpg.add_input_int(label="Offset X", default_value=safe_int(node.properties.get("trig_offset_x"), 0), callback=self.update_property, user_data=(node_id, "trig_offset_x"), parent="properties_panel")
            dpg.add_input_int(label="Offset Y", default_value=safe_int(node.properties.get("trig_offset_y"), 0), callback=self.update_property, user_data=(node_id, "trig_offset_y"), parent="properties_panel")
            dpg.add_input_int(label="Hold Time", default_value=safe_int(node.properties.get("trig_hold_time"), 0), callback=self.update_property, user_data=(node_id, "trig_hold_time"), parent="properties_panel")
            dpg.add_input_int(label="Consecutive Limit", default_value=safe_int(node.properties.get("trig_consecutive_limit"), 3), callback=self.update_property, user_data=(node_id, "trig_consecutive_limit"), parent="properties_panel")
            dpg.add_checkbox(label="Accumulate Hold", default_value=node.properties.get("trig_accumulate_hold", True), callback=self.update_property, user_data=(node_id, "trig_accumulate_hold"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_button(label="+ Add Flow Step Pin", callback=self.add_flow_step_pin, user_data=node_id, parent="properties_panel")

        elif node.type == "Sequence":
            dpg.add_input_text(label="Sequence Name", default_value=node.properties.get("name", "Sequence"), callback=self.update_property, user_data=(node_id, "name"), parent="properties_panel")
            dpg.add_input_float(label="Chance", default_value=safe_float(node.properties.get("chance"), 0.5), callback=self.update_property, user_data=(node_id, "chance"), parent="properties_panel")
            dpg.add_input_int(label="Cooldown", default_value=safe_int(node.properties.get("cooldown"), 120), callback=self.update_property, user_data=(node_id, "cooldown"), parent="properties_panel")
            dpg.add_input_int(label="Post Cooldown", default_value=safe_int(node.properties.get("post_cooldown"), 30), callback=self.update_property, user_data=(node_id, "post_cooldown"), parent="properties_panel")
            dpg.add_input_text(label="Telegraph Color (Hex)", default_value=node.properties.get("color_hex", "#ff0000"), callback=self.update_flow_color_hex, user_data=(node_id, "color_hex"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_text("Trigger Zone", parent="properties_panel")
            dpg.add_combo(label="Trigger Shape", items=["rectangle", "circle"], default_value=node.properties.get("trig_shape_type", "rectangle"), callback=self.update_property, user_data=(node_id, "trig_shape_type"), parent="properties_panel")
            dpg.add_input_int(label="Trigger W", default_value=safe_int(node.properties.get("trig_w"), 90), callback=self.update_property, user_data=(node_id, "trig_w"), parent="properties_panel")
            dpg.add_input_int(label="Trigger H", default_value=safe_int(node.properties.get("trig_h"), 50), callback=self.update_property, user_data=(node_id, "trig_h"), parent="properties_panel")
            dpg.add_input_int(label="Trigger R", default_value=safe_int(node.properties.get("trig_r"), 45), callback=self.update_property, user_data=(node_id, "trig_r"), parent="properties_panel")
            dpg.add_input_int(label="Offset X", default_value=safe_int(node.properties.get("trig_offset_x"), 10), callback=self.update_property, user_data=(node_id, "trig_offset_x"), parent="properties_panel")
            dpg.add_input_int(label="Offset Y", default_value=safe_int(node.properties.get("trig_offset_y"), 0), callback=self.update_property, user_data=(node_id, "trig_offset_y"), parent="properties_panel")
            dpg.add_input_int(label="Hold Time", default_value=safe_int(node.properties.get("trig_hold_time"), 0), callback=self.update_property, user_data=(node_id, "trig_hold_time"), parent="properties_panel")
            dpg.add_input_int(label="Consecutive Limit", default_value=safe_int(node.properties.get("trig_consecutive_limit"), 3), callback=self.update_property, user_data=(node_id, "trig_consecutive_limit"), parent="properties_panel")
            dpg.add_checkbox(label="Accumulate Hold", default_value=node.properties.get("trig_accumulate_hold", True), callback=self.update_property, user_data=(node_id, "trig_accumulate_hold"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_button(label="+ Add Action Step Pin", callback=self.add_sequence_step_pin, user_data=node_id, parent="properties_panel")

        elif node.type == "Attack":
            dpg.add_input_text(label="Attack Name", default_value=node.properties.get("name", "Attack"), callback=self.update_property, user_data=(node_id, "name"), parent="properties_panel")
            dpg.add_input_int(label="Cooldown", default_value=safe_int(node.properties.get("cooldown"), 45), callback=self.update_property, user_data=(node_id, "cooldown"), parent="properties_panel")
            dpg.add_input_int(label="Windup", default_value=safe_int(node.properties.get("windup"), 35), callback=self.update_property, user_data=(node_id, "windup"), parent="properties_panel")

        elif node.type == "Hitbox":
            dpg.add_combo(label="Shape Type", items=["rectangle", "circle"], default_value=node.properties.get("shape_type", "rectangle"), callback=self.update_property, user_data=(node_id, "shape_type"), parent="properties_panel")
            dpg.add_input_int(label="Width", default_value=safe_int(node.properties.get("w"), 50), callback=self.update_property, user_data=(node_id, "w"), parent="properties_panel")
            dpg.add_input_int(label="Height", default_value=safe_int(node.properties.get("h"), 40), callback=self.update_property, user_data=(node_id, "h"), parent="properties_panel")
            dpg.add_input_int(label="Radius", default_value=safe_int(node.properties.get("r"), 25), callback=self.update_property, user_data=(node_id, "r"), parent="properties_panel")
            dpg.add_input_int(label="Offset X", default_value=safe_int(node.properties.get("offset_x"), 10), callback=self.update_property, user_data=(node_id, "offset_x"), parent="properties_panel")
            dpg.add_input_int(label="Offset Y", default_value=safe_int(node.properties.get("offset_y"), 0), callback=self.update_property, user_data=(node_id, "offset_y"), parent="properties_panel")
            dpg.add_input_float(label="Angle", default_value=safe_float(node.properties.get("angle"), 0.0), callback=self.update_property, user_data=(node_id, "angle"), parent="properties_panel")
            dpg.add_input_int(label="Delay (frames)", default_value=safe_int(node.properties.get("delay"), 0), callback=self.update_property, user_data=(node_id, "delay"), parent="properties_panel")
            dpg.add_input_int(label="Duration (frames)", default_value=safe_int(node.properties.get("duration"), 10), callback=self.update_property, user_data=(node_id, "duration"), parent="properties_panel")
            dpg.add_input_int(label="Damage", default_value=safe_int(node.properties.get("damage"), 1), callback=self.update_property, user_data=(node_id, "damage"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_text("Knockback Settings", parent="properties_panel")
            dpg.add_input_float(label="Hit Angle", default_value=safe_float(node.properties.get("kb_angle_hit"), 0.0), callback=self.update_property, user_data=(node_id, "kb_angle_hit"), parent="properties_panel")
            dpg.add_input_float(label="Hit Force", default_value=safe_float(node.properties.get("kb_force_hit"), 12.0), callback=self.update_property, user_data=(node_id, "kb_force_hit"), parent="properties_panel")
            dpg.add_input_float(label="Parry Angle", default_value=safe_float(node.properties.get("kb_angle_parry"), 0.0), callback=self.update_property, user_data=(node_id, "kb_angle_parry"), parent="properties_panel")
            dpg.add_input_float(label="Parry Force", default_value=safe_float(node.properties.get("kb_force_parry"), 6.0), callback=self.update_property, user_data=(node_id, "kb_force_parry"), parent="properties_panel")
            dpg.add_combo(label="Sprite Dir", items=["forward", "up", "down", "to_player", "stationary"], default_value=node.properties.get("sprite_dir", "forward"), callback=self.update_property, user_data=(node_id, "sprite_dir"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_checkbox(label="Visual Box Enabled", default_value=node.properties.get("vis_enabled", False), callback=self.update_property, user_data=(node_id, "vis_enabled"), parent="properties_panel")
            dpg.add_combo(label="Vis Type", items=["rectangle", "circle"], default_value=node.properties.get("vis_type", "rectangle"), callback=self.update_property, user_data=(node_id, "vis_type"), parent="properties_panel")
            dpg.add_input_int(label="Vis Width", default_value=safe_int(node.properties.get("vis_w"), 50), callback=self.update_property, user_data=(node_id, "vis_w"), parent="properties_panel")
            dpg.add_input_int(label="Vis Height", default_value=safe_int(node.properties.get("vis_h"), 40), callback=self.update_property, user_data=(node_id, "vis_h"), parent="properties_panel")
            dpg.add_input_int(label="Vis Radius", default_value=safe_int(node.properties.get("vis_r"), 25), callback=self.update_property, user_data=(node_id, "vis_r"), parent="properties_panel")
            dpg.add_input_int(label="Vis Offset X", default_value=safe_int(node.properties.get("vis_offset_x"), 0), callback=self.update_property, user_data=(node_id, "vis_offset_x"), parent="properties_panel")
            dpg.add_input_int(label="Vis Offset Y", default_value=safe_int(node.properties.get("vis_offset_y"), 0), callback=self.update_property, user_data=(node_id, "vis_offset_y"), parent="properties_panel")

        elif node.type == "Movement":
            dpg.add_input_text(label="Movement Name", default_value=node.properties.get("name", "Movement"), callback=self.update_property, user_data=(node_id, "name"), parent="properties_panel")
            dpg.add_input_int(label="Stop Distance", default_value=safe_int(node.properties.get("stop_dist"), 0), callback=self.update_property, user_data=(node_id, "stop_dist"), parent="properties_panel")

        elif node.type == "Phase":
            dpg.add_combo(label="Direction", items=["forward", "backward", "to_player", "away_from_player", "teleport"], default_value=node.properties.get("direction", "forward"), callback=self.update_property, user_data=(node_id, "direction"), parent="properties_panel")
            dpg.add_combo(label="Velocity Curve", items=["fade_out", "fade_in", "constant", "ease_in_out"], default_value=node.properties.get("curve", "fade_out"), callback=self.update_property, user_data=(node_id, "curve"), parent="properties_panel")
            dpg.add_input_float(label="Force X / Teleport DX", default_value=safe_float(node.properties.get("force_x"), 8.0), callback=self.update_property, user_data=(node_id, "force_x"), parent="properties_panel")
            dpg.add_input_float(label="Force Y / Teleport DY", default_value=safe_float(node.properties.get("force_y"), 0.0), callback=self.update_property, user_data=(node_id, "force_y"), parent="properties_panel")
            dpg.add_input_int(label="Delay (frames)", default_value=safe_int(node.properties.get("delay"), 0), callback=self.update_property, user_data=(node_id, "delay"), parent="properties_panel")
            dpg.add_input_int(label="Duration (frames)", default_value=safe_int(node.properties.get("duration"), 15), callback=self.update_property, user_data=(node_id, "duration"), parent="properties_panel")

        elif node.type == "Projectile":
            dpg.add_input_text(label="Projectile Name", default_value=node.properties.get("name", "Projectile"), callback=self.update_property, user_data=(node_id, "name"), parent="properties_panel")
            dpg.add_input_float(label="Speed", default_value=safe_float(node.properties.get("speed"), 10.0), callback=self.update_property, user_data=(node_id, "speed"), parent="properties_panel")
            dpg.add_input_float(label="Launch Angle", default_value=safe_float(node.properties.get("angle"), 0.0), callback=self.update_property, user_data=(node_id, "angle"), parent="properties_panel")
            dpg.add_input_float(label="Gravity Scale", default_value=safe_float(node.properties.get("gravity"), 0.0), callback=self.update_property, user_data=(node_id, "gravity"), parent="properties_panel")
            dpg.add_input_int(label="Damage", default_value=safe_int(node.properties.get("damage"), 1), callback=self.update_property, user_data=(node_id, "damage"), parent="properties_panel")
            dpg.add_input_int(label="Radius", default_value=safe_int(node.properties.get("radius"), 8), callback=self.update_property, user_data=(node_id, "radius"), parent="properties_panel")
            dpg.add_checkbox(label="Aim At Player", default_value=node.properties.get("aim_at_player", False), callback=self.update_property, user_data=(node_id, "aim_at_player"), parent="properties_panel")
            dpg.add_input_float(label="Homing Strength", default_value=safe_float(node.properties.get("homing"), 0.0), callback=self.update_property, user_data=(node_id, "homing"), parent="properties_panel")
            dpg.add_input_int(label="Shoot Cooldown", default_value=safe_int(node.properties.get("shoot_cooldown"), 30), callback=self.update_property, user_data=(node_id, "shoot_cooldown"), parent="properties_panel")

        elif node.type == "Order":
            dpg.add_input_text(label="Order Name", default_value=node.properties.get("name", "Order"), callback=self.update_property, user_data=(node_id, "name"), parent="properties_panel")
            dpg.add_input_float(label="Chance", default_value=safe_float(node.properties.get("chance"), 1.0), callback=self.update_property, user_data=(node_id, "chance"), parent="properties_panel")
            dpg.add_input_int(label="Cooldown", default_value=safe_int(node.properties.get("cooldown"), 120), callback=self.update_property, user_data=(node_id, "cooldown"), parent="properties_panel")
            dpg.add_input_int(label="Post Cooldown", default_value=safe_int(node.properties.get("post_cooldown"), 30), callback=self.update_property, user_data=(node_id, "post_cooldown"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_text("Trigger Zone (Purple)", parent="properties_panel")
            dpg.add_combo(label="Trigger Shape", items=["rectangle", "circle"], default_value=node.properties.get("trig_shape_type", "rectangle"), callback=self.update_property, user_data=(node_id, "trig_shape_type"), parent="properties_panel")
            dpg.add_input_int(label="Trigger W", default_value=safe_int(node.properties.get("trig_w"), 150), callback=self.update_property, user_data=(node_id, "trig_w"), parent="properties_panel")
            dpg.add_input_int(label="Trigger H", default_value=safe_int(node.properties.get("trig_h"), 60), callback=self.update_property, user_data=(node_id, "trig_h"), parent="properties_panel")
            dpg.add_input_int(label="Trigger R", default_value=safe_int(node.properties.get("trig_r"), 75), callback=self.update_property, user_data=(node_id, "trig_r"), parent="properties_panel")
            dpg.add_input_int(label="Offset X", default_value=safe_int(node.properties.get("trig_offset_x"), 0), callback=self.update_property, user_data=(node_id, "trig_offset_x"), parent="properties_panel")
            dpg.add_input_int(label="Offset Y", default_value=safe_int(node.properties.get("trig_offset_y"), 0), callback=self.update_property, user_data=(node_id, "trig_offset_y"), parent="properties_panel")
            dpg.add_input_int(label="Hold Time", default_value=safe_int(node.properties.get("trig_hold_time"), 0), callback=self.update_property, user_data=(node_id, "trig_hold_time"), parent="properties_panel")
            dpg.add_input_int(label="Consecutive Limit", default_value=safe_int(node.properties.get("trig_consecutive_limit"), 3), callback=self.update_property, user_data=(node_id, "trig_consecutive_limit"), parent="properties_panel")
            dpg.add_checkbox(label="Accumulate Hold", default_value=node.properties.get("trig_accumulate_hold", True), callback=self.update_property, user_data=(node_id, "trig_accumulate_hold"), parent="properties_panel")

            dpg.add_separator(parent="properties_panel")
            dpg.add_text("Steps Connections:", parent="properties_panel")
            steps_pins = node.properties.get("steps_pins", [])
            for idx, pin_id in enumerate(steps_pins):
                step_num = idx + 1
                with dpg.group(horizontal=True, parent="properties_panel"):
                    dpg.add_text(f"Step {step_num}:")
                    connected_names = []
                    for _, (p_out, p_in) in self.links_data.items():
                        if p_in == pin_id:
                            out_node_id = self.pin_to_node.get(p_out)
                            if out_node_id and out_node_id in self.nodes_data:
                                connected_names.append(self.nodes_data[out_node_id].properties.get("name", "Unknown"))
                    if connected_names:
                        dpg.add_text(f" {', '.join(connected_names)}", color=[0, 200, 255])
                    else:
                        dpg.add_text(" Empty", color=[120, 120, 120])

            dpg.add_separator(parent="properties_panel")
            with dpg.group(horizontal=True, parent="properties_panel"):
                dpg.add_button(label="+ Add Step", callback=self._on_add_order_step_click, user_data=node_id)
                dpg.add_button(label="- Remove Step", callback=self._on_remove_order_step_click, user_data=node_id)