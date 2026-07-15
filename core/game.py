# core/game.py
import pygame
import os
import copy
import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CANVAS_OFFSET_X, CANVAS_WIDTH, ensure_level_file
)
from core.game_parts.game_io import GameIOMixin
from core.game_parts.game_editor_logic import GameEditorLogicMixin
from entities.platform_class import Platform
from editor.editor_ui import EditorUI, PlayerStart

class Game(GameIOMixin, GameEditorLogicMixin):
    def __init__(self):
        pygame.init()
        
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        except Exception as e:
            print(f"Mixer init error: {e}")
            
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        ensure_level_file()
        self.platforms = []
        self.enemies = []
        self.projectiles = []  
        self.player = None
        self.gravity = 0.5
        self.flash_timer = 0
        self.show_debug = True
        
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0  
        
        self.left_panel_scroll = 0
        self.left_panel_max_scroll = 400
        self.right_panel_scroll = 0
        self.right_panel_max_scroll = 400
        
        self.editor_mode = "GAMEPLAY"   
        self.snap_to_grid = True        
        self.selected_brush = "Selection"  
        self.selected_instance = None   
        self.dragging_instance = None   
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
        self.available_levels = []
        self.current_level_name = "level_1.json"  
        
        self.inspector_tab = "MAIN"     
        self.selected_preset_name = None
        
        self.selected_trigger_idx = 0   
        self.selected_attack_edit_idx = 0 
        self.selected_box_idx = 0       
        self.selected_move_edit_idx = 0
        self.selected_projectile_edit_idx = 0  
        
        self.selected_seq_idx = 0
        self.selected_step_idx = 0
        
        self.dummy_platform = Platform({"x": 200, "y": 400, "w": CANVAS_WIDTH, "h": 20}, None)
        self.dummy_enemy = None
        self.player_start_obj = None
        
        self.raw_platforms = []
        self.raw_enemies = []
        self.raw_player_cfg = {}
        self.templates = {}
        self.presets = {}
        self.preset_filepaths = {}  
        
        self.hitstop_timer = 0
        self.sounds = {}
        
        self.font_cache = {}
        self.debug_alpha_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Переменные для выпадающих меню (Dropdowns)
        self.active_dropdown_id = None
        self.active_dropdown_data = None
        self.active_dropdown_selection = None
        self.dropdown_just_opened = False 
        
        # Переменные для перетаскивания/изменения размеров хитбоксов
        self.dragging_hitbox = False
        self.hitbox_drag_mode = None
        self.hitbox_drag_start_mouse = (0, 0)
        self.hitbox_drag_start_val = {}

        self.ui = EditorUI(self)
        self.load_level()

    def get_cached_font(self, size, bold=False):
        size = max(6, int(size))
        key = (size, bold)
        if key not in self.font_cache:
            self.font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
        return self.font_cache[key]

    def get_active_hitbox_rect_and_data(self):
        from entities.enemy import Enemy
        enemy = None
        if self.editor_mode == "ENEMY_EDITOR":
            enemy = self.dummy_enemy
        elif self.editor_mode == "LEVEL_EDITOR" and self.selected_instance and isinstance(self.selected_instance, Enemy):
            enemy = self.selected_instance
            
        if not enemy:
            return None
            
        target_enemy_raw = enemy.raw_data
        zoom = self.zoom if self.editor_mode == "LEVEL_EDITOR" else 1.0
        camera_x = self.camera_x if self.editor_mode == "LEVEL_EDITOR" else 0
        camera_y = self.camera_y if self.editor_mode == "LEVEL_EDITOR" else 0
        
        shape_dict = None
        parent_dict = None
        shape_data = None
        
        # Точное определение активной фигуры через геометрические функции класса Enemy
        if self.inspector_tab == "MAIN":
            parent_dict = target_enemy_raw.get("detection")
            if parent_dict:
                shape_dict = parent_dict.get("shape")
                shape_data = enemy.get_detection_shape()
        elif self.inspector_tab == "DETAILED_ATTACK":
            attacks = target_enemy_raw.get("attacks", [])
            if attacks and self.selected_attack_edit_idx < len(attacks):
                curr_att = attacks[self.selected_attack_edit_idx]
                shapes = curr_att.get("shapes", [])
                if shapes and self.selected_box_idx < len(shapes):
                    parent_dict = shapes[self.selected_box_idx]
                    shape_dict = parent_dict.get("shape")
                    shapes_data = enemy.get_attack_shapes_by_index(self.selected_attack_edit_idx)
                    if shapes_data and self.selected_box_idx < len(shapes_data):
                        shape_data = shapes_data[self.selected_box_idx]
        elif self.inspector_tab == "K-FRAMES":
            seq_list = target_enemy_raw.get("sequences", [])
            if seq_list and self.selected_seq_idx < len(seq_list):
                curr_seq = seq_list[self.selected_seq_idx]
                parent_dict = curr_seq.get("trigger_zone")
                if parent_dict:
                    shape_dict = parent_dict.get("shape")
                    shape_data = enemy.get_attack_zone_shape_for_attack_zone(self.selected_seq_idx)
        elif self.inspector_tab == "DETAILED_FLOW":
            flows = target_enemy_raw.get("flows", [])
            if flows and self.selected_flow_idx < len(flows):
                curr_flow = flows[self.selected_flow_idx]
                parent_dict = curr_flow.get("trigger_zone")
                if parent_dict:
                    shape_dict = parent_dict.get("shape")
                    shape_data = enemy.get_attack_zone_shape_for_flow_zone(self.selected_flow_idx)
                    
        if not shape_dict or not parent_dict or not shape_data:
            return None
            
        stype, val = shape_data
        
        if stype == "circle":
            cx, cy, r = val
            asx = CANVAS_OFFSET_X + (cx - r - camera_x) * zoom
            asy = (cy - r - camera_y) * zoom
            asw = r * 2 * zoom
            ash = r * 2 * zoom
        else: # rectangle
            rect, angle = val
            asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
            asy = (rect.y - camera_y) * zoom
            asw = rect.width * zoom
            ash = rect.height * zoom
            
        screen_rect = pygame.Rect(asx, asy, asw, ash)
        return {
            "screen_rect": screen_rect,
            "type": stype,
            "shape_dict": shape_dict,
            "parent_dict": parent_dict,
            "enemy": enemy,
            "zoom": zoom,
            "shape_data_val": val
        }

    def check_hitbox_interaction(self, mouse_pos, mouse_clicked):
        if not mouse_clicked:
            return False
            
        info = self.get_active_hitbox_rect_and_data()
        if not info:
            return False
            
        screen_rect = info["screen_rect"]
        stype = info["type"]
        shape_dict = info["shape_dict"]
        parent_dict = info["parent_dict"]
        enemy = info["enemy"]
        val = info["shape_data_val"]
        
        mx, my = mouse_pos
        
        if stype == "circle":
            cx, cy, r = val
            scx = screen_rect.centerx
            scy = screen_rect.centery
            sr = screen_rect.width / 2
            dist = math.hypot(mx - scx, my - scy)
            
            if dist <= sr:
                self.dragging_hitbox = True
                self.hitbox_drag_start_mouse = (mx, my)
                self.hitbox_drag_start_val = {
                    "offset_x": parent_dict.get("offset_x", 0),
                    "offset_y": parent_dict.get("offset_y", 0),
                    "r": shape_dict.get("r", 25),
                    "enemy_rect_x": enemy.rect.x,
                    "enemy_rect_y": enemy.rect.y,
                    "enemy_rect_w": enemy.rect.width,
                    "enemy_rect_h": enemy.rect.height,
                    "enemy_direction": enemy.direction,
                    "det_type": parent_dict.get("type", "following"),
                    "is_attack": (self.inspector_tab == "DETAILED_ATTACK"),
                    "abs_x": cx - r,
                    "abs_y": cy - r
                }
                if dist >= 0.8 * sr:
                    self.hitbox_drag_mode = "resize_circle"
                else:
                    self.hitbox_drag_mode = "move"
                return True
        else: # rectangle
            rect, angle = val
            if screen_rect.collidepoint(mx, my):
                self.dragging_hitbox = True
                self.hitbox_drag_start_mouse = (mx, my)
                self.hitbox_drag_start_val = {
                    "offset_x": parent_dict.get("offset_x", 0),
                    "offset_y": parent_dict.get("offset_y", 0),
                    "w": shape_dict.get("w", 50),
                    "h": shape_dict.get("h", 40),
                    "enemy_rect_x": enemy.rect.x,
                    "enemy_rect_y": enemy.rect.y,
                    "enemy_rect_w": enemy.rect.width,
                    "enemy_rect_h": enemy.rect.height,
                    "enemy_direction": enemy.direction,
                    "det_type": parent_dict.get("type", "following"),
                    "is_attack": (self.inspector_tab == "DETAILED_ATTACK"),
                    "abs_x": rect.x,
                    "abs_y": rect.y
                }
                
                rx = (mx - screen_rect.left) / screen_rect.width
                ry = (my - screen_rect.top) / screen_rect.height
                
                if rx <= 0.2:
                    self.hitbox_drag_mode = "resize_left"
                elif rx >= 0.8:
                    self.hitbox_drag_mode = "resize_right"
                elif ry <= 0.2:
                    self.hitbox_drag_mode = "resize_top"
                elif ry >= 0.8:
                    self.hitbox_drag_mode = "resize_bottom"
                else:
                    self.hitbox_drag_mode = "move"
                return True
        return False

    def update_hitbox_drag(self, mouse_pos):
        if not self.dragging_hitbox:
            return
            
        if not pygame.mouse.get_pressed()[0]:
            self.dragging_hitbox = False
            self.hitbox_drag_mode = None
            return
            
        info = self.get_active_hitbox_rect_and_data()
        if not info:
            self.dragging_hitbox = False
            self.hitbox_drag_mode = None
            return
            
        shape_dict = info["shape_dict"]
        parent_dict = info["parent_dict"]
        zoom = info["zoom"]
        stype = info["type"]
        
        mx, my = mouse_pos
        start_mx, start_my = self.hitbox_drag_start_mouse
        
        dx_world = (mx - start_mx) / zoom
        dy_world = (my - start_my) / zoom
        
        start_vals = self.hitbox_drag_start_val
        start_abs_x = start_vals["abs_x"]
        start_abs_y = start_vals["abs_y"]
        
        # Безопасная инициализация целевых координат
        new_abs_x = start_abs_x
        new_abs_y = start_abs_y
        
        if stype == "circle":
            # Считываем радиус безопасно внутри блока для кругов
            start_r = start_vals["r"]
            new_r = start_r
            
            if self.hitbox_drag_mode == "move":
                new_abs_x = start_abs_x + dx_world
                new_abs_y = start_abs_y + dy_world
            elif self.hitbox_drag_mode == "resize_circle":
                scx = info["screen_rect"].centerx
                scy = info["screen_rect"].centery
                sr_new = math.hypot(mx - scx, my - scy)
                new_r = max(5, int(sr_new / zoom))
                start_abs_cx = start_abs_x + start_r
                start_abs_cy = start_abs_y + start_r
                new_abs_x = start_abs_cx - new_r
                new_abs_y = start_abs_cy - new_r
                
            shape_dict["r"] = int(new_r)
            
        else: # rectangle
            # Считываем размеры безопасно внутри блока для прямоугольников
            start_w = start_vals["w"]
            start_h = start_vals["h"]
            new_w = start_w
            new_h = start_h
            
            if self.hitbox_drag_mode == "move":
                new_abs_x = start_abs_x + dx_world
                new_abs_y = start_abs_y + dy_world
            elif self.hitbox_drag_mode == "resize_right":
                new_w = max(5, start_w + dx_world)
            elif self.hitbox_drag_mode == "resize_left":
                new_w = max(5, start_w - dx_world)
                actual_dw = new_w - start_w
                new_abs_x = start_abs_x - actual_dw
            elif self.hitbox_drag_mode == "resize_bottom":
                new_h = max(5, start_h + dy_world)
            elif self.hitbox_drag_mode == "resize_top":
                new_h = max(5, start_h - dy_world)
                actual_dh = new_h - start_h
                new_abs_y = start_abs_y - actual_dh
                
            shape_dict["w"] = int(new_w)
            shape_dict["h"] = int(new_h)
            
        # Восстановление параметров врага и расчет новых смещений offset_x / offset_y
        enemy_rect_x = start_vals["enemy_rect_x"]
        enemy_rect_y = start_vals["enemy_rect_y"]
        enemy_rect_w = start_vals["enemy_rect_w"]
        enemy_rect_h = start_vals["enemy_rect_h"]
        enemy_rect_centerx = enemy_rect_x + enemy_rect_w / 2
        enemy_rect_centery = enemy_rect_y + enemy_rect_h / 2
        enemy_direction = start_vals["enemy_direction"]
        det_type = start_vals["det_type"]
        is_attack = start_vals["is_attack"]
        
        if stype == "circle":
            new_cx = new_abs_x + new_r
            new_cy = new_abs_y + new_r
            
            if is_attack:
                new_ox = (new_cx - enemy_rect_centerx) * enemy_direction
                new_oy = new_cy - enemy_rect_centery
            else:
                if det_type == "following" and enemy_direction == -1:
                    new_ox = enemy_rect_centerx - new_cx
                else:
                    new_ox = new_cx - enemy_rect_centerx
                new_oy = new_cy - enemy_rect_centery
        else: # rectangle
            if is_attack:
                new_ox = (new_abs_x + new_w / 2 - enemy_rect_centerx) * enemy_direction
                new_oy = new_abs_y + new_h / 2 - enemy_rect_centery
            else:
                if det_type == "following" and enemy_direction == -1:
                    new_ox = enemy_rect_x - new_abs_x - new_w
                elif det_type == "following" and enemy_direction == 1:
                    new_ox = new_abs_x - (enemy_rect_x + enemy_rect_w)
                else:
                    new_ox = new_abs_x - enemy_rect_centerx + new_w / 2
                new_oy = new_abs_y - enemy_rect_y
                
        parent_dict["offset_x"] = int(new_ox)
        parent_dict["offset_y"] = int(new_oy)
        
        self.rebuild_objects()

    def play_sound(self, sound_name):
        if not pygame.mixer or not pygame.mixer.get_init():
            return
            
        if sound_name not in self.sounds:
            os.makedirs("assets", exist_ok=True)
            sound_file = os.path.join("assets", f"{sound_name}.wav")
            
            if os.path.exists(sound_file):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_file)
                except Exception as e:
                    print(f"Error loading sound {sound_file}: {e}")
                    self.sounds[sound_name] = None
            else:
                import array
                import math
                sample_rate = 44100
                audio_data = array.array('h')
                
                if sound_name == "parry":
                    duration_ms = 150
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-15 * t)
                        freq = 900 + 400 * (1.0 - t)
                        val = int(25000 * math.sin(2 * math.pi * freq * t) * decay)
                        audio_data.append(val)
                elif sound_name == "damage":
                    duration_ms = 200
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-12 * t)
                        freq = 150 - 60 * t
                        val = int(22000 * math.sin(2 * math.pi * freq * t) * decay)
                        audio_data.append(val)
                else:
                    duration_ms = 100
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-10 * t)
                        val = int(15000 * math.sin(2 * math.pi * 440 * t) * decay)
                        audio_data.append(val)
                        
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(buffer=bytes(audio_data))
                except Exception as e:
                    print(f"Error creating procedural sound {sound_name}: {e}")
                    self.sounds[sound_name] = None
                    
        sound_obj = self.sounds.get(sound_name)
        if sound_obj:
            try:
                sound_obj.play()
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")

    def spawn_projectile(self, x, y, vx, vy, damage=1, radius=8, gravity=0.0, homing=0.0):
        from entities.projectile import Projectile
        self.projectiles.append(Projectile(x, y, vx, vy, damage, radius, gravity, homing))

    def prompt_text_input(self, title, prompt, initial_value=""):
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        result = simpledialog.askstring(title, prompt, initialvalue=initial_value)
        root.destroy()
        return result

    def run(self):
        running = True
        while running:
            self.clock.tick(60)  
            mouse_clicked_this_frame = False
            right_clicked_this_frame = False
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_clicked_this_frame = True
                    elif event.button == 3:
                        right_clicked_this_frame = True
                    elif event.button == 4:
                        if 0 <= mouse_pos[0] < CANVAS_OFFSET_X:
                            self.left_panel_scroll = max(0, self.left_panel_scroll - 30)
                        elif 1200 <= mouse_pos[0] <= 1400:
                            self.right_panel_scroll = max(0, self.right_panel_scroll - 30)
                        elif self.editor_mode == "LEVEL_EDITOR" and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                            self.zoom = min(3.0, self.zoom + 0.1)
                    elif event.button == 5:
                        if 0 <= mouse_pos[0] < CANVAS_OFFSET_X:
                            max_scroll_l = getattr(self, "left_panel_max_scroll", 400)
                            self.left_panel_scroll = min(max_scroll_l, self.left_panel_scroll + 30)
                        elif 1200 <= mouse_pos[0] <= 1400:
                            max_scroll_r = getattr(self, "right_panel_max_scroll", 400)
                            self.right_panel_scroll = min(max_scroll_r, self.right_panel_scroll + 30)
                        elif self.editor_mode == "LEVEL_EDITOR" and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                            self.zoom = max(0.3, self.zoom - 0.1)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging_instance = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        self.left_panel_scroll = 0
                        self.right_panel_scroll = 0
                        if self.editor_mode == "GAMEPLAY":
                            self.editor_mode = "LEVEL_EDITOR"
                        elif self.editor_mode == "LEVEL_EDITOR":
                            self.editor_mode = "ENEMY_EDITOR"
                            self.zoom = 1.0  
                            self.selected_attack_edit_idx = 0
                            self.selected_box_idx = 0
                        else:
                            self.editor_mode = "GAMEPLAY"
                            self.zoom = 1.0
                            if self.player:
                                self.player.respawn(self)
                        self.rebuild_objects()
                    elif event.key == pygame.K_r:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_SHIFT:
                            self.load_level()
                        else:
                            if self.player:
                                self.player.respawn(self)
                    elif event.key == pygame.K_TAB:
                        self.show_debug = not self.show_debug

            # Обработка приоритетного перетаскивания активного хитбокса
            if self.editor_mode in ("ENEMY_EDITOR", "LEVEL_EDITOR") and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                if self.dragging_hitbox:
                    self.update_hitbox_drag(mouse_pos)
                else:
                    hitbox_clicked = self.check_hitbox_interaction(mouse_pos, mouse_clicked_this_frame)
                    if hitbox_clicked:
                        # Поглощаем клик, чтобы не сбить выделение на сцене
                        mouse_clicked_this_frame = False

            if self.editor_mode == "GAMEPLAY" and self.player:
                if self.hitstop_timer > 0:
                    self.hitstop_timer -= 1
                else:
                    self.player.handle_input()
                    self.player.update(self.platforms, self.enemies, self)
                    self.projectiles = [p for p in self.projectiles if not p.update(self.platforms, self.player, self)]
                    for enemy in self.enemies:
                        enemy.update(self.platforms, self.gravity, self.player, self)
                    self.enemies = [e for e in self.enemies if e.hp > 0]
                
                target_cam_x = self.player.rect.centerx - CANVAS_WIDTH // 2
                target_cam_y = self.player.rect.centery - SCREEN_HEIGHT // 2
                self.camera_x += (target_cam_x - self.camera_x) * 0.1
                self.camera_y += (target_cam_y - self.camera_y) * 0.1
                self.camera_x = max(0, self.camera_x)

            if self.flash_timer > 0:
                self.screen.fill((40, 70, 40))
                self.flash_timer -= 1
            else:
                self.screen.fill((20, 20, 25))
            
            game_canvas_rect = pygame.Rect(CANVAS_OFFSET_X, 0, CANVAS_WIDTH, SCREEN_HEIGHT)
            pygame.draw.rect(self.screen, (30, 30, 30), game_canvas_rect)
            
            self.debug_alpha_surf.fill((0, 0, 0, 0))

            editing_trig_idx = None
            editing_atk_idx = None
            editing_box_idx = None
            target_enemy_raw = None
            if self.editor_mode == "ENEMY_EDITOR" and self.selected_preset_name:
                target_enemy_raw = self.presets.get(self.selected_preset_name)
            elif self.editor_mode == "LEVEL_EDITOR" and self.selected_instance:
                if not isinstance(self.selected_instance, (Platform, PlayerStart)):
                    target_enemy_raw = self.selected_instance.raw_data

            if target_enemy_raw is not None:
                if self.inspector_tab == "K-FRAMES":
                    editing_trig_idx = self.selected_seq_idx
                elif self.inspector_tab == "DETAILED_ATTACK":
                    editing_atk_idx = self.selected_attack_edit_idx
                    editing_box_idx = self.selected_box_idx
            
            if self.editor_mode == "ENEMY_EDITOR":
                self.dummy_platform.draw(self.screen, CANVAS_OFFSET_X)
                if self.dummy_enemy:
                    p_fake = pygame.Rect(-100, -100, 0, 0)
                    self.dummy_enemy.draw(
                        surface=self.screen,
                        show_debug=True,
                        player_rect=p_fake,
                        camera_x=0,
                        camera_y=0,
                        zoom=1.0,
                        editing_trigger_idx=editing_trig_idx,
                        editing_attack_idx=editing_atk_idx,
                        editing_box_idx=editing_box_idx,
                        inspector_tab=self.inspector_tab,
                        selected_move_idx=self.selected_move_edit_idx,
                        alpha_surf=self.debug_alpha_surf,
                        game=self
                    )
            else:
                current_zoom = self.zoom if self.editor_mode == "LEVEL_EDITOR" else 1.0

                if self.editor_mode == "LEVEL_EDITOR" and self.snap_to_grid:
                    grid_size = int(40 * current_zoom)
                    if grid_size >= 4:
                        start_grid_x = CANVAS_OFFSET_X - (int(self.camera_x * current_zoom) % grid_size)
                        start_grid_y = - (int(self.camera_y * current_zoom) % grid_size)
                        
                        for x in range(start_grid_x, CANVAS_OFFSET_X + CANVAS_WIDTH, grid_size):
                            if x >= CANVAS_OFFSET_X:
                                pygame.draw.line(self.screen, (40, 40, 45), (x, 0), (x, SCREEN_HEIGHT))
                        for y in range(start_grid_y, SCREEN_HEIGHT, grid_size):
                            if y >= 0:
                                pygame.draw.line(self.screen, (40, 40, 45), (CANVAS_OFFSET_X, y), (CANVAS_OFFSET_X + CANVAS_WIDTH, y))

                for plat in self.platforms:
                    plat.draw(self.screen, self.camera_x, self.camera_y, current_zoom)
                    
                for enemy in self.enemies:
                    p_rect = self.player.rect if self.player else pygame.Rect(0, 0, 0, 0)
                    enemy.draw(
                        surface=self.screen,
                        show_debug=self.show_debug or (self.editor_mode == "LEVEL_EDITOR"),
                        player_rect=p_rect,
                        camera_x=self.camera_x,
                        camera_y=self.camera_y,
                        zoom=current_zoom,
                        editing_trigger_idx=editing_trig_idx,
                        editing_attack_idx=editing_atk_idx,
                        editing_box_idx=editing_box_idx,
                        inspector_tab=self.inspector_tab,
                        selected_move_idx=self.selected_move_edit_idx,
                        alpha_surf=self.debug_alpha_surf,
                        game=self
                    )
                    
                for proj in self.projectiles:
                    proj.draw(self.screen, self.camera_x, self.camera_y, current_zoom)
                    
                if self.player:
                    self.player.draw(self.screen, self.camera_x, self.camera_y, current_zoom)

                if self.editor_mode == "LEVEL_EDITOR" and self.player_start_obj:
                    start_sx = CANVAS_OFFSET_X + (self.player_start_obj.rect.x - self.camera_x) * current_zoom
                    start_sy = (self.player_start_obj.rect.y - self.camera_y) * current_zoom
                    start_sw = self.player_start_obj.rect.width * current_zoom
                    start_sh = self.player_start_obj.rect.height * current_zoom
                    
                    pygame.draw.rect(self.screen, (0, 240, 255), (start_sx, start_sy, start_sw, start_sh), 2)
                    font_start_size = max(8, int(14 * current_zoom))
                    font_start = self.get_cached_font(font_start_size)
                    start_lbl = font_start.render("SPAWN", True, (0, 240, 255))
                    self.screen.blit(start_lbl, (start_sx + 3 * current_zoom, start_sy + 4 * current_zoom))

                if self.editor_mode == "LEVEL_EDITOR" and self.selected_instance:
                    sel_sx = CANVAS_OFFSET_X + (self.selected_instance.rect.x - self.camera_x) * current_zoom
                    sel_sy = (self.selected_instance.rect.y - self.camera_y) * current_zoom
                    sel_sw = self.selected_instance.rect.width * current_zoom
                    sel_sh = self.selected_instance.rect.height * current_zoom
                    pygame.draw.rect(self.screen, (0, 200, 255), (sel_sx, sel_sy, sel_sw, sel_sh), 2)

            self.screen.blit(self.debug_alpha_surf, (0, 0))

            # Интерактивный бирюзовый слой для редактирования активного хитбокса
            active_hitbox_info = self.get_active_hitbox_rect_and_data()
            if active_hitbox_info:
                screen_rect = active_hitbox_info["screen_rect"]
                stype = active_hitbox_info["type"]
                
                # Заливка области слабой прозрачностью
                overlay_surf = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
                overlay_surf.fill((0, 240, 255, 30))
                self.screen.blit(overlay_surf, (screen_rect.x, screen_rect.y))
                
                if stype == "rectangle":
                    w20 = int(screen_rect.width * 0.2)
                    h20 = int(screen_rect.height * 0.2)
                    
                    # Левая граница
                    pygame.draw.line(self.screen, (0, 240, 255, 128), (screen_rect.left + w20, screen_rect.top), (screen_rect.left + w20, screen_rect.bottom), 1)
                    # Правая граница
                    pygame.draw.line(self.screen, (0, 240, 255, 128), (screen_rect.right - w20, screen_rect.top), (screen_rect.right - w20, screen_rect.bottom), 1)
                    # Верхняя граница
                    pygame.draw.line(self.screen, (0, 240, 255, 128), (screen_rect.left, screen_rect.top + h20), (screen_rect.right, screen_rect.top + h20), 1)
                    # Нижняя граница
                    pygame.draw.line(self.screen, (0, 240, 255, 128), (screen_rect.left, screen_rect.bottom - h20), (screen_rect.right, screen_rect.bottom - h20), 1)
                else:
                    scx = screen_rect.centerx
                    scy = screen_rect.centery
                    sr = screen_rect.width / 2
                    
                    # Отрисовка внутренней границы захвата (80% от радиуса)
                    pygame.draw.circle(self.screen, (0, 240, 255, 128), (int(scx), int(scy)), int(0.8 * sr), 1)
                    
                    # Отрисовка 4 радиальных линий-направляющих с рукоятками-круглыми кнопками
                    for angle_deg in (0, 90, 180, 270):
                        rad = math.radians(angle_deg)
                        cos_a = math.cos(rad)
                        sin_a = math.sin(rad)
                        p1 = (int(scx + 0.8 * sr * cos_a), int(scy + 0.8 * sr * sin_a))
                        p2 = (int(scx + sr * cos_a), int(scy + sr * sin_a))
                        pygame.draw.line(self.screen, (0, 240, 255, 200), p1, p2, 2)
                        pygame.draw.circle(self.screen, (0, 240, 255), p2, 4)
                    
                pygame.draw.rect(self.screen, (0, 240, 255), screen_rect, 2)

            self.ui.draw_left_panel(mouse_clicked_this_frame)
            self.ui.draw_right_panel(mouse_clicked_this_frame, target_enemy_raw)

            if self.editor_mode == "LEVEL_EDITOR" and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                self.handle_editor_input(mouse_pos, mouse_clicked_this_frame, right_clicked_this_frame)

            font = self.get_cached_font(24)
            player_hp = self.player.hp if self.player else "N/A"
            img = font.render(f"HP: {player_hp} | LSHIFT / RMB: Parry | TAB: Debug Visuals ({'ON' if self.show_debug else 'OFF'}) | SHIFT+R: Reload Level", True, (200, 200, 200))
            self.screen.blit(img, (CANVAS_OFFSET_X + 20, 20))

            if self.flash_timer > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surf.fill((40, 70, 40))
                flash_surf.set_alpha(100)
                self.screen.blit(flash_surf, (0, 0))
                self.flash_timer -= 1

            if not self.player:
                font_err = self.get_cached_font(36)
                err_text = font_err.render("JSON ERROR! Check console.", True, (255, 100, 100))
                err_sub = font_err.render("Fix levels.json & press SHIFT+R", True, (255, 150, 150))
                self.screen.blit(err_text, (SCREEN_WIDTH // 2 - err_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
                self.screen.blit(err_sub, (SCREEN_WIDTH // 2 - err_sub.get_width() // 2, SCREEN_HEIGHT // 2 + 10))

            pygame.display.flip()

        pygame.quit()