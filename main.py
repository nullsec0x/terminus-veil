"""Main game file for the roguelike using Textualize."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Header, Footer
from textual.binding import Binding

from game.player import Player
from game.game_map import GameMap
from game.monster import MonsterManager
from game.combat import CombatSystem, GameState
from game.items import ItemManager, ItemType
from game.fov import FOVCalculator, VisibilityTracker


class GameDisplay(Static):
    """Widget to display the game map and player."""
    
    def __init__(self, game_map: GameMap, player: Player, monster_manager: MonsterManager, 
                 item_manager: ItemManager, game_state: GameState):
        super().__init__()
        self.game_map = game_map
        self.player = player
        self.monster_manager = monster_manager
        self.item_manager = item_manager
        self.game_state = game_state
        self.update_display()
    
    def update_display(self):
        """Update the display with current game state."""
        # Check if game is over and show game over message
        if self.game_state and self.game_state.game_over:
            # Create a centered game over message
            game_over_text = """
[bold red on black]
╔══════════════════════════════════════╗
║                                      ║
║              GAME OVER               ║
║                                      ║
║         Press 'r' to restart         ║
║         Press 'q' to quit            ║
║                                      ║
╚══════════════════════════════════════╝
[/]
"""
            self.update(game_over_text)
        else:
            map_str = self.game_map.render_with_entities(
                self.player.x, self.player.y, self.monster_manager, self.item_manager
            )
            self.update(f"[white on black]{map_str}[/]")


class StatusDisplay(Static):
    """Widget to display player status information."""
    
    def __init__(self, player: Player, game_state: GameState):
        super().__init__()
        self.player = player
        self.game_state = game_state
        self.update_status()
    
    def update_status(self):
        """Update the status display."""
        inventory_str = self.player.inventory.get_inventory_display()
        status_text = f"""
[bold]Player Status[/bold]
HP: {self.player.hp}/{self.player.max_hp}
Position: ({self.player.x}, {self.player.y})
Attack: {self.player.attack_power}
Level: {self.game_state.current_level}
Score: {self.game_state.score}

[bold]Inventory[/bold]
{inventory_str}
        """
        self.update(status_text.strip())


class MessageDisplay(Static):
    """Widget to display game messages."""
    
    def __init__(self, combat_system: CombatSystem):
        super().__init__()
        self.combat_system = combat_system
        self.update_messages()
    
    def update_messages(self):
        """Update the message display."""
        messages = self.combat_system.get_recent_messages(5)
        if messages:
            message_text = "\n".join(messages)
        else:
            message_text = "Welcome to the dungeon!\nUse WASD or arrows to move.\nAttack monsters (♠♣♦) by moving into them.\nCollect items (♥¤♪†) and press 1/2 to use them."
        
        self.update(f"[bold]Messages[/bold]\n{message_text}")


class RoguelikeApp(App):
    """Main application class for the roguelike game."""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #game_area {
        width: 4fr;
        border: solid white;
        padding: 1;
        overflow: auto;
    }
    
    #info_area {
        width: 1fr;
        layout: vertical;
        margin-left: 1;
        min-width: 30;
    }
    
    #status_area {
        height: 1fr;
        border: solid white;
        padding: 1;
        margin-bottom: 1;
    }
    
    #message_area {
        height: 1fr;
        border: solid white;
        padding: 1;
    }
    
    GameDisplay {
        text-style: bold;
        overflow: auto;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("up,w", "move_up", "Move Up"),
        Binding("down,s", "move_down", "Move Down"),
        Binding("left,a", "move_left", "Move Left"),
        Binding("right,d", "move_right", "Move Right"),
        Binding("r", "restart", "Restart"),
        Binding("i", "use_item", "Use Item"),
        Binding("1", "use_potion", "Use Potion"),
        Binding("2", "use_scroll", "Use Scroll"),
    ]
    
    def __init__(self):
        super().__init__()
        self._initialize_game()
    
    def _initialize_game(self):
        """Initialize or restart the game."""
        self.game_map = GameMap()
        # Use the generated start position
        start_x, start_y = self.game_map.player_start
        self.player = Player(start_x, start_y)
        
        # Initialize game systems
        self.monster_manager = MonsterManager()
        self.combat_system = CombatSystem()
        self.game_state = GameState()
        self.item_manager = ItemManager()
        
        # Place the exit on the map
        self.game_map.place_exit()
        
        # Spawn monsters and items based on level
        monster_count = self.game_state.get_monster_count_for_level()
        item_count = self.game_state.get_item_count_for_level()
        
        self.monster_manager.spawn_monsters(self.game_map.tiles, monster_count, 
                                          self.game_state.current_level)
        self.item_manager.spawn_items(self.game_map.tiles, item_count)
        
        # Ensure FOV is completely reset and follows player
        self.game_map.fov_calculator = FOVCalculator(self.game_map.tiles)
        self.game_map.visibility_tracker = VisibilityTracker()
        self.game_map.update_fov(self.player.x, self.player.y)
    
    def _advance_to_next_level(self):
        """Advance to the next dungeon level."""
        # Advance game state
        self.game_state.advance_level()
        
        # Generate completely new map
        self.game_map = GameMap()
        
        # Move player to new start position
        start_x, start_y = self.game_map.player_start
        self.player.x = start_x
        self.player.y = start_y
        
        # Clear old entities completely
        self.monster_manager = MonsterManager()
        self.item_manager = ItemManager()
        
        # Place new exit
        self.game_map.place_exit()
        
        # Spawn new monsters and items with increased difficulty
        monster_count = self.game_state.get_monster_count_for_level()
        item_count = self.game_state.get_item_count_for_level()
        
        self.monster_manager.spawn_monsters(self.game_map.tiles, monster_count, 
                                          self.game_state.current_level)
        self.item_manager.spawn_items(self.game_map.tiles, item_count)
        
        # Completely reset FOV for new map
        self.game_map.fov_calculator = FOVCalculator(self.game_map.tiles)
        self.game_map.visibility_tracker = VisibilityTracker()
        self.game_map.update_fov(self.player.x, self.player.y)
        
        # Update GameDisplay references to new objects
        game_display = self.query_one(GameDisplay)
        game_display.game_map = self.game_map
        game_display.player = self.player
        game_display.monster_manager = self.monster_manager
        game_display.item_manager = self.item_manager
        game_display.game_state = self.game_state
        
        # Add level advancement message
        self.combat_system.combat_log.append(f"Welcome to level {self.game_state.current_level}!")
        self.combat_system.combat_log.append("The dungeon grows more dangerous...")
        
    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()
        with Horizontal():
            with Container(id="game_area"):
                yield GameDisplay(self.game_map, self.player, self.monster_manager, 
                                self.item_manager, self.game_state)
            with Container(id="info_area"):
                with Container(id="status_area"):
                    yield StatusDisplay(self.player, self.game_state)
                with Container(id="message_area"):
                    yield MessageDisplay(self.combat_system)
        yield Footer()
    
    def action_move_up(self) -> None:
        """Move player up."""
        self._try_move(0, -1)
    
    def action_move_down(self) -> None:
        """Move player down."""
        self._try_move(0, 1)
    
    def action_move_left(self) -> None:
        """Move player left."""
        self._try_move(-1, 0)
    
    def action_move_right(self) -> None:
        """Move player right."""
        self._try_move(1, 0)
    
    def action_restart(self) -> None:
        """Restart the current level."""
        # Store current level before restart
        current_level = self.game_state.current_level
        
        # Generate new map for current level
        self.game_map = GameMap()
        
        # Reset player to start position with current HP
        start_x, start_y = self.game_map.player_start
        self.player.x = start_x
        self.player.y = start_y
        self.player.hp = self.player.max_hp  # Restore full health
        
        # Clear old entities
        self.monster_manager = MonsterManager()
        self.item_manager = ItemManager()
        
        # Reset game state but keep current level
        self.game_state.game_over = False
        self.game_state.victory = False
        self.game_state.current_level = current_level
        
        # Place new exit
        self.game_map.place_exit()
        
        # Spawn monsters and items for current level
        monster_count = self.game_state.get_monster_count_for_level()
        item_count = self.game_state.get_item_count_for_level()
        
        self.monster_manager.spawn_monsters(self.game_map.tiles, monster_count, 
                                          self.game_state.current_level)
        self.item_manager.spawn_items(self.game_map.tiles, item_count)
        
        # Reset FOV for new map
        self.game_map.fov_calculator = FOVCalculator(self.game_map.tiles)
        self.game_map.visibility_tracker = VisibilityTracker()
        self.game_map.update_fov(self.player.x, self.player.y)
        
        # Update GameDisplay references to new objects
        game_display = self.query_one(GameDisplay)
        game_display.game_map = self.game_map
        game_display.player = self.player
        game_display.monster_manager = self.monster_manager
        game_display.item_manager = self.item_manager
        game_display.game_state = self.game_state
        
        # Clear combat log and add restart message
        self.combat_system.clear_log()
        self.combat_system.combat_log.append(f"Level {current_level} restarted!")
        
        # Force complete UI refresh
        self.refresh()
        self._update_displays()
    
    def action_use_item(self) -> None:
        """Open item usage menu."""
        # For now, just use the first available potion
        self.action_use_potion()
    
    def action_use_potion(self) -> None:
        """Use a health potion."""
        result = self.player.inventory.use_item(ItemType.HEALTH_POTION, self.player)
        if result:
            self.combat_system.combat_log.append(result)
        else:
            self.combat_system.combat_log.append("No health potions available!")
        self._update_displays()
    
    def action_use_scroll(self) -> None:
        """Use a magic scroll."""
        result = self.player.inventory.use_item(ItemType.MAGIC_SCROLL, self.player)
        if result:
            self.combat_system.combat_log.append(result)
        else:
            self.combat_system.combat_log.append("No magic scrolls available!")
        self._update_displays()
    
    def _try_move(self, dx: int, dy: int):
        """Try to move the player or attack if there's a monster.
        
        Args:
            dx: Change in X coordinate
            dy: Change in Y coordinate
        """
        if self.game_state.game_over:
            return
        
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Check for monster at target position
        target_monster = self.monster_manager.get_monster_at(new_x, new_y)
        
        if target_monster and target_monster.is_alive:
            # Attack the monster
            combat_messages = self.combat_system.player_attack_monster(
                self.player, target_monster
            )
            
            # Process monster turn
            turn_messages = self.combat_system.process_turn(
                self.player, self.monster_manager, self.game_map.tiles, 
                self.game_map.visibility_tracker
            )
            
        elif self.player.move(dx, dy, self.game_map.tiles):
            # Player moved successfully
            
            # Check for items at new position
            item = self.item_manager.collect_item(self.player.x, self.player.y)
            if item:
                pickup_message = self.player.inventory.add_item(item)
                self.combat_system.combat_log.append(pickup_message)
            
            # Check for victory condition
            if self.game_state.check_victory_condition(
                self.player.x, self.player.y, self.game_map.tiles
            ):
                # Player reached the exit - advance to next level
                self._advance_to_next_level()
                self._update_displays()
                return
            
            # Process monster turn
            turn_messages = self.combat_system.process_turn(
                self.player, self.monster_manager, self.game_map.tiles, 
                self.game_map.visibility_tracker
            )
        
        # Check defeat condition
        self.game_state.check_defeat_condition(self.player)
        
        self._update_displays()
    
    def _update_displays(self) -> None:
        """Update all display widgets."""
        # Update FOV
        self.game_map.update_fov(self.player.x, self.player.y)
        
        game_display = self.query_one(GameDisplay)
        status_display = self.query_one(StatusDisplay)
        message_display = self.query_one(MessageDisplay)
        
        game_display.update_display()
        status_display.update_status()
        message_display.update_messages()


def main():
    """Run the roguelike game."""
    app = RoguelikeApp()
    app.run()


if __name__ == "__main__":
    main()

