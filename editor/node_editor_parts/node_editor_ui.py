# editor/node_editor_parts/node_editor_ui.py
import dearpygui.dearpygui as dpg

class NodeEditorUIMixin:
    def setup_ui(self):
        with dpg.window(
            label="AI Behavior Node Visual Graph Designer",
            tag="main_window",
            width=1400,
            height=800,
            no_bring_to_front_on_focus=True
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("Target Preset:")
                presets = self.find_all_presets()
                default_val = presets[0] if presets else ""
                dpg.add_combo(items=presets, default_value=default_val, tag="preset_combo", width=300)
                dpg.add_button(label="Load Graph", callback=self.load_preset_file)
                dpg.add_button(label="Save (Live-Reload)", callback=self.save_preset_file)
                dpg.add_button(label="Auto-Arrange", callback=self.auto_arrange)
                dpg.add_checkbox(label="Show Preview [P]", default_value=True, tag="show_preview_checkbox", callback=self.toggle_preview_visibility)
                dpg.add_button(label="Focus Preview [F]", callback=self.toggle_focus)
                
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                with dpg.child_window(tag="left_panel_window", width=320, height=720):
                    with dpg.collapsing_header(label="Create Graph Nodes", default_open=True):
                        dpg.add_button(label="Add AI Flow Node", width=290, callback=self.spawn_flow_btn)
                        dpg.add_button(label="Add Action Sequence Node", width=290, callback=self.spawn_sequence_btn)
                        dpg.add_button(label="Add Attack Action Node", width=290, callback=self.spawn_attack_btn)
                        dpg.add_button(label="Add Hitbox Component Node", width=290, callback=self.spawn_hitbox_btn)
                        dpg.add_button(label="Add Movement Action Node", width=290, callback=self.spawn_movement_btn)
                        dpg.add_button(label="Add Phase Component Node", width=290, callback=self.spawn_phase_btn)
                        dpg.add_button(label="Add Projectile Action Node", width=290, callback=self.spawn_projectile_btn)
                        dpg.add_button(label="Add seq/flow order Node", width=290, callback=self.spawn_order_btn_callback)
                        
                        # Разделитель и кнопка для удаления
                        dpg.add_separator()
                        dpg.add_button(label="Delete Selected Nodes [Del]", width=290, callback=self.delete_selected_nodes)
                        
                    dpg.add_separator()
                    
                    with dpg.child_window(tag="properties_panel", width=300, height=330):
                        dpg.add_text("Select a node on the canvas to inspect its properties.")
                        
                    dpg.add_separator()
                    
                    with dpg.collapsing_header(label="Sequence Timeline", default_open=True, tag="timeline_header"):
                        dpg.add_drawlist(width=300, height=120, tag="timeline_drawlist")
                        
                with dpg.child_window(tag="right_panel_window", width=1050, height=720):
                    dpg.add_node_editor(tag="editor_tag", callback=self.link_callback, delink_callback=self.delink_callback, minimap=True)

        self.setup_preview_window()
        
        dpg.set_viewport_resize_callback(self.resize_callback)
        with dpg.handler_registry():
            dpg.add_key_press_handler(callback=self.global_key_handler)

    def spawn_order_btn_callback(self, sender, app_data):
        self.spawn_order_btn()

    def setup_preview_window(self):
        with dpg.window(label="Interactive Preview Panel", tag="preview_window", width=380, height=340, pos=[950, 150], no_close=True, no_move=True):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Reset View", callback=self.reset_preview_pan)
                dpg.add_slider_float(label="Zoom", tag="preview_zoom", default_value=0.5, min_value=0.1, max_value=2.0, width=120)
            # drawlist инициализируется с width=-1 и height=-1 для авторасширения в окне
            dpg.add_drawlist(width=-1, height=-1, tag="preview_drawlist")

    def resize_callback(self, sender, app_data):
        if not dpg.does_item_exist("main_window"):
            return
        
        vw = dpg.get_viewport_width()
        vh = dpg.get_viewport_height()
        
        dpg.configure_item("main_window", width=vw, height=vh)
        dpg.set_item_pos("main_window", [0, 0])
        
        left_w = 320
        child_h = max(100, vh - 90)
        right_w = max(100, vw - left_w - 40)
        
        if dpg.does_item_exist("left_panel_window"):
            dpg.configure_item("left_panel_window", width=left_w, height=child_h)
        if dpg.does_item_exist("right_panel_window"):
            dpg.configure_item("right_panel_window", width=right_w, height=child_h)
        if dpg.does_item_exist("properties_panel"):
            dpg.configure_item("properties_panel", width=left_w - 20, height=max(100, child_h - 410))

    def global_key_handler(self, sender, app_data):
        if app_data == 122 or app_data == 27:
            dpg.toggle_viewport_fullscreen()
        elif app_data == 70:
            self.toggle_focus()
        elif app_data == 80:
            if dpg.does_item_exist("show_preview_checkbox"):
                current_val = dpg.get_value("show_preview_checkbox")
                dpg.set_value("show_preview_checkbox", not current_val)
                self.toggle_preview_visibility()
        elif app_data == 261 or app_data == 259:  # Клавиши Delete (261) и Backspace (259)
            self.delete_selected_nodes()