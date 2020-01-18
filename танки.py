import pygame
import os
import random
import sys
import uuid


class Tank:
    def __init__(self, level, side, pos=None, direction=None):
        global sprites
        self.health = 100
        self.speed = 1
        self.side = side
        self.level = level
        self.control = [pygame.K_SPACE, pygame.K_w, pygame.K_d, pygame.K_s, pygame.K_a]
        self.state = 'alive'
        self.image = sprites.subsurface(64, 0, 26, 30)
        if pos:
            self.rect = pygame.Rect(pos, (26, 26))
        else:
            self.rect = pygame.Rect((0, 0), (26, 26))
        if not direction:
            self.direction = random.choice(['up', 'down', 'right', 'left'])
        else:
            self.direction = direction
        self.pressed = [False] * 4

    def draw(self):
        global screen
        if self.state == 'alive':
            screen.blit(self.image, self.rect.topleft)
        elif self.state == 'exploding':
            self.explosion.draw()

    def explode(self):
        if self.state != 'dead':
            self.state = 'exploding'
            self.explosion = Explosion(self.rect.topleft)

    def fire(self):
        global bullets, fired_bullets
        if self.state != 'alive':
            gtimer.destroy(self.timer_uuid_fire)
            return False
        bullet = Bullet(level, self.rect.topleft, self.direction)
        if self.side == 'player':
            bullet.owner = 'player'
            fired_bullets += 1
        else:
            bullet.owner = 'enemy'
        bullets.append(bullet)
        return True

    def rotate(self, direction, fixed_pos=True):
        self.direction = direction
        if direction == 'up':
            self.image = self.image_up
            if fixed_pos:
                self.rect.top -= 5
        elif direction == 'down':
            self.image = self.image_down
            if fixed_pos:
                self.rect.top += 5
        elif direction == 'right':
            self.image = self.image_right
            if fixed_pos:
                self.rect.left += 5
        else:
            self.image = self.image_left
            if fixed_pos:
                self.rect.left -= 5

    def turn_around(self):
        if self.direction == 'up':
            self.rotate('down')
        elif self.direction == 'down':
            self.rotate('up')
        elif self.direction == 'left':
            self.rotate('right')
        else:
            self.rotate('left')

    def update(self, time_passed):
        if self.state == 'exploding':
            if not self.explosion.active:
                self.state = 'dead'
                del self.explosion

    def bullet_impact(self, friendly_fire=False, damage=50):
        global play_sounds, sounds
        if not friendly_fire:
            self.health -= damage
            if self.health < 1:
                if self.side == 'enemy' and play_sounds:
                    sounds['explosion'].play()
                self.explode()
            return True
        if self.side == 'enemy':
            return False
        else:
            return True


class Enemy(Tank):
    def __init__(self, level, side='enemy', pos=None, direction=None):
        global enemies, sprites
        Tank.__init__(self, level, side='enemy', pos=None, direction=None)
        self.level = level
        self.rect = pygame.Rect(pos, (26, 26))
        self.image = sprites.subsurface(64, 0, 26, 30)
        self.image_up = self.image
        self.image_down = pygame.transform.rotate(self.image, 180)
        self.image_left = pygame.transform.rotate(self.image, 90)
        self.image_right = pygame.transform.rotate(self.image, 270)
        self.rotate(self.direction, False)
        self.path = self.generate_path(self.direction)
        self.timer_uuid_fire = gtimer.add(20000, lambda: self.fire())
        self.side = side

    def move(self):
        global enemies, player
        if self.state != 'alive':
            return
        if not self.path:
            self.path = self.generate_path(None, True)
        new_pos = self.path.pop(0)
        if self.direction == 'up' and new_pos[1] < 0:
            self.path = self.generate_path(self.direction, True)
            return
        elif self.direction == 'right' and new_pos[0] > width - 30:
            self.path = self.generate_path(self.direction, True)
            return
        elif self.direction == 'down' and new_pos[1] > height - 30:
            self.path = self.generate_path(self.direction, True)
            return
        elif self.direction == 'left' and new_pos[0] < 0:
            self.path = self.generate_path(self.direction, True)
            return
        new_rect = pygame.Rect(new_pos, (26, 26))
        if new_rect.collidelist(self.level.obstacle_rects) != -1:
            self.path = self.generate_path(self.direction, True)
            return
        for enemy in enemies:
            if enemy != self and new_rect.colliderect(enemy.rect):
                self.turn_around()
                self.path = self.generate_path(self.direction)
                return
        if new_rect.colliderect(player.rect):
            self.turn_around()
            self.path = self.generate_path(self.direction)
            return
        self.rect.topleft = new_rect.topleft

    def update(self, time_passed):
        Tank.update(self, time_passed)
        if self.state == 'alive':
            self.move()
        elif self.state == 'exploding' and not self.explosion.active:
            self.state = 'dead'
            del self.explosion

    def generate_path(self, direction=None, fixed_direction=False):
        all_directions = ['up', 'down', 'right', 'left']
        if not direction:
            if self.direction == 'up':
                oposite_direction = 'down'
            elif self.direction == 'down':
                oposite_direction = 'up'
            elif self.direction == 'right':
                oposite_direction = 'left'
            else:
                oposite_direction = 'right'
            directions = all_directions
            random.shuffle(directions)
            directions.remove(oposite_direction)
            directions.append(oposite_direction)
        else:
            if direction == 'up':
                oposite_direction = 'down'
            elif direction == 'down':
                oposite_direction = 'up'
            elif direction == 'right':
                oposite_direction = 'left'
            else:
                oposite_direction = 'right'
            directions = all_directions
            random.shuffle(directions)
            directions.remove(oposite_direction)
            directions.remove(direction)
            directions.insert(0, direction)
            directions.append(oposite_direction)
        x = self.rect.left // tile_width
        y = self.rect.top // tile_height
        new_direction = None
        max_x = width // tile_width
        max_y = height // tile_height
        for dir in directions:
            if dir == 'up' and y > 1:
                new_pos_rect = self.rect.move(0, -10)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = dir
                    break
            elif dir == 'right' and x < max_x - 3:
                new_pos_rect = self.rect.move(10, 0)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = dir
                    break
            elif dir == 'down' and y < max_y - 3:
                new_pos_rect = self.rect.move(0, 10)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = dir
                    break
            elif dir == 'left' and x > 1:
                new_pos_rect = self.rect.move(-10, 0)
                if new_pos_rect.collidelist(self.level.obstacle_rects) == -1:
                    new_direction = dir
                    break
        if not new_direction:
            new_direction = oposite_direction
        if fixed_direction and new_direction == self.direction:
            fixed_direction = False
        self.rotate(new_direction, fixed_direction)
        positions = []
        x = self.rect.left
        y = self.rect.top
        pixels = int(random.randint(1, 12) * 32) + 3
        if new_direction == 'up':
            for px in range(0, pixels, self.speed):
                positions.append([x, y - px])
        if new_direction == 'right':
            for px in range(0, pixels, self.speed):
                positions.append([x + px, y])
        if new_direction == 'down':
            for px in range(0, pixels, self.speed):
                positions.append([x, y + px])
        if new_direction == 'left':
            for px in range(0, pixels, self.speed):
                positions.append([x - px, y])
        return positions


class Player(Tank):
    def __init__(self, level, side='player', pos=None, direction=None):
        global sprites
        Tank.__init__(self, level, side='player', pos=None, direction=None)
        self.level = level
        self.start_pos = pos
        self.start_direction = direction
        self.rect.topleft = self.start_pos
        self.image = sprites.subsurface(0, 0, 32, 32)
        self.image_up = self.image
        self.image_down = pygame.transform.rotate(self.image, 180)
        self.image_left = pygame.transform.rotate(self.image, 90)
        self.image_right = pygame.transform.rotate(self.image, 270)
        if not direction:
            self.rotate('up', False)
        else:
            self.rotate(direction, False)
        self.side = side

    def move(self, direction):
        global player, enemies
        if self.state == 'exploding' and not self.explosion.active:
            self.state = 'dead'
            del self.explosion
        if self.state != 'alive':
            return
        if self.direction != direction:
            self.rotate(direction, False)
        if direction == 'up':
            new_pos = [self.rect.left, self.rect.top - self.speed]
            if new_pos[1] < 0:
                return
        elif direction == 'right':
            new_pos = [self.rect.left + self.speed, self.rect.top]
            if new_pos[0] > width - 30:
                return
        elif direction == 'down':
            new_pos = [self.rect.left, self.rect.top + self.speed]
            if new_pos[1] > height - 30:
                return
        else:
            new_pos = [self.rect.left - self.speed, self.rect.top]
            if new_pos[0] < 0:
                return
        player_rect = pygame.Rect(new_pos, (26, 26))
        if player_rect.collidelist(self.level.obstacle_rects) != -1:
            return
        for enemy in enemies:
            if player_rect.colliderect(enemy.rect):
                return
        self.rect.topleft = (new_pos[0], new_pos[1])


class Explosion:
    def __init__(self, pos, interval=None, images=None):
        global sprites
        self.pos = [pos[0] - 16, pos[1] - 16]
        self.active = True
        if not interval:
            interval = 100
        if not images:
            images = [sprites.subsurface(0, 80 * 2, 32 * 2, 32 * 2),
                      sprites.subsurface(32 * 2, 80 * 2, 32 * 2, 32 * 2),
                      sprites.subsurface(64 * 2, 80 * 2, 32 * 2, 32 * 2)]
        images.reverse()
        self.images = images
        self.image = self.images.pop()
        gtimer.add(interval, lambda: self.update(), len(self.images) + 1)

    def draw(self):
        global screen
        screen.blit(self.image, self.pos)

    def update(self):
        if len(self.images):
            self.image = self.images.pop()
        else:
            self.active = False


class Level:
    def __init__(self, level_map):
        global sprites
        self.tile_size = 16
        self.tile_brick = sprites.subsurface(96, 128, 16, 16)
        self.tile_grass = sprites.subsurface(112, 144, 16, 16)
        self.obstacle_rects = []
        self.load_level(level_map)

    def load_level(self, level_map):
        filename = 'maps/' + str(level_map)
        if not os.path.isfile(filename):
            return False
        file = open(filename, 'r')
        data = file.read().split('\n')
        self.tile_map = []
        x, y = 0, 0
        for row in data:
            for letter in row:
                if letter == '#':
                    tile_type = self.tile_brick
                elif letter == '.':
                    tile_type = self.tile_grass
                else:
                    continue
                tile = TileRect(x, y, self.tile_size, self.tile_size, tile_type)
                if tile_type == self.tile_brick:
                    self.obstacle_rects.append(tile)
                self.tile_map.append(tile)
                x += self.tile_size
            x = 0
            y += self.tile_size
        return True

    def draw(self):
        global screen
        for tile in self.tile_map:
            screen.blit(tile.type, tile.topleft)


class TileRect(pygame.Rect):
    def __init__(self, left, top, width, height, type):
        pygame.Rect.__init__(self, left, top, width, height)
        self.type = type


class Bullet:
    def __init__(self, level, pos, direction, damage=50, speed=2):
        global sprites
        self.level = level
        self.direction = direction
        self.damage = damage
        self.owner = None
        self.image = sprites.subsurface(150, 148, 6, 8)
        if direction == 'up':
            self.rect = pygame.Rect(pos[0] + 11, pos[1] - 8, 6, 8)
        elif direction == 'right':
            self.image = pygame.transform.rotate(self.image, 270)
            self.rect = pygame.Rect(pos[0] + 26, pos[1] + 11, 8, 6)
        elif direction == 'down':
            self.image = pygame.transform.rotate(self.image, 180)
            self.rect = pygame.Rect(pos[0] + 11, pos[1] + 26, 6, 8)
        else:
            self.image = pygame.transform.rotate(self.image, 90)
            self.rect = pygame.Rect(pos[0] - 8, pos[1] + 11, 8, 6)
        self.explosion_images = [sprites.subsurface(0, 160, 64, 64),
                                 sprites.subsurface(64, 160, 64, 64)]
        self.speed = speed
        self.state = 'active'

    def draw(self):
        global screen
        if self.state == 'active':
            screen.blit(self.image, self.rect.topleft)
        elif self.state == 'exploding':
            self.explosion.draw()

    def update(self):
        global player, enemies, bullets
        if self.state == 'exploding' and not self.explosion.active:
            self.destroy()
            del self.explosion
        if self.state != 'active':
            return
        if self.direction == 'up':
            self.rect.topleft = [self.rect.left, self.rect.top - self.speed]
            if self.rect.top < 0:
                if play_sounds and self.owner == 'player':
                    sounds['steel'].play()
                self.explode()
                return
        elif self.direction == 'right':
            self.rect.topleft = [self.rect.left + self.speed, self.rect.top]
            if self.rect.left > width - self.rect.width:
                if play_sounds and self.owner == 'player':
                    sounds['steel'].play()
                self.explode()
                return
        elif self.direction == 'down':
            self.rect.topleft = [self.rect.left, self.rect.top + self.speed]
            if self.rect.top > height - self.rect.height:
                if play_sounds and self.owner == 'player':
                    sounds['steel'].play()
                self.explode()
                return
        else:
            self.rect.topleft = [self.rect.left - self.speed, self.rect.top]
            if self.rect.left < 0:
                if play_sounds and self.owner == 'player':
                    sounds['steel'].play()
                self.explode()
                return
        rects = self.level.obstacle_rects
        if self.rect.collidelistall(rects):
            self.explode()
            return
        for bull in bullets:
            if self.state == 'active' and bull.owner != self.owner and \
                    bull != self and self.rect.colliderect(bull.rect):
                self.destroy()
                self.explode()
                return
        for enemy in enemies:
            if enemy.state == 'alive' and self.rect.colliderect(enemy.rect):
                if enemy.bullet_impact(self.owner == 'enemy'):
                    self.destroy()
                    return
        if player.state == 'alive' and self.rect.colliderect(player.rect):
            if player.bullet_impact(self.owner == 'player'):
                self.destroy()
                return

    def destroy(self):
        self.state = 'removed'

    def explode(self):
        if self.state != 'removed':
            self.state = 'exploding'
            self.explosion = Explosion([self.rect.left - 13, self.rect.top - 13], None, self.explosion_images)


class Timer(object):
    def __init__(self):
        self.timers = []

    def add(self, interval, callback, repeat=-1):
        options = {
            'interval': interval,
            'callback': callback,
            'repeat': repeat,
            'times': 0,
            'time': 0,
            'uuid': uuid.uuid4()
        }
        self.timers.append(options)
        return options['uuid']

    def destroy(self, uuid_num):
        for timer in self.timers:
            if timer['uuid'] == uuid_num:
                self.timers.remove(timer)
                return

    def update(self, time_passed):
        for timer in self.timers:
            timer['time'] += time_passed
            if timer['time'] > timer['interval']:
                timer['time'] -= timer['interval']
                timer['times'] += 1
                if -1 < timer['repeat'] == timer['times']:
                    self.timers.remove(timer)
                try:
                    timer['callback']()
                except:
                    try:
                        self.timers.remove(timer)
                    except:
                        pass


def start(text, gameover=False):
    fon_1 = pygame.transform.scale(load_image('background1.png'), (width, height))
    fon_2 = pygame.transform.scale(load_image('background2.png'), (width, height))
    fon_3 = pygame.transform.scale(load_image('background3.png'), (width, height))
    cloud1 = pygame.transform.scale(load_image('cloud1.png'), (46, 21))
    cloud2 = pygame.transform.scale(load_image('cloud2.png'), (147, 54))
    cloud3 = pygame.transform.scale(load_image('cloud3.png'), (55, 28))
    tank = pygame.transform.scale(load_image('tank.png'), (270, 150))
    screen.blit(fon_1, (0, 0))
    screen.blit(fon_2, (0, 0))
    screen.blit(fon_3, (0, 0))
    screen.blit(cloud1, (300, 50))
    screen.blit(cloud2, (400, 100))
    screen.blit(cloud3, (700, 50))
    screen.blit(tank, (400, 300))
    font = pygame.font.Font(None, 50)
    text_coord = 30
    for line in text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
    while 1:
        for i in pygame.event.get():
            if i.type == pygame.QUIT:
                terminate()
            if i.type == pygame.KEYDOWN:
                if gameover:
                    if i.key == pygame.K_n:
                        return 'New_game'
                    elif i.key == pygame.K_b:
                        return 'New_map'
                    elif i.key == pygame.K_q:
                        terminate()
                else:
                    if i.key == pygame.K_ESCAPE:
                        return False
                    else:
                        return True
            elif i.type == pygame.MOUSEBUTTONDOWN and not gameover:
                return True
        pygame.display.flip()
        clock.tick(fps)


def load_image(name):
    fullname = 'images/' + name
    image = pygame.image.load(fullname)
    return image


def draw():
    level.draw()
    player.draw()
    for enemy in enemies:
        enemy.draw()
    for bull in bullets:
        bull.draw()
    pygame.display.flip()


def generate_enemies(number):
    count = 0
    while count < number:
        enemy_pos = random.choice(enemy_possible_points)
        if enemy_pos not in enemy_positions:
            enemy_positions.append(enemy_pos)
            new_enemy = Enemy(level, pos=enemy_pos)
            enemies.append(new_enemy)
            count += 1


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    pygame.init()
    size = width, height = 800, 800
    tile_width = tile_height = 16
    screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
    if '-w' in sys.argv[1:]:
        screen = pygame.display.set_mode(size)
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
    clock = pygame.time.Clock()
    fps = 50
    play_sounds = False
    pygame.mixer.pre_init(44100, -16, 1, 512)

    gtimer = Timer()
    start_text = ['Игра в танки',
                  '---------------------------------------------------------',
                  'Правила игры:',
                  'Движение - кнопками WASD',
                  'Выстрел - кнопка ПРОБЕЛ.',
                  'Игра идет до полного уничтожения',
                  'танков противника',
                  'или пражения игрока.',
                  '',
                  'Звуки вкл/выкл кпокой M',
                  '---------------------------------------------------------',
                  'Запуск с ключом -w открывает игру в окне',
                  '',
                  'Приятной игры!']
    if not start(start_text):
        screen = pygame.display.set_mode(size)
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
    sprites = pygame.transform.scale(pygame.image.load('images/sprites.gif'), [192, 224])
    pygame.display.set_icon(sprites.subsurface(0, 0, 26, 26))

    sounds = dict()
    sounds['start'] = pygame.mixer.Sound('sounds/gamestart.ogg')
    sounds['end'] = pygame.mixer.Sound('sounds/gameover.ogg')
    sounds['bg'] = pygame.mixer.Sound('sounds/background.ogg')
    sounds['fire'] = pygame.mixer.Sound('sounds/fire.ogg')
    sounds['explosion'] = pygame.mixer.Sound('sounds/explosion.ogg')
    sounds['brick'] = pygame.mixer.Sound('sounds/brick.ogg')
    sounds['steel'] = pygame.mixer.Sound('sounds/steel.ogg')

    bullets = []

    maps = ['map1.txt', 'map2.txt', 'map3.txt']
    map_number = 0
    level = Level(maps[map_number])
    play_sounds = True
    if play_sounds:
        sounds['start'].play()
        gtimer.add(4300, lambda: sounds['bg'].play(-1), 1)
    enemies = []
    enemy_possible_points = []
    for i in range(10, width - 30, 30):
        for j in range(10, height - 30, 30):
            if not (40 < i < width - 50 and 40 < j < height - 50) and \
                    (i, j) not in enemy_possible_points:
                enemy_possible_points.append((i, j))
    enemy_positions = []
    generate_enemies(10)
    player = Player(level, pos=(width // 2, height // 2))

    shot_enemies = 0
    fired_bullets = 0

    running = True
    time_passed = clock.tick(20)
    while running:
        for i in pygame.event.get():
            if i.type == pygame.QUIT:
                running = False
                terminate()
            if i.type == pygame.KEYDOWN:
                if i.key == pygame.K_m:
                    play_sounds = not play_sounds
                    if play_sounds:
                        gtimer.add(4330, lambda: sounds['bg'].play(-1), 1)
                    else:
                        for sound in sounds:
                            sounds[sound].stop()
                if i.key == pygame.K_ESCAPE:
                    screen = pygame.display.set_mode(size)
                    os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'
                if player.state == 'alive':
                    try:
                        index = player.control.index(i.key)
                    except:
                        pass
                    else:
                        if index == 0:
                            if player.fire() and play_sounds:
                                sounds['fire'].play()
                        elif index == 1:
                            player.pressed[0] = True
                        elif index == 2:
                            player.pressed[1] = True
                        elif index == 3:
                            player.pressed[2] = True
                        else:
                            player.pressed[3] = True
            elif i.type == pygame.KEYUP:
                if player.state == 'alive':
                    try:
                        index = player.control.index(i.key)
                    except:
                        pass
                    else:
                        if index == 1:
                            player.pressed[0] = False
                        elif index == 2:
                            player.pressed[1] = False
                        elif index == 3:
                            player.pressed[2] = False
                        elif index == 4:
                            player.pressed[3] = False
        if player.state == 'alive':
            if player.pressed[0]:
                player.move('up')
            elif player.pressed[1]:
                player.move('right')
            elif player.pressed[2]:
                player.move('down')
            elif player.pressed[3]:
                player.move('left')
        if player.state == 'dead' or len(enemies) == 0:
            if player.state == 'dead':
                top_text = 'Игра окончена! Ты ПрОиГрАл Гыгыгыгыг'
            else:
                top_text = 'Победа!'
            if play_sounds:
                for sound in sounds:
                    sounds[sound].stop()
                sounds['end'].play()
            if fired_bullets:
                statistics = 'составляет ' + str(int(shot_enemies / fired_bullets * 200)) + '%'
            else:
                statistics = 'не определена'
            gameover_text = [top_text,
                             '---------------------------------------------------------',
                             'Уничножено врагов: ' + str(shot_enemies),
                             'Выпущено снарядов: ' + str(fired_bullets),
                             'Точность стрельбы: ' + str(statistics),
                             'N - начать заново',
                             'B - начать с другой картой',
                             'Q - завершить игру']
            next_step = start(gameover_text, gameover=True)
            if next_step == 'New_map':
                map_number = (map_number + 1) % len(maps)
            if next_step:
                bullets.clear()
                enemies.clear()
                del gtimer.timers[:]
                del player
                level = Level(maps[map_number])
                generate_enemies(10)
                shot_enemies = 0
                fired_bullets = 0
                player = Player(level, pos=(width // 2, height // 2))
                if play_sounds:
                    sounds['start'].play()
                    gtimer.add(4300, lambda: sounds['bg'].play(-1), 1)
        player.update(time_passed)
        for bull in bullets:
            if bull.state == 'removed':
                bullets.remove(bull)
            else:
                bull.update()
        for enemy in enemies:
            enemy.update(time_passed)
            if enemy.state == 'dead':
                enemies.remove(enemy)
                shot_enemies += 1
        gtimer.update(time_passed)
        screen.fill(pygame.Color('black'))
        draw()
