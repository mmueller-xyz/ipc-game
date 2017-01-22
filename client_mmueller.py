import socket
from enum import Enum
from random import randint
import math, time, argparse
import heapq

name = 'client_mmueller'

"""
Der Dijkstra Algorythmus wurde von "http://www.redblobgames.com/pathfinding/a-star/implementation.html"
übernommen und leicht verändert.
"""

class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


class FieldType(Enum):
    UNKNOWN = 'U'
    GRASS = 'G'
    CASTLE = 'C'
    FOREST = 'F'
    MOUNTAIN = 'M'
    LAKE = 'L'

class FieldWeight(Enum):
    UNKNOWN = 11
    GRASS = 10
    FOREST = 10
    MOUNTAIN = 20
    LAKE = 999999
    O_CASTLE = 0
    F_CASTLE = 0
    DISCOVER = 2

class ClientController():
    def __init__(self, ip, port, size):
        self.map = []
        self.xy = [0, 0]
        self.xy_scrol = [0, 0]
        self.f_Scrol = False    #found scroll
        self.g_Scrol = False    #got scroll
        self.xy_Fcast = [0, 0]
        self.f_Fcast = False    #found enemy castle
        self.mapsize = size
        self.turn = 0
        self.last_dir = 0

        while len(self.map) < self.mapsize:
            lst = []
            while len(lst) < self.mapsize:
                lst.append(FieldType.UNKNOWN.value)
            self.map.append(lst)


        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.clientsocket:
            try:
                # Verbindung herstellen (Gegenpart: accept() )
                self.clientsocket.connect((ip, port))
                msg = name
                # Nachricht schicken
                self.clientsocket.send(msg.encode())
                # Antwort empfangen
                data = self.clientsocket.recv(1024).decode()
                if not data or not data == "OK":
                    # Schließen, falls Verbindung geschlossen wurde
                    self.clientsocket.close()

                while self.msg_rec():
                    self.go()
                print("end")
                self.clientsocket.close()
            except socket.error as serr:
                print("Socket error: " + serr.strerror)

    def addView(self, view):
        dist = (len(view)-1)/2
        print()
        print("%i ter Zug:" % (self.turn+1))
        print("Sichtweite: %d" % dist)
        print("Position: %i, %i" % (self.xy[0], self.xy[1]))
        for y in range(0, len(view)):
            print(view[y])
            for x in range(0, len(view)):
                ab = self.translate(x, y, dist)
                a = ab[0]
                b = ab[1]
                if view[y][x].upper() == FieldType.CASTLE.value and a != 0 and b != 0:
                    self.f_Fcast = True
                    self.xy_Fcast = [a, b]
                self.map[b][a] = view[y][x].upper()

    def clearView(self):
        self.map = []
        while len(self.map) < self.mapsize:
            lst = []
            while len(lst) < self.mapsize:
                lst.append(FieldType.UNKNOWN.value)
            self.map.append(lst)

    def dijkstra_search(self, goal):
        frontier = PriorityQueue()
        frontier.put(tuple(self.xy), 0)
        goal = tuple(goal)
        came_from = {}
        cost_so_far = {}
        came_from[tuple(self.xy)] = None
        cost_so_far[tuple(self.xy)] = 0

        while not frontier.empty():
            current = frontier.get()

            if current == goal:
                break

            for nextN in self.getNeighbours(current):
                nextN = tuple(nextN)
                new_cost = cost_so_far[current] + self.weight(list(current))
                if nextN not in cost_so_far or new_cost < cost_so_far[nextN]:
                    cost_so_far[nextN] = new_cost
                    priority = new_cost
                    frontier.put(nextN, priority)
                    came_from[nextN] = current

        path = ClientController.reconstruct_path(came_from, tuple(self.xy), goal)
        print(path)
        if len(path) == 0:
            self.g_Scrol = True
            self.go()
        else:
            neighbours = self.getNeighbours(self.xy)
            for i in range(0, len(neighbours)):
                if neighbours[i] == list(path[0]):
                    self.goStep(str(i))

            return path[0]

    def go(self):
        if self.f_Scrol and not self.g_Scrol:
            self.goTo(self.xy_scrol)
        elif self.g_Scrol and self.f_Fcast:
            self.goTo(self.xy_Fcast)
        else:
            self.goRandom()

    def goRandom(self):
        '''dir = {
            '0': 'up',
            '1': 'right',
            '2': 'down',
            '3': 'left'
        }

        dir1 = dir[str(randint(0, 3))]
        self.clientsocket.send(dir1.encode())
        self.moveX(dir)
        '''
        '''
        self.goStep(str(randint(0, 3)))
        return
        '''
        if True:
            neig = self.getNeighbours(self.xy)
            if self.turn > 0:
                neig.pop((self.last_dir+2)%len(neig))
            pqueue = PriorityQueue()
            for i in neig:
                pqueue.put(tuple(i), self.weight(i, 1))

            step = pqueue.get()
            neighbours = self.getNeighbours(self.xy)
            for i in range(0, len(neighbours)):
                if neighbours[i] == list(step):
                    self.goStep(str(i))
        else:
            pass #another algorihtm maybe
        #print(dir1)

    def goStep(self, step):
        dir = {
            '0': 'up',
            '1': 'right',
            '2': 'down',
            '3': 'left'
        }[step]
        self.last_dir = int(step)
        self.clientsocket.send(dir.encode())
        self.moveX(step)

    def goTo(self, xy):
        dij_xy = self.dijkstra_search(xy)

    def getNeighbours(self, xy):
        lst = []
        xy = list(xy)
        for i in range(0, 2):
            if i == 1:
                a = xy[0] - 1
                b = xy[1] + 1
            else:
                a = xy[0] + 1
                b = xy[1] - 1
            a = self.warp(a)
            b = self.warp(b)
            lst.append([self.warp(xy[0]), b])
            lst.append([a, self.warp(xy[1])])

        return lst

    def getNewFields(self, xy):
        i = 0
        lst = []
        dist = 1
        ftype = self.map[xy[1]][xy[0]]
        if ftype == FieldType.GRASS.value:
            dist = 2
        elif ftype == FieldType.MOUNTAIN.value:
            dist = 3

        for y in range(0, (dist+1)*2):
            for x in range(0, (dist+1)*2):
                ab = self.translate(x, y, dist)
                a = ab[0]
                b = ab[1]
                if self.map[b][a] == FieldType.UNKNOWN.value:
                    i += 1
        return i

    def msg_rec(self):
        data = self.clientsocket.recv(1024).decode()
        view = []

        i = int(math.sqrt(len(data)/2))

        if len(data)< 18:
            return False
        if data[1] != ' ' and data[1] != 'B':
            return False

        for y in range(0, i):
            row = []
            for x in range(0, i):
                row.append(data[(i*2*y)+x*2])
                if data[(i*2*y)+x*2+1] == 'B':
                    self.f_Scrol = True
                    ab = self.translate(x, y, (i-1)/2)
                    a = ab[0]
                    b = ab[1]
                    self.xy_scrol = [a, b]
            view.append(row)
            #print(row)

        self.addView(view)
        self.printMap()
        return True

    def moveX(self, i):
        if i == '0':
            self.xy[1] -= 1
        elif i == '1':
            self.xy[0] += 1
        elif i == '2':
            self.xy[1] += 1
        elif i == '3':
            self.xy[0] -= 1
        self.warpX()
        self.turn += 1
        #print(self.xy)

    def printMap(self):
        for i in self.map:
            print(i)

    @staticmethod
    def reconstruct_path(came_from, start, goal):
        current = goal
        path = [current]
        while current != start:
            current = came_from[current]
            path.append(current)
        #path.append(start)  # optional
        path.pop()
        path.reverse()  # optional
        return path

    def translate(self, x, y, dist):
        a = self.xy[0] + x - dist
        b = self.xy[1] + y - dist

        '''if a < 0:
            a = len(self.map) + a
        if a >= len(self.map):
            a = a - len(self.map)
        if b < 0:
            b = len(self.map) + b
        if b >= len(self.map):
            b = b - len(self.map)
        '''
        a = self.warp(a)
        b = self.warp(b)

        a = int(a)
        b = int(b)
        return [a, b]

    def warpX(self):
        if self.xy[1] < 0:
            self.xy[1] = len(self.map) + self.xy[1]
        if self.xy[0] >= len(self.map):
            self.xy[0] = self.xy[0] - len(self.map)
        if self.xy[1] >= len(self.map):
            self.xy[1] = self.xy[1] - len(self.map)
        if self.xy[0] < 0:
            self.xy[0] = len(self.map) + self.xy[0]

    def warp(self, a):
        if a < 0:
            a = len(self.map) + a
        if a >= len(self.map):
            a = a - len(self.map)
        return a

    def weight(self, xy, neibours=0):
        xy[0] = self.warp(xy[0])
        xy[1] = self.warp(xy[1])
        if self.f_Fcast and self.f_Scrol:
            uvalue = 15
        else:
            uvalue = 10
        b = {
            FieldType.UNKNOWN.value: uvalue,
            FieldType.GRASS.value: 10,
            FieldType.FOREST.value: 10,
            FieldType.MOUNTAIN.value: 20,
            FieldType.LAKE.value: 999999,
            FieldType.CASTLE.value: 10
        }[self.map[xy[1]][xy[0]]]
        if not self.f_Fcast and not self.f_Scrol:
            b -= self.getNewFields(xy)*FieldWeight.DISCOVER.value
            b += randint(0, 5)
        if neibours > 0:
            neibours-=1
            c = 0
            for i in self.getNeighbours(xy):
                c += self.weight(i, neibours)
            b += c/len(self.getNeighbours(xy))
        return b

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--ip-address=', type=str, help='server to connect to', default='localhost', dest='server')
    parser.add_argument(
        '-p', '--port=', type=int, help='port number', default=5050, dest='port')
    parser.add_argument(
        '-s', '--size=', type=int, help='size of the map', default=10, dest='size')
    args = parser.parse_args()
    print(args)
    client = ClientController(args.server, args.port, args.size)
