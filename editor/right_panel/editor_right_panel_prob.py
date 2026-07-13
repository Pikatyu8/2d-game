# editor/right_panel/editor_right_panel_prob.py
import pygame
from config import BORDER_COLOR
from core.physics import shapes_intersect

class RightPanelProbTabMixin:
    def normalize_pool_indices(self, sequences, pool):
        """Принудительно нормализует вероятности в случайном пуле, чтобы их сумма всегда равнялась 1.0"""
        valid_indices = [idx for idx in pool if idx < len(sequences)]
        if not valid_indices:
            return
        
        current_sum = sum(sequences[idx].get("chance", 0.5) for idx in valid_indices)
        
        # Если сумма уже равна 1.0 (с небольшой погрешностью), нормализация не требуется
        if abs(current_sum - 1.0) < 0.001:
            return
            
        if current_sum == 0:
            share = round(1.0 / len(valid_indices), 2)
            for idx in valid_indices:
                sequences[idx]["chance"] = share
        else:
            for idx in valid_indices:
                raw_val = sequences[idx].get("chance", 0.5) / current_sum
                sequences[idx]["chance"] = round(raw_val, 2)
                
        # Корректируем погрешность округления на последнем элементе
        new_sum = sum(sequences[idx].get("chance", 0.0) for idx in valid_indices)
        diff = round(1.0 - new_sum, 2)
        if abs(diff) > 0.001:
            sequences[valid_indices[-1]]["chance"] = round(sequences[valid_indices[-1]]["chance"] + diff, 2)

    def draw_enemy_probability_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        sequences = target_enemy_raw.get("sequences", [])
        flows = target_enemy_raw.get("flows", [])
        
        # --- СЕКЦИЯ 1: ВНУТРЕННИЕ СЛУЧАЙНЫЕ ПУЛЫ ПОТОКОВ ---
        lbl_pools = self.font_ui.render("FLOW RANDOM POOLS", True, (255, 180, 100))
        game.screen.blit(lbl_pools, (1215, y_offset))
        y_offset += 25

        random_pools = []
        for f_idx, flow in enumerate(flows):
            for s_idx, step in enumerate(flow.get("steps", [])):
                if step.get("is_random", False) and step.get("seq_pool"):
                    # Автоматически нормализуем пул при отрисовке вкладки
                    self.normalize_pool_indices(sequences, step["seq_pool"])
                    
                    random_pools.append({
                        "flow_name": flow.get("name", f"Flow {f_idx+1}"),
                        "step_idx": s_idx,
                        "pool": step["seq_pool"]
                    })

        if not random_pools:
            none_pools = self.font_ui.render("No flows with random steps.", True, (120, 120, 120))
            game.screen.blit(none_pools, (1215, y_offset))
            y_offset += 25
        else:
            for p in random_pools:
                pool_lbl = self.font_ui.render(f"{p['flow_name']} (Step #{p['step_idx'] + 1}):", True, (255, 255, 255))
                game.screen.blit(pool_lbl, (1215, y_offset))
                y_offset += 18
                
                for seq_idx in p["pool"]:
                    if seq_idx < len(sequences):
                        seq = sequences[seq_idx]
                        name_lbl = self.font_ui.render(f"  {seq.get('name', f'Seq {seq_idx+1}')}", True, (180, 180, 180))
                        game.screen.blit(name_lbl, (1215, y_offset))
                        
                        val_text = f"{seq.get('chance', 0.5):.2f}"
                        btn_minus, btn_plus = self.draw_property_row("", val_text, y_offset)
                        
                        if mouse_clicked_this_frame:
                            if btn_minus.collidepoint(mouse_pos):
                                self.adjust_pool_chance(target_enemy_raw, p["pool"], seq_idx, -0.01)
                            if btn_plus.collidepoint(mouse_pos):
                                self.adjust_pool_chance(target_enemy_raw, p["pool"], seq_idx, 0.01)
                        
                        y_offset += 26
                y_offset += 10

        pygame.draw.line(game.screen, BORDER_COLOR, (1205, y_offset), (1395, y_offset), 1)
        y_offset += 15

        # --- СЕКЦИЯ 2: ВНЕШНИЕ ГЕОМЕТРИЧЕСКИЕ ПЕРЕКРЫТИЯ ---
        lbl_overlaps_title = self.font_ui.render("TRIGGER ZONE OVERLAPS", True, (255, 180, 100))
        game.screen.blit(lbl_overlaps_title, (1215, y_offset))
        y_offset += 25

        active_triggers = []
        for i, seq in enumerate(sequences):
            is_in_flow = any(
                i in step.get("seq_pool", []) or i == step.get("seq_idx", 0)
                for flow in flows
                for step in flow.get("steps", [])
            )
            if is_in_flow:
                continue

            active_triggers.append({
                "type": "sequence",
                "idx": i,
                "name": seq.get("name", f"Seq {i+1}"),
                "ref": seq,
                "shape_data": self.game.dummy_enemy.get_attack_zone_shape_for_attack_zone(i) if self.game.dummy_enemy else None
            })
        
        for j, flow in enumerate(flows):
            active_triggers.append({
                "type": "flow",
                "idx": j,
                "name": flow.get("name", f"Flow {j+1}"),
                "ref": flow,
                "shape_data": self.game.dummy_enemy.get_attack_zone_shape_for_flow_zone(j) if self.game.dummy_enemy else None
            })

        overlapping_ids = set()
        overlap_pairs = []
        for idx_a in range(len(active_triggers)):
            for idx_b in range(idx_a + 1, len(active_triggers)):
                ta = active_triggers[idx_a]
                tb = active_triggers[idx_b]
                if ta["shape_data"] and tb["shape_data"]:
                    type_a, val_a = ta["shape_data"]
                    type_b, val_b = tb["shape_data"]
                    if shapes_intersect(type_a, val_a, type_b, val_b):
                        overlapping_ids.add(idx_a)
                        overlapping_ids.add(idx_b)
                        overlap_pairs.append((ta, tb))

        if not overlapping_ids:
            none_lbl = self.font_ui.render("No active overlaps.", True, (120, 120, 120))
            game.screen.blit(none_lbl, (1215, y_offset))
            y_offset += 20
        else:
            for idx in sorted(list(overlapping_ids)):
                t = active_triggers[idx]
                name_lbl = self.font_ui.render(t["name"], True, (180, 180, 180))
                game.screen.blit(name_lbl, (1215, y_offset))
                
                val_text = f"{t['ref'].get('chance', 0.5):.2f}"
                btn_minus, btn_plus = self.draw_property_row("", val_text, y_offset)
                
                if mouse_clicked_this_frame:
                    if btn_minus.collidepoint(mouse_pos):
                        self.adjust_trigger_chance(target_enemy_raw, active_triggers, t["type"], t["idx"], -0.01)
                    if btn_plus.collidepoint(mouse_pos):
                        self.adjust_trigger_chance(target_enemy_raw, active_triggers, t["type"], t["idx"], 0.01)
                
                y_offset += 28

            y_offset += 10
            lbl_list = self.font_ui.render("INTERSECTIONS LIST:", True, (255, 100, 100))
            game.screen.blit(lbl_list, (1215, y_offset))
            y_offset += 20

            for ta, tb in overlap_pairs:
                pair_lbl = self.font_ui.render(f"{ta['name']} <-> {tb['name']}", True, (255, 120, 120))
                game.screen.blit(pair_lbl, (1215, y_offset))
                y_offset += 18

        return y_offset

    def adjust_pool_chance(self, target_enemy_raw, pool, seq_idx, delta):
        sequences = target_enemy_raw.get("sequences", [])
        valid_indices = [idx for idx in pool if idx < len(sequences)]
        if seq_idx not in valid_indices:
            return

        # Гарантируем, что пул изначально строго нормализован до 1.0
        self.normalize_pool_indices(sequences, valid_indices)

        target_seq = sequences[seq_idx]
        old_chance = target_seq.get("chance", 0.5)
        new_chance = max(0.0, min(1.0, round(old_chance + delta, 2)))
        target_seq["chance"] = new_chance

        other_indices = [idx for idx in valid_indices if idx != seq_idx]
        if other_indices:
            total_others = sum(sequences[idx].get("chance", 0.5) for idx in other_indices)
            target_remaining = round(1.0 - new_chance, 2)

            if total_others > 0:
                # Пропорционально перераспределяем остаток между другими элементами пула
                for idx in other_indices:
                    val = sequences[idx].get("chance", 0.5)
                    sequences[idx]["chance"] = round((val / total_others) * target_remaining, 2)
            else:
                # Если у других была нулевая вероятность, делим остаток поровну
                share = round(target_remaining / len(other_indices), 2)
                for idx in other_indices:
                    sequences[idx]["chance"] = share

            # Фиксируем микро-погрешность округления на последнем элементе
            current_sum = sum(sequences[idx].get("chance", 0.0) for idx in valid_indices)
            diff = round(1.0 - current_sum, 2)
            if abs(diff) > 0.001:
                sequences[other_indices[-1]]["chance"] = round(sequences[other_indices[-1]]["chance"] + diff, 2)
                
        self.game.rebuild_objects()

    def adjust_trigger_chance(self, target_enemy_raw, active_triggers, trigger_type, idx, delta):
        target_trig = None
        for t in active_triggers:
            if t["type"] == trigger_type and t["idx"] == idx:
                target_trig = t
                break
        
        if not target_trig:
            return
            
        old_chance = target_trig["ref"].get("chance", 0.5)
        new_chance = max(0.0, min(1.0, round(old_chance + delta, 2)))
        actual_delta = new_chance - old_chance
        if abs(actual_delta) < 0.001:
            return
            
        target_trig["ref"]["chance"] = new_chance
        
        overlapping_others = []
        if target_trig["shape_data"]:
            type_a, val_a = target_trig["shape_data"]
            for t in active_triggers:
                if t is target_trig:
                    continue
                if t["shape_data"]:
                    type_b, val_b = t["shape_data"]
                    if shapes_intersect(type_a, val_a, type_b, val_b):
                        overlapping_others.append(t)
        
        if overlapping_others:
            comp_delta = -actual_delta / len(overlapping_others)
            for ot in overlapping_others:
                ot_old = ot["ref"].get("chance", 0.5)
                ot["ref"]["chance"] = max(0.0, min(1.0, round(ot_old + comp_delta, 2)))
        
        self.game.rebuild_objects()