# core/game.py
import pygame
import os
import copy
import math
import sys
import json
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CANVAS_OFFSET_X, CANVAS_WIDTH, ensure_level_file
)
from core.game_parts.game_io import GameIOMixin
from core.game_parts.game_editor_logic import GameEditorLogicMixin
from core.game_parts.game_hitbox import GameHitboxMixin
from core.game_parts.game_utils import GameUtilsMixin
from entities.platform_class import Platform
from editor.editor_ui import EditorUI, PlayerStart

class Game(GameIOMixin, GameEditorLogicMixin, GameHitboxMixin, GameUtilsMixin):
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
        
        self.active_dropdown_id = None
        self.active_dropdown_data = None
        self.active_dropdown_selection = None
        self.dropdown_just_opened = False 
        
        self.dragging_hitbox = False
        self.hitbox_drag_mode = None
        self.hitbox_drag_start_mouse = (0, 0)
        self.hitbox_drag_start_val = {}

        self.ui = EditorUI(self)
        self.load_level()
    
        if os.path.exists(".editor_selection.json"):
            try:
                os.remove(".editor_selection.json")
            except Exception:
                pass

    def auto_save_current_preset(self):
        if self.editor_mode == "ENEMY_EDITOR" and self.selected_preset_name:
            preset_data = self.presets.get(self.selected_preset_name)
            filepath = self.preset_filepaths.get(self.selected_preset_name)
            if preset_data and filepath:
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(preset_data, f, indent=4)
                    self.last_preset_mod_time = os.path.getmtime(filepath)
                    print(f"[Auto-Save] Synchronized edited preset file to disk: {filepath}")
                except Exception as e:
                    print(f"[Auto-Save Error] {e}")

    def run(self):
        running = True
        while running:
            self.clock.tick(60)  
            mouse_clicked_this_frame = False
            right_clicked_this_frame = False
            mouse_pos = pygame.mouse.get_pos()

            # Проверка внешних изменений пресета (Live-Reload)
            if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") and getattr(self, "selected_preset_name", None):
                filepath = self.preset_filepaths.get(self.selected_preset_name)
                if filepath and os.path.exists(filepath):
                    try:
                        mtime = os.path.getmtime(filepath)
                        if not hasattr(self, "last_preset_mod_time"):
                            self.last_preset_mod_time = mtime
                        if mtime > self.last_preset_mod_time:
                            self.last_preset_mod_time = mtime
                            print(f"[Live-Reload] Изменения зафиксированы: {self.selected_preset_name}. Пересборка...")
                            self.rebuild_objects()
                    except Exception:
                        pass
                
            # Проверка файла синхронизации выбора (вынесена на верхний уровень)
            sel_path = ".editor_selection.json"
            if os.path.exists(sel_path):
                try:
                    sel_mtime = os.path.getmtime(sel_path)
                    if not hasattr(self, "last_sel_mod_time"):
                        self.last_sel_mod_time = sel_mtime
                    if sel_mtime > self.last_sel_mod_time:
                        self.last_sel_mod_time = sel_mtime
                        with open(sel_path, "r", encoding="utf-8") as sf:
                            s_info = json.load(sf)
                        
                        p_combo_path = s_info.get("preset_name", "")
                        p_name = os.path.splitext(os.path.basename(p_combo_path))[0].replace("_", " ").title() if p_combo_path else ""
                        
                        print(f"[Selection Sync Log] Detected change in .editor_selection.json. s_info: {s_info}")
                        print(f"[Selection Sync Log] Current editor mode: {self.editor_mode}, active preset: {self.selected_preset_name}")
                        print(f"[Selection Sync Log] Incoming preset: {p_name}")
                        
                        if p_name and p_name in self.presets:
                            trigger_rebuild = False
                            if self.selected_preset_name != p_name:
                                self.selected_preset_name = p_name
                                trigger_rebuild = True
                                print(f"[Selection Sync Log] Preset changed to: {p_name}")
                            if self.editor_mode != "ENEMY_EDITOR":
                                self.editor_mode = "ENEMY_EDITOR"
                                self.camera_x = 200
                                self.camera_y = 0
                                self.zoom = 1.0
                                trigger_rebuild = True
                                print(f"[Selection Sync Log] Editor mode changed to ENEMY_EDITOR")
                                
                            if trigger_rebuild:
                                self.rebuild_objects()
                                filepath = self.preset_filepaths.get(self.selected_preset_name)
                                if filepath and os.path.exists(filepath):
                                    self.last_preset_mod_time = os.path.getmtime(filepath)
                                
                            tab = s_info.get("inspector_tab")
                            if tab:
                                self.inspector_tab = tab
                                print(f"[Selection Sync Log] Set inspector_tab to {tab}")
                            if "attack_idx" in s_info:
                                self.selected_attack_edit_idx = s_info["attack_idx"]
                            if "box_idx" in s_info:
                                self.selected_box_idx = s_info["box_idx"]
                            if "seq_idx" in s_info:
                                self.selected_seq_idx = s_info["seq_idx"]
                            if "flow_idx" in s_info:
                                self.selected_flow_idx = s_info["flow_idx"]
                                
                            self.dragging_hitbox = False
                            self.hitbox_drag_mode = None
                            
                            print(f"[Selection Sync Log] Synchronized values: attack_idx={self.selected_attack_edit_idx}, box_idx={self.selected_box_idx}, seq_idx={self.selected_seq_idx}, flow_idx={getattr(self, 'selected_flow_idx', None)}")
                        else:
                            print(f"[Selection Sync Warning] Preset '{p_name}' not found in available presets: {list(self.presets.keys())}")
                except Exception as e:
                    print(f"[Selection Sync Error] Fail to parse/process selection file: {e}")
            
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

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
                        elif self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                            self.zoom = min(3.0, self.zoom + 0.1)
                    elif event.button == 5:
                        if 0 <= mouse_pos[0] < CANVAS_OFFSET_X:
                            max_scroll_l = getattr(self, "left_panel_max_scroll", 400)
                            self.left_panel_scroll = min(max_scroll_l, self.left_panel_scroll + 30)
                        elif 1200 <= mouse_pos[0] <= 1400:
                            max_scroll_r = getattr(self, "right_panel_max_scroll", 400)
                            self.right_panel_scroll = min(max_scroll_r, self.right_panel_scroll + 30)
                        elif self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
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
                            self.camera_x = 200  
                            self.camera_y = 0
                            self.zoom = 1.0  
                            self.selected_attack_edit_idx = 0
                            self.selected_box_idx = 0
                        else:
                            self.editor_mode = "GAMEPLAY"
                            self.camera_x = 0
                            self.camera_y = 0
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

            if self.editor_mode in ("ENEMY_EDITOR", "LEVEL_EDITOR") and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                if self.dragging_hitbox:
                    self.update_hitbox_drag(mouse_pos)
                else:
                    hitbox_clicked = self.check_hitbox_interaction(mouse_pos, mouse_clicked_this_frame)
                    if hitbox_clicked:
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
                self.dummy_platform.draw(self.screen, self.camera_x, self.camera_y, self.zoom)
                if self.dummy_enemy:
                    p_fake = pygame.Rect(-100, -100, 0, 0)
                    self.dummy_enemy.draw(
                        surface=self.screen,
                        show_debug=True,
                        player_rect=p_fake,
                        camera_x=self.camera_x,
                        camera_y=self.camera_y,
                        zoom=self.zoom,
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

            active_hitbox_info = self.get_active_hitbox_rect_and_data()
            if active_hitbox_info:
                screen_rect = active_hitbox_info["screen_rect"]
                stype = active_hitbox_info["type"]
                val = active_hitbox_info["shape_data_val"]
                zoom = active_hitbox_info["zoom"]
                camera_x = self.camera_x if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") else 0
                camera_y = self.camera_y if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") else 0
                
                rot_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                
                if stype == "rectangle":
                    rect, angle = val
                    cx = CANVAS_OFFSET_X + (rect.centerx - camera_x) * zoom
                    cy = (rect.centery - camera_y) * zoom
                    sw = rect.width * zoom
                    sh = rect.height * zoom
                    
                    rad = math.radians(-angle)
                    cos_a, sin_a = math.cos(rad), math.sin(rad)
                    
                    w20 = sw * 0.2
                    h20 = sh * 0.2
                    
                    local_x = [-sw/2, -sw/2 + w20, sw/2 - w20, sw/2]
                    local_y = [-sh/2, -sh/2 + h20, sh/2 - h20, sh/2]
                    
                    grid_points = [[None for _ in range(4)] for _ in range(4)]
                    for i in range(4):
                        for j in range(4):
                            px = local_x[i]
                            py = local_y[j]
                            rx = px * cos_a - py * sin_a + cx
                            ry = px * sin_a + py * cos_a + cy
                            grid_points[i][j] = (int(rx), int(ry))
                            
                    outer_corners = [grid_points[0][0], grid_points[3][0], grid_points[3][3], grid_points[0][3]]
                    pygame.draw.polygon(rot_surf, (0, 240, 255, 30), outer_corners)
                    
                    corner_tl = [grid_points[0][0], grid_points[1][0], grid_points[1][1], grid_points[0][1]]
                    corner_tr = [grid_points[2][0], grid_points[3][0], grid_points[3][1], grid_points[2][1]]
                    corner_bl = [grid_points[0][2], grid_points[1][2], grid_points[1][3], grid_points[0][3]]
                    corner_br = [grid_points[2][2], grid_points[3][2], grid_points[3][3], grid_points[2][3]]
                    
                    pygame.draw.polygon(rot_surf, (0, 240, 255, 75), corner_tl)
                    pygame.draw.polygon(rot_surf, (0, 240, 255, 75), corner_tr)
                    pygame.draw.polygon(rot_surf, (0, 240, 255, 75), corner_bl)
                    pygame.draw.polygon(rot_surf, (0, 240, 255, 75), corner_br)
                    
                    pygame.draw.line(rot_surf, (0, 240, 255, 128), grid_points[1][0], grid_points[1][3], 1)
                    pygame.draw.line(rot_surf, (0, 240, 255, 128), grid_points[2][0], grid_points[2][3], 1)
                    pygame.draw.line(rot_surf, (0, 240, 255, 128), grid_points[0][1], grid_points[3][1], 1)
                    pygame.draw.line(rot_surf, (0, 240, 255, 128), grid_points[0][2], grid_points[3][2], 1)
                    
                    pygame.draw.polygon(rot_surf, (0, 240, 255), outer_corners, 2)
                    
                    self.screen.blit(rot_surf, (0, 0))
                    
                else:
                    pygame.draw.circle(rot_surf, (0, 240, 255, 30), (int(screen_rect.centerx), int(screen_rect.centery)), int(screen_rect.width / 2))
                    self.screen.blit(rot_surf, (0, 0))
                    
                    scx = screen_rect.centerx
                    scy = screen_rect.centery
                    sr = screen_rect.width / 2
                    
                    pygame.draw.circle(self.screen, (0, 240, 255, 128), (int(scx), int(scy)), int(0.8 * sr), 1)
                    
                    for angle_deg in (0, 90, 180, 270):
                        rad = math.radians(angle_deg)
                        cos_a = math.cos(rad)
                        sin_a = math.sin(rad)
                        p1 = (int(scx + 0.8 * sr * cos_a), int(scy + 0.8 * sr * sin_a))
                        p2 = (int(scx + sr * cos_a), int(scy + sr * sin_a))
                        pygame.draw.line(self.screen, (0, 240, 255, 200), p1, p2, 2)
                        pygame.draw.circle(self.screen, (0, 240, 255), p2, 4)
                        
                    pygame.draw.circle(self.screen, (0, 240, 255), (int(scx), int(scy)), int(sr), 2)

            self.ui.draw_left_panel(mouse_clicked_this_frame)
            self.ui.draw_right_panel(mouse_clicked_this_frame, target_enemy_raw)

            if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
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