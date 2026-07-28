# editor/node_editor_parts/node_editor_timeline.py
import dearpygui.dearpygui as dpg

class NodeEditorTimelineMixin:
    def update_timeline(self):
        if not dpg.does_item_exist("timeline_drawlist"):
            return
            
        dpg.delete_item("timeline_drawlist", children_only=True)
        
        # Получаем активный выделенный узел
        node = self.nodes_data.get(self.active_selected_node_id) if self.active_selected_node_id else None
        
        # Если выделен хитбокс, находим родительскую атаку
        if node and node.type == "Hitbox":
            p_in_hitbox = list(node.input_pins.keys())[0] if node.input_pins else None
            for lid, (p_out, p_in) in self.links_data.items():
                if p_in == p_in_hitbox:
                    atk_id = self.pin_to_node.get(p_out)
                    if atk_id and self.nodes_data.get(atk_id) and self.nodes_data[atk_id].type == "Attack":
                        # Находим последовательность, к которой прилинкована эта атака
                        p_atk_in = list(self.nodes_data[atk_id].input_pins.keys())[0]
                        for lid2, (p_out2, p_in2) in self.links_data.items():
                            if p_in2 == p_atk_in:
                                seq_id = self.pin_to_node.get(p_out2)
                                if seq_id and self.nodes_data.get(seq_id) and self.nodes_data[seq_id].type == "Sequence":
                                    node = self.nodes_data[seq_id]
                                    break
                        break

        # Отрисовка пустого состояния, если не выделена последовательность
        if not node or node.type != "Sequence":
            dpg.draw_text(
                pos=[15, 45], 
                text="Select any Sequence node\nto view its frame timeline.", 
                color=[140, 140, 150, 200], 
                size=12, 
                parent="timeline_drawlist"
            )
            return

        # Находим и группируем все шаги Sequence на основе линков ее выходящих пинов
        steps = []
        for pin_id in node.properties.get("steps_pins", []):
            pin_prop = node.output_pins[pin_id].properties
            step_delay = pin_prop["delay"]
            step_index = pin_prop["index"]
            
            linked_act = None
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == pin_id:
                    act_id = self.pin_to_node.get(p_in)
                    if act_id and self.nodes_data.get(act_id) and self.nodes_data[act_id].type in ("Attack", "Movement", "Projectile"):
                        linked_act = self.nodes_data[act_id]
                        break
            steps.append({
                "pin_id": pin_id,
                "index": step_index,
                "delay": step_delay,
                "node": linked_act
            })

        # Вспомогательная функция вычисления длительности действия
        def get_step_duration(step_node):
            if not step_node:
                return 10
            stype = step_node.type
            if stype == "Attack":
                windup = step_node.properties.get("windup", 35)
                p_hitboxes_out = list(step_node.output_pins.keys())[0]
                connected_hitboxes = []
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == p_hitboxes_out:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id) and self.nodes_data[hb_id].type == "Hitbox":
                            connected_hitboxes.append(self.nodes_data[hb_id])
                total_dur = max([hb.properties.get("delay", 0) + hb.properties.get("duration", 10) for hb in connected_hitboxes]) if connected_hitboxes else 15
                return windup + total_dur
            elif stype == "Movement":
                p_phases_out = list(step_node.output_pins.keys())[0]
                connected_phases = []
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == p_phases_out:
                        ph_id = self.pin_to_node.get(p_in)
                        if ph_id and self.nodes_data.get(ph_id) and self.nodes_data[ph_id].type == "Phase":
                            connected_phases.append(self.nodes_data[ph_id])
                durations = []
                for ph in connected_phases:
                    p_dur = 1 if ph.properties.get("direction") == "teleport" else ph.properties.get("duration", 15)
                    durations.append(ph.properties.get("delay", 0) + p_dur)
                return max(durations) if durations else 15
            elif stype == "Projectile":
                return 8
            return 10

        # Рассчитываем общую длину шкалы времени
        total_duration = max([s["delay"] + get_step_duration(s["node"]) for s in steps]) if steps else 60
        scale_max = max(60, total_duration)

        bar_x = 10
        bar_y = 10
        bar_w = 280
        bar_h = 75

        # Фон сетки таймлайна
        dpg.draw_rectangle(pmin=[bar_x, bar_y], pmax=[bar_x + bar_w, bar_y + bar_h], fill=[15, 15, 20, 255], color=[50, 50, 60, 255], parent="timeline_drawlist")

        # Отрисовка временной шкалы и разметки кадров
        for f in range(0, scale_max + 1, 20):
            grid_x = bar_x + (f / scale_max) * bar_w
            dpg.draw_line(p1=[grid_x, bar_y], p2=[grid_x, bar_y + bar_h], color=[35, 35, 40, 255], thickness=1, parent="timeline_drawlist")
            if f % 40 == 0 or f == scale_max:
                dpg.draw_text(pos=[grid_x - 6, bar_y + bar_h + 3], text=str(f), color=[100, 100, 100, 255], size=9, parent="timeline_drawlist")

        # Отрисовка полос шагов
        step_row_height = 12
        for s_idx, s in enumerate(steps):
            delay = s["delay"]
            step_node = s["node"]
            duration = get_step_duration(step_node)
            
            row_y = bar_y + 4 + (s_idx % 4) * 17
            is_current = (self.active_selected_node_id == (step_node.id if step_node else None))
            
            if step_node and step_node.type == "Attack":
                windup = step_node.properties.get("windup", 35)
                p_hitboxes_out = list(step_node.output_pins.keys())[0]
                connected_hitboxes = []
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == p_hitboxes_out:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id) and self.nodes_data[hb_id].type == "Hitbox":
                            connected_hitboxes.append(self.nodes_data[hb_id])
                total_dur = max([hb.properties.get("delay", 0) + hb.properties.get("duration", 10) for hb in connected_hitboxes]) if connected_hitboxes else 15
                
                tx = bar_x + (delay / scale_max) * bar_w
                tw = (windup / scale_max) * bar_w
                
                ax = bar_x + ((delay + windup) / scale_max) * bar_w
                aw = (total_dur / scale_max) * bar_w
                
                # Подготовка атаки (windup) - оранжевый
                dpg.draw_rectangle(pmin=[tx, row_y], pmax=[tx + tw, row_y + step_row_height], fill=[255, 140, 0, 150], color=[255, 140, 0, 255] if is_current else [150, 80, 0, 200], parent="timeline_drawlist")
                # Активная фаза действия (хитбоксы) - красный
                dpg.draw_rectangle(pmin=[ax, row_y], pmax=[ax + aw, row_y + step_row_height], fill=[255, 60, 60, 180], color=[255, 60, 60, 255] if is_current else [180, 40, 40, 200], parent="timeline_drawlist")
                
                label = f"{step_node.properties.get('name', 'Attack')} (Step {s['index']})"
                dpg.draw_text(pos=[tx + 5, row_y - 1], text=label, color=[255, 255, 255, 220], size=10, parent="timeline_drawlist")
                
            elif step_node and step_node.type == "Movement":
                mx_start = bar_x + (delay / scale_max) * bar_w
                mw = (duration / scale_max) * bar_w
                
                # Фаза перемещения - синий
                dpg.draw_rectangle(pmin=[mx_start, row_y], pmax=[mx_start + mw, row_y + step_row_height], fill=[45, 85, 140, 150], color=[75, 130, 160, 255] if is_current else [45, 85, 140, 200], parent="timeline_drawlist")
                
                label = f"{step_node.properties.get('name', 'Movement')} (Step {s['index']})"
                dpg.draw_text(pos=[mx_start + 5, row_y - 1], text=label, color=[255, 255, 255, 220], size=10, parent="timeline_drawlist")
                
            elif step_node and step_node.type == "Projectile":
                px_start = bar_x + (delay / scale_max) * bar_w
                pw = (duration / scale_max) * bar_w
                
                # Фаза стрельбы снарядом - фиолетовый
                dpg.draw_rectangle(pmin=[px_start, row_y], pmax=[px_start + pw, row_y + step_row_height], fill=[105, 55, 140, 150], color=[105, 55, 140, 255] if is_current else [80, 40, 110, 200], parent="timeline_drawlist")
                
                label = f"{step_node.properties.get('name', 'Projectile')} (Step {s['index']})"
                dpg.draw_text(pos=[px_start + 5, row_y - 1], text=label, color=[255, 255, 255, 220], size=10, parent="timeline_drawlist")
            else:
                # Слот шага без связи
                ux_start = bar_x + (delay / scale_max) * bar_w
                uw = (10 / scale_max) * bar_w
                dpg.draw_rectangle(pmin=[ux_start, row_y], pmax=[ux_start + uw, row_y + step_row_height], fill=[40, 40, 45, 100], color=[80, 80, 85, 120], parent="timeline_drawlist")
                label = f"Unlinked (Step {s['index']})"
                dpg.draw_text(pos=[ux_start + 5, row_y - 1], text=label, color=[150, 150, 150, 180], size=10, parent="timeline_drawlist")