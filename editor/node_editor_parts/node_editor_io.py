# editor/node_editor_parts/node_editor_io.py
import json
import os
import dearpygui.dearpygui as dpg
from editor.node_editor_parts.node_editor_io_import import NodeEditorIOImportMixin
from editor.node_editor_parts.node_editor_io_export import NodeEditorIOExportMixin

class NodeEditorIOMixin(NodeEditorIOImportMixin, NodeEditorIOExportMixin):
    def sync_with_dpg(self):
        """
        Вспомогательный метод для синхронизации Dear PyGui с внутренними структурами данных.
        Поскольку свойства обновляются мгновенно через соответствующие callbacks,
        данный метод может оставаться пустым.
        """
        pass

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