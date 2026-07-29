# tests/test_node_editor.py
import sys
from unittest.mock import MagicMock

# Полностью изолируем модуль dearpygui перед импортом редактора,
# чтобы тесты могли выполняться без установки C++ библиотек GUI.
sys.modules['dearpygui'] = MagicMock()
sys.modules['dearpygui.dearpygui'] = MagicMock()

import unittest
from editor.node_editor import NodeEditor
from editor.node_editor_parts.node_editor_state import NodeData, PinData

# Импортируем мок напрямую из пространства имен инспектора для точной проверки вызовов
from editor.node_editor_parts.node_editor_inspector import dpg as dpg_mock

class TestNodeEditorLogic(unittest.TestCase):
    def setUp(self):
        # Очищаем вызовы мока перед каждым тестом
        dpg_mock.reset_mock()
        
        # Настраиваем генератор уникальных ID для Dear PyGui функций,
        # чтобы вызовы add_node, add_node_attribute и т.д. возвращали разные значения
        # вместо одного и того же Mock-объекта (что приводило к перезаписи ключей в словарях)
        id_counter = 0
        def get_unique_id(*args, **kwargs):
            nonlocal id_counter
            id_counter += 1
            return id_counter
            
        dpg_mock.add_node.side_effect = get_unique_id
        dpg_mock.add_node_attribute.side_effect = get_unique_id
        dpg_mock.add_node_link.side_effect = get_unique_id

        # Динамические моки для метода sync_with_dpg, чтобы он не удалял созданные ноды и линки
        def get_item_children_mock(tag, slot):
            if tag == "editor_tag":
                if slot == 1:  # mvNode
                    return list(self.editor.nodes_data.keys())
                elif slot == 0:  # mvNodeLink
                    return list(self.editor.links_data.keys())
            return []

        def get_item_type_mock(item):
            if item in self.editor.nodes_data:
                return "mvAppItemType::mvNode"
            if item in self.editor.links_data:
                return "mvAppItemType::mvNodeLink"
            return ""

        dpg_mock.get_item_children.side_effect = get_item_children_mock
        dpg_mock.get_item_type.side_effect = get_item_type_mock
        dpg_mock.does_item_exist.return_value = True

        self.editor = NodeEditor()

    def test_node_and_pin_data_structures(self):
        """Проверка корректности хранения данных в структурах NodeData и PinData."""
        node = NodeData(node_id=10, node_type="Attack", label="Melee")
        self.assertEqual(node.id, 10)
        self.assertEqual(node.type, "Attack")
        self.assertEqual(node.label, "Melee")
        
        pin = PinData(pin_id=101, pin_type="Input", label="Trigger", data_type="Exec")
        self.assertEqual(pin.id, 101)
        self.assertEqual(pin.pin_type, "Input")
        self.assertEqual(pin.data_type, "Exec")

    def test_link_callback_validation(self):
        """Проверка логики валидации связей между пинами."""
        # Регистрируем тестовые пины в реестре редактора
        # Случай 1: Валидное соединение (один тип данных, разные направления)
        self.editor.pins_registry[101] = {"node_id": 1, "type": "Exec", "direction": "Output"}
        self.editor.pins_registry[102] = {"node_id": 2, "type": "Exec", "direction": "Input"}
        
        # Случай 2: Невалидное соединение (одинаковое направление)
        self.editor.pins_registry[201] = {"node_id": 1, "type": "Exec", "direction": "Output"}
        self.editor.pins_registry[202] = {"node_id": 2, "type": "Exec", "direction": "Output"}

        # Случай 3: Невалидное соединение (разные типы данных)
        self.editor.pins_registry[301] = {"node_id": 1, "type": "Behavior", "direction": "Output"}
        self.editor.pins_registry[302] = {"node_id": 2, "type": "Exec", "direction": "Input"}

        # Очищаем историю вызовов, накопившуюся при инициализации тем в setUp
        dpg_mock.add_node_link.reset_mock()

        # Проверяем Случай 1 (должен создаться линк: 101 -> 102)
        self.editor.link_callback("editor_tag", (101, 102))
        dpg_mock.add_node_link.assert_called_with(101, 102, parent="editor_tag")
        
        # Сбрасываем историю для проверки невалидных случаев
        dpg_mock.add_node_link.reset_mock()

        # Проверяем невалидный случай 2 (линк не должен создаваться)
        self.editor.link_callback("editor_tag", (201, 202))
        dpg_mock.add_node_link.assert_not_called()

        # Проверяем невалидный случай 3 (линк не должен создаваться)
        self.editor.link_callback("editor_tag", (301, 302))
        dpg_mock.add_node_link.assert_not_called()

    def test_hit_test_shape_circle(self):
        """Проверка математики хит-тестинга кликов по кругу в превью."""
        # Формат info: (shape_type, w, h, r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape)
        circle_info = ("circle", 0, 0, 50, 0, 0, 0.0, "following", 100, 100)

        # 1. Клик точно в центр круга (100, 100) -> должен вернуть перемещение ('move')
        mode_center = self.editor._hit_test_shape(circle_info, 100, 100)
        self.assertEqual(mode_center, "move")

        # 2. Клик ближе к краю (140, 100) (расстояние 40 из 50) -> должен вернуть изменение размера ('resize_circle')
        mode_edge = self.editor._hit_test_shape(circle_info, 140, 100)
        self.assertEqual(mode_edge, "resize_circle")

        # 3. Клик далеко за пределами круга (200, 200) -> должен вернуть None
        mode_outside = self.editor._hit_test_shape(circle_info, 200, 200)
        self.assertIsNone(mode_outside)

    def test_hit_test_shape_rectangle(self):
        """Проверка математики хит-тестинга кликов по прямоугольнику в превью."""
        # Прямоугольник шириной 100 и высотой 50 с центром в (100, 100) без поворота
        rect_info = ("rectangle", 100, 50, 0, 0, 0, 0.0, "following", 100, 100)

        # 1. Клик в центр (100, 100) -> должен вернуть перемещение ('move')
        mode_center = self.editor._hit_test_shape(rect_info, 100, 100)
        self.assertEqual(mode_center, "move")

        # 2. Клик по правому краю (145, 100) -> изменение размера вправо ('resize_right')
        mode_right = self.editor._hit_test_shape(rect_info, 145, 100)
        self.assertEqual(mode_right, "resize_right")

        # 3. Клик по левому краю (55, 100) -> изменение размера влево ('resize_left')
        mode_left = self.editor._hit_test_shape(rect_info, 55, 100)
        self.assertEqual(mode_left, "resize_left")

        # 4. Клик в область угла (например, верхний правый угол 145, 78) -> поворот ('rotate')
        mode_corner = self.editor._hit_test_shape(rect_info, 145, 78)
        self.assertEqual(mode_corner, "rotate")

    def test_import_export_json_roundtrip(self):
        """Проверка полного цикла импорта из JSON и последующего экспорта в граф."""
        preset_data = {
            "hp": 5,
            "name": "Export Test Enemy",
            "body": {"w": 40, "h": 60},
            "movement_config": {"type_move": "walking", "speed": 1.2},
            "attacks": [
                {
                    "name": "Jab", "cooldown": 30, "windup": 10,
                    "shapes": [{"shape": {"type": "rectangle", "w": 30, "h": 20}, "offset_x": 10, "offset_y": 0}]
                }
            ]
        }
        self.editor.import_json_to_graph(preset_data)
        exported = self.editor.export_graph_to_json()
        
        self.assertIsNotNone(exported)
        self.assertEqual(exported["hp"], 5)
        self.assertEqual(len(exported["attacks"]), 1)
        self.assertEqual(exported["attacks"][0]["name"], "Jab")

    def test_auto_arrange(self):
        """Проверка вызова метода авто-расстановки узлов на холсте."""
        self.editor.create_root_node()
        self.editor.create_attack_node()
        self.editor.auto_arrange()
        self.assertTrue(dpg_mock.set_item_pos.called)

    def test_export_structure_without_root(self):
        """Проверка того, что экспорт возвращает None, если отсутствует узел Root."""
        self.editor.nodes_data.clear()
        exported = self.editor.export_graph_to_json()
        self.assertIsNone(exported)

if __name__ == "__main__":
    unittest.main()