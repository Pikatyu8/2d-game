# editor/node_editor_parts/node_editor_state.py
import os

class NodeData:
    def __init__(self, node_id, node_type, label, properties=None):
        self.id = node_id
        self.type = node_type
        self.label = label
        self.properties = properties or {}
        self.input_pins = {}
        self.output_pins = {}

class PinData:
    def __init__(self, pin_id, pin_type, label, data_type, properties=None):
        self.id = pin_id
        self.pin_type = pin_type
        self.label = label
        self.data_type = data_type
        self.properties = properties or {}

class NodeEditorStateMixin:
    def init_state(self):
        self.nodes_data = {}
        self.links_data = {}
        self.pins_registry = {}
        self.pin_to_node = {}
        self.active_selected_node_id = None
        self.current_loaded_file_path = None
        
        # Переменные состояния интерактивного превью
        self.preview_dragging = False
        self.preview_drag_mode = None
        self.preview_drag_is_vis = False
        self.preview_drag_start_mouse = (0, 0)
        self.preview_drag_start_val = {}
        
        # Смещение и панорамирование холста превью
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0
        self.preview_canvas_panning = False
        self.preview_pan_start_mouse = (0, 0)
        self.preview_pan_start_val = (0.0, 0.0)

    def find_all_presets(self):
        presets = []
        enemies_dir = "enemies"
        if os.path.exists(enemies_dir):
            for root, _, files in os.walk(enemies_dir):
                for file in files:
                    if file.endswith(".json"):
                        presets.append(os.path.join(root, file))
        return sorted(presets)