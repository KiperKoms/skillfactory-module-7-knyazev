from random import randint, choice

class BoardException(Exception):
    pass

class BoardOutException(BoardException):
    def __str__(self):
        return "Вы пытаетесь выстрелить за доску!"

class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту клетку"

class BoardWrongShipException(BoardException):
    pass

class Dot:
    """Класс точек на поле"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        """Изначально объекты сравниваются по их id (адресу в памяти),
        а мы бы хотели, чтобы сравнивались точки в каждом из объектов.
        Для этого переопределим магический метод __eq__()"""
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        """Магический метод для отображения информации об объекте класса в режиме отладки (для разработчиков)"""
        return f"Dot({self.x}, {self.y})"

class Ship:
    def __init__(self, bow, l, o):
        self.bow = bow                 # Точка, где размещен нос корабля
        self.l = l                     # Длина корабля
        self.o = o                     # Ориентация корабля
        self.lives = l                 # Количество жизней (сколько точек корабля еще не подбито)

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.l):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:
                cur_x += i

            elif self.o == 1:
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))

        return ship_dots

    def shooten(self, shot):
        return shot in self.dots

class Board:
    """Класс доски представляет матрицу точек"""

    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid

        self.counter_kills = 0   # счетчик уничтоженных кораблей

        self.field = [["O"] * size for _ in range(size)]

        self.busy = []
        self.ships = []
        self.last_hit = []  # список точек, раненого корабля


    def __str__(self):
        res = '  | 1 | 2 | 3 | 4 | 5 | 6 |'
        for i, row in enumerate(self.field):
            res += f'\n{i + 1} | ' + ' | '.join(row) + ' |'

        if self.hid:
            res = res.replace("■", "O")
        return res

    def out(self, d):
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def contour(self, ship, verb=False):
        near = [(i, j) for i in range(-1, 2) for j in range(-1, 2)]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)
                if not self.out(cur) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = "."
                    self.busy.append(cur)

    def add_ship(self, ship):
        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = "■"
            self.busy.append(d)

        self.ships.append(ship)
        self.contour(ship)

    def shot(self, d):
        if self.out(d):
            raise BoardOutException()

        if d in self.busy:
            raise BoardUsedException()

        self.busy.append(d)

        for ship in self.ships:
            if ship.shooten(d):
                ship.lives -= 1
                self.field[d.x][d.y] = "X"
                print('Попал')
                if ship.lives == 0:
                    self.counter_kills += 1
                    self.contour(ship, verb=True)
                    print("Корабль уничтожен!")
                    self.last_hit = []
                    return False
                else:
                    print("Корабль ранен!")
                    self.last_hit.append(d)
                    return True

        self.field[d.x][d.y] = "."
        print("Мимо!")
        return False

    def begin(self):
        self.busy = []

    def defeat(self):
        return self.counter_kills == len(self.ships)

class Player:
    """Описание игрока"""
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)

class AI(Player):
    def ask(self):
        last = self.enemy.last_hit
        while True:
            if last:  # добиваем раненый корабль
                if len(last) == 1:
                    near = ((0, 1), (0, -1), (1, 0), (-1, 0))
                else:
                    if last[0].x == last[-1].x:
                        near = ((0, 1), (0, -1))
                    else:
                        near = ((1, 0), (-1, 0))
                dx, dy = choice(near)
                d = choice((Dot(last[-1].x + dx, last[-1].y + dy), Dot(last[0].x + dx, last[0].y + dy)))
            else:
                d = Dot(randint(0, 5), randint(0, 5))
            if d not in self.enemy.busy and not self.enemy.out(d):
                break
        print(' ' * 33 + f'Ход компьютера: {d.x + 1} {d.y + 1}')
        print(' ' * 33, end='')
        return d

class User(Player):
    def ask(self):
        while True:
            cords = input("Ваш ход: ").split()

            if len(cords) != 2:
                print(" Введите 2 координаты! ")
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):
                print(" Введите числа! ")
                continue

            x, y = int(x), int(y)

            return Dot(x - 1, y - 1)

class Game:
    def __init__(self, size=6):
        self.size = size
        pl = self.random_board()
        co = self.random_board()
        co.hid = True

        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def try_board(self):
        lens = [3, 2, 2, 1, 1, 1, 1]
        board = Board(size=self.size)
        attempts = 0
        for l in lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), l, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def random_board(self):
        board = None
        while board is None:
            board = self.try_board()
        return board

    def greet(self):
        print("-------------------")
        print("  Приветсвуем вас  ")
        print("      в игре       ")
        print("    морской бой    ")
        print("-------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

    def loop(self):
        num = 0
        while True:
            print('-' * self.size * 10)
            print('Ваша доска:' + ' ' * (self.size * 4 - 2) + 'Доска компьютера:')
            for i in range (self.size):
                print((self.us.board.__str__().split('\n')[i] + ' ' * self.size + self.ai.board.__str__().split('\n')[i]))

            if num % 2 == 0:
                print("Ходит пользователь!")
                repeat = self.us.move()
            else:
                print(' ' * 33 + 'Ходит компьютер!')
                repeat = self.ai.move()
            if repeat:
                num -= 1

            if self.ai.board.defeat():
                print("-" * 20)
                print("Вы выиграли!")
                break

            if self.us.board.defeat():
                print("-" * 20)
                print("Компьютер выиграл!")
                break
            num += 1

    def start(self):
        self.greet()
        self.loop()

g = Game()
g.start()