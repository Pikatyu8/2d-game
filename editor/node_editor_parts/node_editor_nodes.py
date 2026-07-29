# editor/node_editor_parts/node_editor_nodes.py
import dearpygui.dearpygui as dpg
from editor.node_editor_parts.node_editor_state import NodeData, PinData

class NodeEditorNodesMixin:
    def create_node_theme(self, color):
        with dpg.theme() as theme_id:
            with dpg.theme_component(dpg.mvNode):
                dpg.add_theme_color(dpg.mvNodeCol_TitleBar, color, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, tuple(min(255, c + 20) for c in color), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, tuple(min(255, c + 40) for c in color), category=dpg.mvThemeCat_Nodes)
        return theme_id

    def init_themes(self):
        self.root_theme = self.create_node_theme((60, 75, 95))
        self.flow_theme = self.create_node_theme((0, 140, 150))
        self.sequence_theme = self.create_node_theme((170, 100, 30))
        self.attack_theme = self.create_node_theme((140, 45, 45))
        self.hitbox_theme = self.create_node_theme((160, 75, 105))
        self.movement_theme = self.create_node_theme((45, 85, 140))
        self.phase_theme = self.create_node_theme((75, 130, 160))
        self.projectile_theme = self.create_node_theme((105, 55, 140))
        self.order_theme = self.create_node_theme((80, 50, 120))
        self.order_highlight_theme = self.create_node_theme((0, 240, 255))

    def create_root_node(self, properties=None):
        properties = properties or {}
        node_id = dpg.add_node(label="Root (Enemy Preset)", parent="editor_tag")
        node = NodeData(node_id, "Root", "Root (Enemy Preset)", properties)

        p_flows = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Flows Link (Behavior)", parent=p_flows)
        node.output_pins[p_flows] = PinData(p_flows, "Output", "Flows", "Behavior")
        self.pins_registry[p_flows] = {"node_id": node_id, "type": "Behavior", "direction": "Output"}
        self.pin_to_node[p_flows] = node_id

        p_seqs = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Sequences Link (Exec)", parent=p_seqs)
        node.output_pins[p_seqs] = PinData(p_seqs, "Output", "Sequences", "Exec")
        self.pins_registry[p_seqs] = {"node_id": node_id, "type": "Exec", "direction": "Output"}
        self.pin_to_node[p_seqs] = node_id

        # Новые универсальные пины хитбоксов для Root (Тело)
        p_body = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Body shapes (Component)", parent=p_body)
        node.output_pins[p_body] = PinData(p_body, "Output", "Body", "Component")
        self.pins_registry[p_body] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_body] = node_id
        properties["body_pin"] = p_body

        # Зрение (Детекция)
        p_det = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Detection shapes (Component)", parent=p_det)
        node.output_pins[p_det] = PinData(p_det, "Output", "Detection", "Component")
        self.pins_registry[p_det] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_det] = node_id
        properties["det_pin"] = p_det

        # Новые пины хитбоксов остановки для Root
        p_stop = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Stopping shapes (Component)", parent=p_stop)
        node.output_pins[p_stop] = PinData(p_stop, "Output", "Stopping", "Component")
        self.pins_registry[p_stop] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_stop] = node_id
        properties["stop_pin"] = p_stop

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.root_theme)
        return node_id

    def create_flow_node(self, properties=None):
        properties = properties or {}
        properties.setdefault("steps_pins", [])
        properties.setdefault("name", f"Combo Flow {len(self.nodes_data)}")
        node_id = dpg.add_node(label=f"Flow: {properties['name']}", parent="editor_tag")
        node = NodeData(node_id, "Flow", f"Flow: {properties['name']}", properties)

        p_in = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text("Parent Connection", parent=p_in)
        node.input_pins[p_in] = PinData(p_in, "Input", "Parent", "Behavior")
        self.pins_registry[p_in] = {"node_id": node_id, "type": "Behavior", "direction": "Input"}
        self.pin_to_node[p_in] = node_id

        p_order = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        group_id = dpg.add_group(horizontal=True, tag=f"order_group_{node_id}", parent=p_order)
        dpg.add_text("order: ", parent=group_id)

        node.output_pins[p_order] = PinData(p_order, "Output", "Order Connection", "Order")
        self.pins_registry[p_order] = {"node_id": node_id, "type": "Order", "direction": "Output"}
        self.pin_to_node[p_order] = node_id
        properties["order_pin"] = p_order

        # Новый пин триггера для Flow
        p_trig = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Trigger zone (Component)", parent=p_trig)
        node.output_pins[p_trig] = PinData(p_trig, "Output", "Trigger Zone", "Component")
        self.pins_registry[p_trig] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_trig] = node_id
        properties["trig_pin"] = p_trig

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.flow_theme)

        if "steps" in properties:
            for idx, step_data in enumerate(properties["steps"]):
                self.add_flow_step_pin_ui(node_id, step_index=idx, step_data=step_data)

        return node_id

    def create_sequence_node(self, properties=None):
        properties = properties or {}
        properties.setdefault("steps_pins", [])
        properties.setdefault("name", f"Sequence {len(self.nodes_data)}")
        node_id = dpg.add_node(label=f"Sequence: {properties['name']}", parent="editor_tag")
        node = NodeData(node_id, "Sequence", f"Sequence: {properties['name']}", properties)

        p_in = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text("Trigger Input", parent=p_in)
        node.input_pins[p_in] = PinData(p_in, "Input", "Trigger", "Exec")
        self.pins_registry[p_in] = {"node_id": node_id, "type": "Exec", "direction": "Input"}
        self.pin_to_node[p_in] = node_id

        p_order = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        group_id = dpg.add_group(horizontal=True, tag=f"order_group_{node_id}", parent=p_order)
        dpg.add_text("order: ", parent=group_id)

        node.output_pins[p_order] = PinData(p_order, "Output", "Order Connection", "Order")
        self.pins_registry[p_order] = {"node_id": node_id, "type": "Order", "direction": "Output"}
        self.pin_to_node[p_order] = node_id
        properties["order_pin"] = p_order

        # Новый пин триггера для Sequence
        p_trig = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Trigger zone (Component)", parent=p_trig)
        node.output_pins[p_trig] = PinData(p_trig, "Output", "Trigger Zone", "Component")
        self.pins_registry[p_trig] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_trig] = node_id
        properties["trig_pin"] = p_trig

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.sequence_theme)

        if "steps" in properties:
            for idx, step_data in enumerate(properties["steps"]):
                self.add_sequence_step_pin_ui(node_id, step_index=idx, step_data=step_data)

        return node_id

    def create_attack_node(self, properties=None):
        properties = properties or {}
        properties.setdefault("name", f"Attack Template {len(self.nodes_data)}")
        node_id = dpg.add_node(label=f"Attack Action", parent="editor_tag")
        node = NodeData(node_id, "Attack", "Attack Action", properties)

        p_in = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text("Activate (Exec)", parent=p_in)
        node.input_pins[p_in] = PinData(p_in, "Input", "Activate", "Exec")
        self.pins_registry[p_in] = {"node_id": node_id, "type": "Exec", "direction": "Input"}
        self.pin_to_node[p_in] = node_id

        p_out = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Hitboxes (Component)", parent=p_out)
        node.output_pins[p_out] = PinData(p_out, "Output", "Hitboxes", "Component")
        self.pins_registry[p_out] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_out] = node_id

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.attack_theme)
        return node_id

    def create_hitbox_node(self, properties=None):
        properties = properties or {}
        node_id = dpg.add_node(label="Hitbox Component", parent="editor_tag")
        node = NodeData(node_id, "Hitbox", "Hitbox Component", properties)

        p_in = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text("Parent Link (Component)", parent=p_in)
        node.input_pins[p_in] = PinData(p_in, "Input", "Parent", "Component")
        self.pins_registry[p_in] = {"node_id": node_id, "type": "Component", "direction": "Input"}
        self.pin_to_node[p_in] = node_id

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.hitbox_theme)
        return node_id

    def create_movement_node(self, properties=None):
        properties = properties or {}
        properties.setdefault("name", f"Movement Preset {len(self.nodes_data)}")
        node_id = dpg.add_node(label="Movement Action", parent="editor_tag")
        node = NodeData(node_id, "Movement", "Movement Action", properties)

        p_in = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text("Activate (Exec)", parent=p_in)
        node.input_pins[p_in] = PinData(p_in, "Input", "Activate", "Exec")
        self.pins_registry[p_in] = {"node_id": node_id, "type": "Exec", "direction": "Input"}
        self.pin_to_node[p_in] = node_id

        p_out = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Phases (Component)", parent=p_out)
        node.output_pins[p_out] = PinData(p_out, "Output", "Phases", "Component")
        self.pins_registry[p_out] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_out] = node_id

        # Новый пин области остановки для Movement
        p_stop = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Stop Area (Component)", parent=p_stop)
        node.output_pins[p_stop] = PinData(p_stop, "Output", "Stop Area", "Component")
        self.pins_registry[p_stop] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_stop] = node_id
        properties["stop_pin"] = p_stop

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.movement_theme)
        return node_id

    def create_phase_node(self, properties=None):
        properties = properties or {}
        node_id = dpg.add_node(label="Phase Component", parent="editor_tag")
        node = NodeData(node_id, "Phase", "Phase Component", properties)

        p_in = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text("Parent Link (Component)", parent=p_in)
        node.input_pins[p_in] = PinData(p_in, "Input", "Parent", "Component")
        self.pins_registry[p_in] = {"node_id": node_id, "type": "Component", "direction": "Input"}
        self.pin_to_node[p_in] = node_id

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.phase_theme)
        return node_id

    def create_projectile_node(self, properties=None):
        properties = properties or {}
        properties.setdefault("name", f"Projectile Template {len(self.nodes_data)}")
        node_id = dpg.add_node(label="Projectile Action", parent="editor_tag")
        node = NodeData(node_id, "Projectile", "Projectile Action", properties)

        p_in = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text("Activate (Exec)", parent=p_in)
        node.input_pins[p_in] = PinData(p_in, "Input", "Activate", "Exec")
        self.pins_registry[p_in] = {"node_id": node_id, "type": "Exec", "direction": "Input"}
        self.pin_to_node[p_in] = node_id

        # Новый пин хитбоксов снаряда
        p_out = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Hitboxes (Component)", parent=p_out)
        node.output_pins[p_out] = PinData(p_out, "Output", "Hitboxes", "Component")
        self.pins_registry[p_out] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_out] = node_id
        properties["hitbox_pin"] = p_out

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.projectile_theme)
        return node_id

    def add_sequence_step_pin_ui(self, node_id, step_index=None, step_data=None):
        node = self.nodes_data[node_id]
        steps_list = node.properties.setdefault("steps_pins", [])
        if step_index is None:
            step_index = len(steps_list)

        pin_label = f"Step {step_index}"
        delay_val = step_data.get("delay", 0) if step_data else 0

        pin_id = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text(pin_label, parent=pin_id)
        delay_input = dpg.add_input_int(width=85, label="Delay", default_value=delay_val, callback=self.update_step_delay, user_data=(node_id, pin_id), parent=pin_id)

        pin_info = PinData(pin_id, "Output", pin_label, "Exec", {"delay": delay_val, "delay_input": delay_input, "index": step_index})
        node.output_pins[pin_id] = pin_info
        self.pins_registry[pin_id] = {"node_id": node_id, "type": "Exec", "direction": "Output"}
        self.pin_to_node[pin_id] = node_id
        steps_list.append(pin_id)

    def add_flow_step_pin_ui(self, node_id, step_index=None, step_data=None):
        node = self.nodes_data[node_id]
        steps_list = node.properties.setdefault("steps_pins", [])
        if step_index is None:
            step_index = len(steps_list)

        pin_label = f"Step {step_index}"
        delay_val = step_data.get("delay", 0) if step_data else 0
        is_random = step_data.get("is_random", False) if step_data else False

        pin_id = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text(pin_label, parent=pin_id)
        delay_input = dpg.add_input_int(width=85, label="Delay", default_value=delay_val, callback=self.update_flow_step_delay, user_data=(node_id, pin_id), parent=pin_id)
        random_chk = dpg.add_checkbox(label="Random Pool", default_value=is_random, callback=self.update_flow_step_random, user_data=(node_id, pin_id), parent=pin_id)

        pin_info = PinData(pin_id, "Output", pin_label, "Exec", {
            "delay": delay_val,
            "is_random": is_random,
            "delay_input": delay_input,
            "random_chk": random_chk,
            "index": step_index
        })
        node.output_pins[pin_id] = pin_info
        self.pins_registry[pin_id] = {"node_id": node_id, "type": "Exec", "direction": "Output"}
        self.pin_to_node[pin_id] = node_id
        steps_list.append(pin_id)

    def create_order_node(self, properties=None):
        properties = properties or {}
        properties.setdefault("steps_pins", [])
        properties.setdefault("name", f"Order {len(self.nodes_data)}")

        node_id = dpg.add_node(label=f"seq/flow order: {properties['name']}", parent="editor_tag")
        node = NodeData(node_id, "Order", f"seq/flow order: {properties['name']}", properties)

        p_static = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Static)
        group_id = dpg.add_group(horizontal=True, parent=p_static)
        dpg.add_button(label="+", width=30, callback=self._on_add_order_step_click, user_data=node_id, parent=group_id)
        dpg.add_button(label="-", width=30, callback=self._on_remove_order_step_click, user_data=node_id, parent=group_id)
        dpg.add_text("Steps Control", parent=group_id)

        # Новый пин триггера для Order
        p_trig = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_text("Trigger zone (Component)", parent=p_trig)
        node.output_pins[p_trig] = PinData(p_trig, "Output", "Trigger Zone", "Component")
        self.pins_registry[p_trig] = {"node_id": node_id, "type": "Component", "direction": "Output"}
        self.pin_to_node[p_trig] = node_id
        properties["trig_pin"] = p_trig

        self.nodes_data[node_id] = node
        dpg.bind_item_theme(node_id, self.order_theme)
        return node_id

    def add_order_step(self, node_id):
        node = self.nodes_data[node_id]
        steps_list = node.properties.setdefault("steps_pins", [])
        step_index = len(steps_list) + 1

        pin_label = f"Step {step_index}"

        pin_id = dpg.add_node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_text(pin_label, parent=pin_id)

        pin_info = PinData(pin_id, "Input", pin_label, "Order", {"index": step_index})
        node.input_pins[pin_id] = pin_info
        self.pins_registry[pin_id] = {"node_id": node_id, "type": "Order", "direction": "Input"}
        self.pin_to_node[pin_id] = node_id
        steps_list.append(pin_id)

    def _on_add_order_step_click(self, sender, app_data, user_data):
        self.add_order_step(user_data)
        self.rebuild_all_order_buttons()

    def _on_remove_order_step_click(self, sender, app_data, user_data):
        node = self.nodes_data.get(user_data)
        if node and node.properties.get("steps_pins"):
            pin_id = node.properties["steps_pins"].pop()
            for lid, (p_out, p_in) in list(self.links_data.items()):
                if p_in == pin_id or p_out == pin_id:
                    if dpg.does_item_exist(lid):
                        dpg.delete_item(lid)
                    self.links_data.pop(lid, None)

            if dpg.does_item_exist(pin_id):
                dpg.delete_item(pin_id)

            self.pins_registry.pop(pin_id, None)
            self.pin_to_node.pop(pin_id, None)
            node.input_pins.pop(pin_id, None)

            self.rebuild_all_order_buttons()