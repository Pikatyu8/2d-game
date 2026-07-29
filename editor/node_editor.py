# editor/node_editor.py
import sys
import os
import time
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import dearpygui.dearpygui as dpg
except ImportError as e:
    with open("node_editor_error.log", "a", encoding="utf-8") as f:
        f.write(f"\n[Ошибка] Не удалось импортировать Dear PyGui: {e}\n")
        f.write("[Решение] Пожалуйста, убедитесь, что библиотека установлена в используемом Python-окружении:\n")
        f.write(f"          Сделайте запуск: {sys.executable} -m pip install dearpygui\n")
    raise

from editor.node_editor_parts.node_editor_state import NodeEditorStateMixin
from editor.node_editor_parts.node_editor_nodes import NodeEditorNodesMixin
from editor.node_editor_parts.node_editor_io import NodeEditorIOMixin
from editor.node_editor_parts.node_editor_inspector import NodeEditorInspectorMixin
from editor.node_editor_parts.node_editor_ui import NodeEditorUIMixin
from editor.node_editor_parts.node_editor_preview import NodeEditorPreviewMixin
from editor.node_editor_parts.node_editor_timeline import NodeEditorTimelineMixin

class NodeEditor(
    NodeEditorStateMixin,
    NodeEditorNodesMixin,
    NodeEditorIOMixin,
    NodeEditorInspectorMixin,
    NodeEditorUIMixin,
    NodeEditorPreviewMixin,
    NodeEditorTimelineMixin
):
    def __init__(self):
        dpg.create_context()
        self.init_state()
        self.init_themes()

    def spawn_order_btn(self):
        node_id = self.create_order_node()
        self.add_order_step(node_id)
        self.add_order_step(node_id)
        self.rebuild_all_order_buttons()

    def rebuild_all_order_buttons(self):
        connections = {}
        for lid, (p_out, p_in) in list(self.links_data.items()):
            out_reg = self.pins_registry.get(p_out)
            in_reg = self.pins_registry.get(p_in)
            if out_reg and in_reg and out_reg["type"] == "Order" and in_reg["type"] == "Order":
                order_node_id = in_reg["node_id"]
                order_node = self.nodes_data.get(order_node_id)
                if order_node:
                    pin_info = order_node.input_pins.get(p_in)
                    if pin_info:
                        step_idx = pin_info.properties.get("index", 1)
                        connections.setdefault(p_out, []).append((order_node_id, step_idx))
                        
        if not hasattr(self, "order_pills_registry"):
            self.order_pills_registry = {}
        self.order_pills_registry.clear()
        
        for node_id, node in list(self.nodes_data.items()):
            if node.type in ("Flow", "Sequence"):
                order_pin = node.properties.get("order_pin")
                if not order_pin:
                    continue
                    
                group_tag = f"order_group_{node_id}"
                if dpg.does_item_exist(group_tag):
                    dpg.delete_item(group_tag, children_only=True)
                    dpg.add_text("order: ", parent=group_tag)
                    
                    node_conns = connections.get(order_pin, [])
                    node_conns.sort(key=lambda x: x[1])
                    
                    for order_node_id, step_idx in node_conns:
                        btn_label = f"[{step_idx}]"
                        btn_id = dpg.add_button(
                            label=btn_label, 
                            parent=group_tag, 
                            callback=self._on_order_pill_click,
                            user_data=(order_node_id, node_id)
                        )
                        self.order_pills_registry[btn_id] = order_node_id

    def _on_order_pill_click(self, sender, app_data, user_data):
        order_node_id, parent_node_id = user_data
        if dpg.does_item_exist(order_node_id):
            dpg.clear_selected_nodes("editor_tag")
            dpg.select_item(order_node_id)
            self.rebuild_inspector(order_node_id)

    def update_order_highlights(self):
        if not hasattr(self, "order_pills_registry") or not self.order_pills_registry:
            return
            
        hovered_order_node = None
        for btn_id, order_node_id in list(self.order_pills_registry.items()):
            if dpg.does_item_exist(btn_id):
                try:
                    if dpg.is_item_hovered(btn_id):
                        hovered_order_node = order_node_id
                        break
                except Exception:
                    pass
                    
        if not hasattr(self, "currently_highlighted_order_node"):
            self.currently_highlighted_order_node = None
            
        if hovered_order_node != self.currently_highlighted_order_node:
            if self.currently_highlighted_order_node and dpg.does_item_exist(self.currently_highlighted_order_node):
                dpg.bind_item_theme(self.currently_highlighted_order_node, self.order_theme)
                
            self.currently_highlighted_order_node = hovered_order_node
            
            if hovered_order_node and dpg.does_item_exist(hovered_order_node):
                dpg.bind_item_theme(hovered_order_node, self.order_highlight_theme)

    def run(self, arg_name=None):
        dpg.create_viewport(title="AI Visual Graph Editor", width=1410, height=810)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        dpg.toggle_viewport_fullscreen()

        # Автоматическая загрузка пресета, если имя передано в аргументах запуска
        if arg_name:
            presets = self.find_all_presets()
            target_preset = None
            arg_clean = arg_name.strip().strip('"\'')
            # 1. Поиск совпадения по имени файла или пути
            for p in presets:
                if arg_clean.lower() in p.lower() or os.path.basename(p).lower().startswith(arg_clean.lower()):
                    target_preset = p
                    break
            # 2. Поиск по нормализованному названию (замена пробелов на подчеркивания)
            if not target_preset:
                normalized_arg = arg_clean.lower().replace(" ", "_")
                for p in presets:
                    if normalized_arg in p.lower():
                        target_preset = p
                        break
            
            if target_preset:
                dpg.set_value("preset_combo", target_preset)
                self.load_preset_file(None, None)

        last_checked_selection = None
        while dpg.is_dearpygui_running():
            self.update_preview()
            self.update_timeline()

            current_nodes_sig = len(self.nodes_data)
            current_links_sig = len(self.links_data)
            if (not hasattr(self, "last_links_signature") or self.last_links_signature != current_links_sig or
                not hasattr(self, "last_nodes_signature") or self.last_nodes_signature != current_nodes_sig):
                self.last_links_signature = current_links_sig
                self.last_nodes_signature = current_nodes_sig
                self.rebuild_all_order_buttons()

            self.update_order_highlights()

            if self.current_loaded_file_path and os.path.exists(self.current_loaded_file_path):
                try:
                    mtime = os.path.getmtime(self.current_loaded_file_path)
                    if not hasattr(self, "last_file_mod_time"):
                        self.last_file_mod_time = mtime
                    if mtime > self.last_file_mod_time:
                        self.last_file_mod_time = mtime
                        print(f"[Live-Reload] Пресет изменен извне (Pygame). Перезагрузка графа...")
                        self.load_preset_file(None, None)
                except Exception:
                    pass

            selected = dpg.get_selected_nodes("editor_tag")
            if selected:
                active_sel = selected[0]
                if active_sel != last_checked_selection:
                    last_checked_selection = active_sel
                    self.rebuild_inspector(active_sel)

                    node = self.nodes_data.get(active_sel)
                    if node:
                        print(f"[Node Editor Log] Selected node: id={node.id}, type={node.type}, label='{node.label}'")
                        selection_info = None

                        if node.type == "Hitbox":
                            atk_node = None
                            p_in_hitbox = list(node.input_pins.keys())[0] if node.input_pins else None
                            if p_in_hitbox:
                                for lid, (p_out, p_in) in self.links_data.items():
                                    if p_in == p_in_hitbox:
                                        atk_node_id = self.pin_to_node.get(p_out)
                                        if atk_node_id and self.nodes_data.get(atk_node_id) and self.nodes_data[atk_node_id].type == "Attack":
                                            atk_node = self.nodes_data[atk_node_id]
                                            break
                            if atk_node:
                                sorted_attacks = sorted([n for n in self.nodes_data.values() if n.type == "Attack"], key=lambda x: dpg.get_item_pos(x.id)[1])
                                try:
                                    atk_idx = sorted_attacks.index(atk_node)
                                    p_hitboxes_out = list(atk_node.output_pins.keys())[0]
                                    connected_hitboxes = []
                                    for _, (p_out, p_in) in self.links_data.items():
                                        if p_out == p_hitboxes_out:
                                            hb_node_id = self.pin_to_node.get(p_in)
                                            if hb_node_id and self.nodes_data.get(hb_node_id) and self.nodes_data[hb_node_id].type == "Hitbox":
                                                connected_hitboxes.append(self.nodes_data[hb_node_id])
                                    connected_hitboxes.sort(key=lambda x: x.properties.get("delay", 0))
                                    hb_idx = connected_hitboxes.index(node)

                                    selection_info = {
                                        "preset_name": dpg.get_value("preset_combo"),
                                        "inspector_tab": "DETAILED_ATTACK",
                                        "attack_idx": atk_idx,
                                        "box_idx": hb_idx
                                    }
                                except ValueError as ve:
                                    print(f"[Node Editor Error] Failed to resolve index in lists: {ve}")

                        elif node.type == "Sequence":
                            sorted_sequences = sorted([n for n in self.nodes_data.values() if n.type == "Sequence"], key=lambda x: dpg.get_item_pos(x.id)[1])
                            if node in sorted_sequences:
                                seq_idx = sorted_sequences.index(node)
                                selection_info = {
                                    "preset_name": dpg.get_value("preset_combo"),
                                    "inspector_tab": "K-FRAMES",
                                    "seq_idx": seq_idx
                                }

                        elif node.type == "Flow":
                            sorted_flows = sorted([n for n in self.nodes_data.values() if n.type == "Flow"], key=lambda x: dpg.get_item_pos(x.id)[1])
                            if node in sorted_flows:
                                flow_idx = sorted_flows.index(node)
                                selection_info = {
                                    "preset_name": dpg.get_value("preset_combo"),
                                    "inspector_tab": "DETAILED_FLOW",
                                    "flow_idx": flow_idx
                                }

                        elif node.type == "Root":
                            selection_info = {
                                "preset_name": dpg.get_value("preset_combo"),
                                "inspector_tab": "MAIN"
                            }

                        elif node.type == "Order":
                            sorted_orders = sorted([n for n in self.nodes_data.values() if n.type == "Order"], key=lambda x: dpg.get_item_pos(x.id)[1])
                            if node in sorted_orders:
                                order_idx = sorted_orders.index(node)
                                selection_info = {
                                    "preset_name": dpg.get_value("preset_combo"),
                                    "inspector_tab": "DETAILED_ORDER",
                                    "order_idx": order_idx
                                }

                        if selection_info:
                            try:
                                with open(".editor_selection.json", "w", encoding="utf-8") as sf:
                                    json.dump(selection_info, sf, indent=4)
                            except Exception as ex:
                                print(f"[Node Editor Error] Failed to write .editor_selection.json: {ex}")
            dpg.render_dearpygui_frame()
            time.sleep(0.016)

        dpg.destroy_context()
if __name__ == "__main__":
    editor = NodeEditor()
    editor.setup_ui()
    
    start_arg = sys.argv[1].strip() if len(sys.argv) > 1 else None
    editor.run(start_arg)