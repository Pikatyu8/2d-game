# editor/editor_ui.py
import pygame
from editor.editor_player_start import PlayerStart
from editor.editor_widgets import EditorWidgetsMixin
from editor.editor_left_panel import EditorLeftPanelMixin
from editor.right_panel.editor_right_panel import EditorRightPanelMixin

class EditorUI(EditorWidgetsMixin, EditorLeftPanelMixin, EditorRightPanelMixin):
    def __init__(self, game):
        self.game = game
        self.font_ui = pygame.font.SysFont(None, 20)