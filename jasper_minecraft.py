from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import randint

app = Ursina()

# Player
player = FirstPersonController()
player.health = 100

selected_color = color.green
enemies = []
water_blocks = []
animals = []
game_over = False

# UI
health_text = Text(
    text=f'Health: {player.health}',
    position=(-0.85, 0.45),
    scale=2
)

controls_text = Text(
    text=
    "CONTROLS\n"
    "WASD - Move\n"
    "Mouse - Look\n"
    "Left Click - Shoot\n"
    "1-6 - Change Color\n"
    "7 - Plant Tree\n"
    "8 - Pour Water\n"
    "Right Click - Break Block",
    position=(-0.85, 0.15),
    scale=1
)

hint_text = Text(
    text="Defeat all enemies!",
    position=(0, 0.45),
    origin=(0, 0),
    scale=2
)

class Block(Button):
    def __init__(self, position=(0,0,0), block_color=color.green):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            texture='white_cube',
            color=block_color,
            highlight_color=color.white,
            collider='box',
            origin_y=0.5
        )

    def input(self, key):
        if self.hovered:
            if key == 'middle mouse down':
                Block(
                    position=self.position + mouse.normal,
                    block_color=selected_color
                )

            if key == 'right mouse down':
                destroy(self)

class Tree:
    def __init__(self, position=(0,0,0)):
        trunk_height = 3
        for y in range(trunk_height):
            Block(position=(position[0], y, position[2]), block_color=color.brown)

        leaf_positions = [
            (0, trunk_height, 0),
            (1, trunk_height, 0),
            (-1, trunk_height, 0),
            (0, trunk_height, 1),
            (0, trunk_height, -1),
            (1, trunk_height, 1),
            (-1, trunk_height, 1),
            (1, trunk_height, -1),
            (-1, trunk_height, -1),
            (0, trunk_height + 1, 0)
        ]

        for offset in leaf_positions:
            Block(
                position=(position[0] + offset[0], position[1] + offset[1], position[2] + offset[2]),
                block_color=color.lime
            )

class Water(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            parent=scene,
            model='cube',
            color=color.azure.tint(0.6),
            scale=(1, 0.5, 1),
            position=position,
            texture='white_cube'
        )

class Animal(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            parent=scene,
            model='sphere',
            color=color.orange,
            scale=0.6,
            position=position,
            collider='box'
        )
        self.speed = 1.5
        self.direction = Vec3(randint(-1, 1), 0, randint(-1, 1))
        if self.direction == Vec3(0, 0, 0):
            self.direction = Vec3(1, 0, 0)
        self.wander_timer = 0.5

    def update(self):
        self.wander_timer -= time.dt
        if self.wander_timer <= 0:
            self.direction = Vec3(randint(-1, 1), 0, randint(-1, 1))
            if self.direction == Vec3(0, 0, 0):
                self.direction = Vec3(1, 0, 0)
            self.wander_timer = randint(60, 140) / 100

        self.position += self.direction * self.speed * time.dt

        if abs(self.x) > 18 or abs(self.z) > 18:
            self.direction *= -1

        for water in water_blocks:
            if distance(self.position, water.position) < 1:
                self.direction = Vec3(randint(-1, 1), 0, randint(-1, 1))
                if self.direction == Vec3(0, 0, 0):
                    self.direction = Vec3(1, 0, 0)
                break

class Bullet(Entity):
    def __init__(self, position, direction):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.2,
            position=position
        )
        self.direction = direction
        self.speed = 30

    def update(self):
        self.position += self.direction * self.speed * time.dt

        if distance(self.position, player.position) > 100:
            destroy(self)

        for enemy in enemies[:]:
            if not getattr(enemy, 'enabled', True):
                if enemy in enemies:
                    enemies.remove(enemy)
                continue

            try:
                if distance(self.position, enemy.position) < 1:
                    enemy.health -= 25

                    if enemy.health <= 0:
                        enemies.remove(enemy)
                        destroy(enemy)

                    destroy(self)
                    return
            except Exception:
                if enemy in enemies:
                    enemies.remove(enemy)
                continue

class Enemy(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(1,2,1),
            position=position,
            collider='box'
        )

        self.health = 100
        self.speed = 2

    def update(self):
        direction = player.position - self.position
        direction.y = 0

        if direction.length() > 1:
            self.position += direction.normalized() * self.speed * time.dt

        if distance(self.position, player.position) < 1.5:
            player.health -= 15 * time.dt

def input(key):
    global selected_color

    if key == 'r' and game_over:
        respawn()
        return

    if game_over:
        return

    if key == 'left mouse down':
        Bullet(
            position=player.position + Vec3(0,1.5,0),
            direction=camera.forward
        )

    if key == '1':
        selected_color = color.green
        hint_text.text = "Green Block Selected"

    elif key == '2':
        selected_color = color.gray
        hint_text.text = "Stone Block Selected"

    elif key == '3':
        selected_color = color.brown
        hint_text.text = "Wood Block Selected"

    elif key == '4':
        selected_color = color.blue
        hint_text.text = "Water Block Selected"

    elif key == '5':
        selected_color = color.red
        hint_text.text = "Red Block Selected"

    elif key == '6':
        selected_color = color.yellow
        hint_text.text = "Gold Block Selected"

    elif key == '7':
        target = player.position + camera.forward * 3
        Tree(position=(round(target.x), 0, round(target.z)))
        hint_text.text = "Planted a Tree!"

    elif key == '8':
        target = player.position + camera.forward * 3
        water = Water(position=(round(target.x), 0.25, round(target.z)))
        water_blocks.append(water)
        hint_text.text = "Poured Water!"

    if key == 'q':
        application.quit()

def respawn():
    global game_over
    player.position = (0, 2, 0)
    player.health = 100
    game_over = False
    hint_text.text = "Respawned!"


def update():
    global game_over
    health_text.text = f'Health: {int(player.health)}'

    if game_over:
        return

    if player.health < 30:
        hint_text.text = "WARNING: LOW HEALTH!"

    if player.health <= 0 and not game_over:
        player.health = 0
        hint_text.text = "GAME OVER - Press R to Respawn"
        game_over = True

    if len(enemies) == 0:
        hint_text.text = "YOU WIN!"

# Generate ground
for x in range(-20, 21):
    for z in range(-20, 21):
        Block(position=(x, 0, z), block_color=color.green)

# Create lakes
lake_centers = [(-10, -5), (8, 10), (0, 12)]
for center_x, center_z in lake_centers:
    for x in range(center_x - 3, center_x + 4):
        for z in range(center_z - 3, center_z + 4):
            if (x - center_x) ** 2 + (z - center_z) ** 2 <= 10:
                water_blocks.append(Water(position=(x, 0.25, z)))

# Plant trees
for x in range(-18, 19, 6):
    for z in range(-18, 19, 6):
        if randint(0, 4) == 0 and not any((x - cx) ** 2 + (z - cz) ** 2 <= 12 for cx, cz in lake_centers):
            Tree(position=(x, 0, z))

# Spawn animals
for i in range(6):
    animal = Animal(position=(randint(-15, 15), 0.5, randint(-15, 15)))
    animals.append(animal)

# Spawn enemies
for i in range(3):
    enemy = Enemy(
        position=(randint(-15,15), 1, randint(-15,15))
    )
    enemies.append(enemy)

Sky()
DirectionalLight()

app.run()