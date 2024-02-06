import pygame as py 
from sys import exit 
import math

# from pygame.sprite import Group 
from settings import * 
py.font.init()
font = py.font.Font(None, 20)

py.init()

py.mixer.init()
py.mixer.music.load("audio/SwitchWithMeTheme.wav")

window = py.display.set_mode((window_w, window_h))
py.display.set_caption("Factory MMO")
clock = py.time.Clock()

# loads images 
background = py.transform.scale(py.image.load("assets/world_map.png").convert(), (window_w, window_h))

# class Pickaxe(py.sprite.Sprite):
#     def __init__(self, name) -> None:
#         super.__init__()
#         self.mining_speed = 5
#         self.durability = 100
#         self.ore_mined = 0 
        
#     def upgrade(self):
#         pass 

class MessageLog:
    def __init__(self, max_messages=5):
        self.messages = []
        self.max_messages = max_messages
        
    def add_message(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop() # remove oldest message 
    
    def draw(self, window):
        for i, message in enumerate(reversed(self.messages)):
            label = font.render(message, True, (0,0,0))
            window.blit(label, (10, window_h - (i+1)*20))

class Factory(py.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = py.transform.scale(py.image.load("assets/factory.png").convert(), (128, 128))
        self.image.set_colorkey((0,0,0))
        self.research_rate = 20
        self.unlock_price = 1000
        self.pos = py.math.Vector2((200, 200))
        self.rect = self.image.get_rect(topleft=self.pos)
        
class Furnace(py.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = py.transform.scale(py.image.load("assets/furnace.png").convert(), (64, 64))
        self.image.set_colorkey((0,0,0))
        self.production_rate = 1000
        self.amount_of_coal = 0 
        self.amount_of_iron = 0
        self.rect = self.image.get_rect()

# DISPENSED ITEM
class IronBar(py.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.value = 50
        self.weight = 28
        self.image = py.transform.scale(py.image.load("assets/iron-bar.png").convert(), (32, 32))
        self.rect = self.image.get_rect()
        
# MINED ITEMS
class IronOre(py.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = py.transform.scale(py.image.load("assets/iron_stone.png").convert(), (32, 32))
        self.image.set_colorkey((0, 0, 0))
        self.amount_of_iron = 500
        self.rect = self.image.get_rect()

class CoalVein(py.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = py.transform.scale(py.image.load("assets/coal_rock.png").convert(), (32, 32))
        self.image.set_colorkey((0, 0, 0))
        self.amount_of_coal = 500
        self.rect = self.image.get_rect()

# INVENTORY
class Inventory:
    def __init__(self, rows, cols):
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.is_open = False 
        self.iron_ore_image = py.transform.scale(py.image.load("assets/iron_stone.png").convert(), (28, 28))
        self.coal_image = py.transform.scale(py.image.load("assets/coal_rock.png").convert(), (28, 28))

    def __contains__(self, item):
        for row in self.grid:
            if item in row:
                return True
        return False 
    
    def add_item(self, item):
        for row in self.grid:
            for i in range(len(row)):
                if row[i] is None:
                    row[i] = item
                    return True  # item was added successfully
        return False  # inventory is full, item was not added

    def remove_item(self, item):
        for row in self.grid:
            for i in range(len(row)):
                if row[i] == item:
                    row[i] = None
                    self.refresh()
                    return True  # item was removed successfully
        return False  # item was not found in inventory

    def refresh(self):
        removed_items = 0 
        for row in self.grid:
            for i in range(len(row)):
                if row[i] is not None:
                    row[i] = None
                    removed_items += 1
                    if removed_items == 2:
                        return 

    def draw(self, window):
        if self.is_open:
            # draw inv 
            s = py.Surface((300,200))
            s.set_alpha(128)
            s.fill((200,200,200))
            window.blit(s, (50,50))

            # label 
            label = font.render('Inventory', True, (0,0,0))
            window.blit(label, (60, 60))
            
            for i, row in enumerate(self.grid):
                for j, item in enumerate(row):
                    py.draw.rect(window, (255, 255, 255), (60 + 30 * j, 90 + 30 * i, 30, 30), 1)
                    if item is not None:
                        if item == 'coal':
                            window.blit(self.coal_image, (60 + 30 * j, 90 + 30 * i))
                        elif item == 'iron ore':
                            window.blit(self.iron_ore_image, (60 + 30 * j, 90 + 30 * i))
                
# PLAYER  
class Player(py.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = py.transform.scale(py.image.load("assets/character_pygame.png").convert_alpha(), (32, 32))
        self.flipped_image = py.transform.flip(self.image, True, False)
        self.current_image = self.image 
        self.pos = py.math.Vector2(PLAYER_START_X, PLAYER_START_Y)
        self.speed = PLAYER_SPEED 
        self.rect = self.image.get_rect(topleft=self.pos)
        self.inventory = Inventory(5, 5)
        self.in_factory = False 
        self.mining = False 
        self.last_mine_time  = py.time.get_ticks()
        self.message_log = MessageLog()
        self.last_deposit_time = py.time.get_ticks()
       
        
    def user_input(self):
        self.velocity_x = 0
        self.velocity_y = 0 
        
        keys = py.key.get_pressed()
        
        if keys[py.K_w]:
            self.velocity_y = -self.speed
        if keys[py.K_a]:
            self.velocity_x = -self.speed
            self.current_image = self.flipped_image
        if keys[py.K_s]:
            self.velocity_y = self.speed
        if keys[py.K_d]:
            self.velocity_x = self.speed 
            self.current_image = self.image 

        # player is moving diagonally 
        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)
        
    def move(self):
        self.pos += py.math.Vector2(self.velocity_x, self.velocity_y)
        self.rect.topleft = self.pos

    def mine(self, ore_type):
        if not self.inventory.add_item(ore_type):
            self.message_log.add_message(f'Inventory full. Cannot mine more {ore_type}')
            print(f'Inventory full. Cannot mine more {ore_type}')
    
    def update(self):
        self.user_input()
        self.move()
        
        keys = py.key.get_pressed()
        if keys[py.K_e]:
            self.inventory.is_open = True# toggle 
        else:
            self.inventory.is_open = False 
                    
        if self.rect.colliderect(factory.rect):
            if not self.in_factory:
                print('factory+')
                self.in_factory = True 
        else:
            self.in_factory = False 

# FURNACE COLLISION
        try:
            if player.rect.colliderect(furnace.rect):
                print("furnace+")
                if py.mouse.get_pressed()[0] and 'iron ore' in self.inventory and 'coal' in self.inventory:
                    current_time = py.time.get_ticks()
                    if current_time - self.last_deposit_time > 1000:  # 1000 ms = 1 second
                        if 'coal' in self.inventory:
                            self.inventory.remove_item('coal')
                            furnace.amount_of_coal += 1
                            self.last_deposit_time = current_time
                        if 'iron ore' in self.inventory:
                            self.inventory.remove_item('iron ore')
                            furnace.amount_of_iron += 1
                            self.last_deposit_time = current_time
        except Exception as e:
            print(f"Error at{e}")
        
        try:
            for ore in [iron_ore1, iron_ore2, coal_vein1, coal_vein2]:
                if self.rect.colliderect(ore.rect):
                    # Check if left mouse button is being held down
                    if py.mouse.get_pressed()[0]:
                        current_time = py.time.get_ticks()
                        if current_time - self.last_mine_time > 1000:  # 1000 ms = 1 second
                            ore_type = 'iron ore' if isinstance(ore, IronOre) else 'coal'
                            if ore_type == 'iron ore':
                                self.mine(ore_type)
                                self.last_mine_time = current_time
                                ore.amount_of_iron -= 1
                                if ore.amount_of_iron <= 0:
                                    # remove the ore if it's depleted
                                    ore.kill()
                            if ore_type == 'coal':
                                self.mine(ore_type)
                                self.last_mine_time = current_time
                                ore.amount_of_coal -= 1
                                if ore.amount_of_coal <= 0:
                                    ore.kill()
                            break
        except Exception as e:
            print(f"Error at {e}")  
        

player = Player()
factory = Factory()
furnace = Furnace()
furnace.rect.topleft = (500, 600)
iron_ore1 = IronOre()
iron_ore1.rect.topleft = (50, 50)
iron_ore2 = IronOre()
iron_ore2.rect.topleft = (500, 200)
coal_vein1 = CoalVein()
coal_vein1.rect.topleft = (500, 350)
coal_vein2 = CoalVein()
coal_vein2.rect.topleft = (550, 280)


# audio settings
py.mixer.music.set_volume(0.1)
py.mixer.music.play(-1)

while True:
    
    keys = py.key.get_pressed()
    for event in py.event.get():
        if event.type == py.QUIT:
            py.quit()
            exit()


    window.blit(background, (0, 0))
    window.blit(factory.image, factory.pos)
    window.blit(furnace.image, furnace.rect.topleft)

    # objects
    window.blit(iron_ore1.image, iron_ore1.rect.topleft)
    window.blit(iron_ore2.image, iron_ore2.rect.topleft)
    window.blit(coal_vein1.image, coal_vein1.rect.topleft)
    window.blit(coal_vein2.image, coal_vein2.rect.topleft)
    
    # player     
    window.blit(player.current_image, player.pos)
    
    player.message_log.draw(window)
    player.inventory.draw(window)
    player.update()
    
    
    
    py.display.update()
    clock.tick(FPS)

    