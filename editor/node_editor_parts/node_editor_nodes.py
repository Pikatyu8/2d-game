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
        
        with dpg.node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output) as pin_id:
            dpg.add_text(pin_label)
            delay_input = dpg.add_input_int(width=85, label="Delay", default_value=delay_val, callback=self.update_step_delay, user_data=(node_id, pin_id))
            
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
        
        with dpg.node_attribute(parent=node_id, attribute_type=dpg.mvNode_Attr_Output) as pin_id:
            dpg.add_text(pin_label)
            delay_input = dpg.add_input_int(width=85, label="Delay", default_value=delay_val, callback=self.update_flow_step_delay, user_data=(node_id, pin_id))
            random_chk = dpg.add_checkbox(label="Random Pool", default_value=is_random, callback=self.update_flow_step_random, user_data=(node_id, pin_id))
            
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