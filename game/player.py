"""Player class for the roguelike game."""

from .items import Inventory


class Player:
    """Represents the player character in the game."""
    
    def __init__(self, x: int, y: int):
        """Initialize the player at given coordinates.
        
        Args:
            x: X coordinate on the map
            y: Y coordinate on the map
        """
        self.x = x
        self.y = y
        self.symbol = '☺'  
        self.hp = 100
        self.max_hp = 100
        self.attack_power = 10
        self.inventory = Inventory()
    
    def move(self, dx: int, dy: int, game_map) -> bool:
        """Attempt to move the player by dx, dy.
        
        Args:
            dx: Change in x coordinate
            dy: Change in y coordinate
            game_map: The game map to check for collisions
            
        Returns:
            True if move was successful, False if blocked
        """
        new_x = self.x + dx
        new_y = self.y + dy
        
        if (0 <= new_x < len(game_map[0]) and 
            0 <= new_y < len(game_map) and 
            game_map[new_y][new_x] != '#'):
            self.x = new_x
            self.y = new_y
            return True
        return False
    
    def take_damage(self, damage: int):
        """Apply damage to the player.
        
        Args:
            damage: Amount of damage to take
        """
        self.hp = max(0, self.hp - damage)
    
    def heal(self, amount: int):
        """Heal the player.
        
        Args:
            amount: Amount of HP to restore
        """
        self.hp = min(self.max_hp, self.hp + amount)
    
    def is_alive(self) -> bool:
        """Check if the player is still alive.
        
        Returns:
            True if player has HP > 0
        """
        return self.hp > 0

