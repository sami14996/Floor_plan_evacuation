'''
ToDo:
    Change speed.
    Change number of agents.
    Try all permutations with barriers(4) and gates(3).
    Save graph for each.
'''

from Agent1 import *
from Point import Point

import pygame
from pygame.locals import *
from pygame.color import *
import thinkplot
import random

from datetime import datetime
import pickle
import pandas
import matplotlib.pyplot as plt

import sys

DEBUG = False


class Wall:
    def __init__(self, wallType, **parameters):
        # type : "circle" | "line", points
        # Circle : type='circle' { "center": Point(x,y), "radius": r }
        # Line : type='line'{ "p1": Point(x1,y1), "p2": Point(x2,y2) }
        self.wallType = wallType
        self.parameters = parameters
        self.checkValid()

    def checkValid(self):
        if self.wallType == 'circle':
            assert isinstance(self.parameters["center"], Point), "Circles need a center"
            # assert isinstance(self.parameters["radius"], int), "Radius needs to be an int"

        if self.wallType == 'line':
            assert isinstance(self.parameters['p1'], Point)
            assert isinstance(self.parameters['p2'], Point)

        if self.wallType == 'maze':
            assert isinstance(self.parameters['p1'], Point)
            assert isinstance(self.parameters['p2'], Point)
            assert isinstance(self.parameters['thickness'], int)


class Goal(Wall):
    """ Defines a goal. Currently, only horizontal and vertical lines are supported. """

    def checkValid(self):
        assert self.wallType == 'line'
        assert isinstance(self.parameters['p1'], Point)
        assert isinstance(self.parameters['p2'], Point)
        assert (self.parameters['p1'].x == self.parameters['p2'].x or self.parameters['p1'].y == self.parameters[
            'p2'].y)

        # p1 should always be smaller than p2
        if (self.parameters['p1'].x == self.parameters['p2'].x):
            if self.parameters['p1'].y > self.parameters['p2'].y:
                p1Temp = self.parameters['p1']
                self.parameters['p1'] = self.paramters['p2']
                self.parameters['p2'] = p1Temp
        elif (self.parameters['p1'].y == self.parameters['p2'].y):
            if self.parameters['p1'].x > self.parameters['p2'].x:
                p1Temp = self.parameters['p1']
                self.parameters['p1'] = self.paramters['p2']
                self.parameters['p2'] = p1Temp


class Environment():
    conditions = {'k': 1.2 * 10 ** 5, 'ka': 2.4 * 10 ** 5}

    def __init__(self, N, walls, goals, agents, conditions, instruments):
        self.N = N
        self.walls = walls
        self.goals = goals
        self.agents = agents
        self.instruments = instruments
        # Conditions: Agent force, Agent repulsive distance, acceleration time, step length,
        self.conditions.update(conditions)

    def step(self):
        for agent in self.agents:
            # print(agent.desiredDirection)
            selfDriveForce = agent.selfDriveForce()
            pairForce = Point(0, 0)
            wallForce = Point(0, 0)
            for wall in self.walls:
                wallForce += agent.wallForce(wall)
            for agent2 in self.agents:
                if agent.index == agent2.index:
                    continue
                pairForce += agent.pairForce(agent2)
            netForce = selfDriveForce + pairForce + wallForce
            agent.move(netForce)

        self.updateInstruments()

    def updateInstruments(self):
        for instrument in self.instruments:
            instrument.update(self)

    def plot(self, num):
        self.instruments[num].plot()


class EnvironmentViewer():
    BG_COLOR = Color(233, 235, 238)

    BLACK = Color(0, 0, 0)
    WHITE = Color(255, 255, 255)
    YELLOW = Color(255, 233, 0)
    RED = Color(203, 20, 16)
    #GOAL = Color(252, 148, 37)
    GOAL = Color(21, 119, 40)

    pygameScale = 50

    def __init__(self, environment):
        self.env = environment
        self.screen = pygame.display.set_mode((500,750)) #, pygame.FULLSCREEN

    def draw(self, layout):
        self.screen.fill(self.BG_COLOR)

        if not layout:
            for agent in self.env.agents:
                self.drawAgent(agent)

        for wall in self.env.walls:
            self.drawWall(wall, Color(0, 0, 0))

        for goal in self.env.goals:
            self.drawGoal(goal)

        pygame.display.update()

    def drawAgent(self, agent):
        # Draw agent
        pygame.draw.circle(self.screen, self.RED, agent.pos.pygame, int(agent.size * self.pygameScale))
        # Draw desired vector
        pygame.draw.line(self.screen, self.RED, agent.pos.pygame, (agent.pos + (agent.desiredDirection)).pygame)
        if(DEBUG): print("drew agent at ", agent.pos)

    def drawWall(self, wall, color=WHITE):
        if wall.wallType == 'circle':
            pygame.draw.circle(self.screen, color, wall.parameters['center'].pygame, int(wall.parameters['radius'] * self.pygameScale))
            if(DEBUG): print("drew wall at {}".format(wall.parameters['center']))

        if wall.wallType == 'line':
            pygame.draw.line(self.screen, color, wall.parameters['p1'].pygame, wall.parameters['p2'].pygame, 15)
            if(DEBUG): print("drew wall between {} and {}".format(wall.parameters['p1'], wall.parameters['p2']))

        if wall.wallType == 'maze':
            pygame.draw.line(self.screen, color, wall.parameters['p1'].pygame, wall.parameters['p2'].pygame, wall.parameters['thickness'])
            if(DEBUG): print("drew maze-wall between {} and {}".format(wall.parameters['p1'], wall.parameters['p2']))

    def drawGoal(self, goal):
        self.drawWall(goal, color=self.GOAL)


class Instrument():
    """ Instrument that logs the state of the environment"""

    def __init__(self):
        self.metric = []

    def plot(self, **options):
        thinkplot.plot(self.metric, **options)
        thinkplot.show()


class ReachedGoal(Instrument):
    """ Logs the number of agents that have escaped """

    def update(self, env):
        self.metric.append(self.countReachedGoal(env))

    def countReachedGoal(self, env):
        num_escaped = 0
        num_goals = len(env.agents[0].goals)

        if num_goals == 3:
            for agent in env.agents:
                if agent.pos.x > agent.goals[0].parameters['p1'].x:
                    num_escaped += 1
                elif agent.pos.y > agent.goals[1].parameters['p1'].y:
                    num_escaped += 1
                elif agent.pos.x < agent.goals[2].parameters['p1'].x:
                    num_escaped += 1
        elif num_goals == 2:
            for agent in env.agents:
                if agent.pos.x > agent.goals[0].parameters['p1'].x:
                    num_escaped += 1
                elif agent.pos.y > agent.goals[1].parameters['p1'].y:
                    num_escaped += 1
        elif num_goals == 1:
            for agent in env.agents:
                if agent.pos.x > agent.goals[0].parameters['p1'].x:
                    num_escaped += 1
        return num_escaped



def randFloat(minVal, maxVal):
    return random.random() * (maxVal - minVal) + minVal

def runSimulation(roomHeight=10,
                  roomWidth=8,
                  barrier=1, # pos is relative to door center
                  num_goals=3,
                  doorWidth=1.5,
                  numAgents=50,
                  agentMass=80,
                  desiredSpeed=4,
                  view=False,
                  layout=False):

    walls = []
    # Only add barrier if its radius is above 0
    if barrier==1:
        # gate 1
        walls.append(Wall('maze', **{ 'p1': Point(8, 7), 'p2':Point(8, 10), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(8, 12), 'p2':Point(8, 14), 'thickness':20 }))
        # gate 2
        walls.append(Wall('maze', **{ 'p1': Point(5, 1), 'p2':Point(5, 4), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(5, 5), 'p2':Point(5, 7), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(4, 9), 'p2':Point(4, 12), 'thickness':20 }))
        # gate 3
        #walls.append(Wall('maze', **{ 'p1': Point(2, 4), 'p2':Point(2, 8), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(2, 10), 'p2':Point(2, 13), 'thickness':20 }))
        # gate 4
        walls.append(Wall('maze', **{ 'p1': Point(5, 13), 'p2':Point(7, 13), 'thickness':20 }))
        # walls.append(Wall('circle', **{ 'center': Point(roomWidth + barrier['pos'].x, roomHeight//2 + barrier['pos'].y), 'radius': barrier['length'] }))
        # walls.append(Wall('circle', **{ 'center': Point(roomWidth + barrier['pos'].x-1, roomHeight//2 + barrier['pos'].y+1), 'radius': barrier['length'] }))
        # walls.append(Wall('circle', **{ 'center': Point(roomWidth + barrier['pos'].x-3, roomHeight//2 + barrier['pos'].y-3), 'radius': barrier['length'] }))
    elif barrier==2:
        # gate 1
        walls.append(Wall('maze', **{ 'p1': Point(5, 1), 'p2':Point(5, 4), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(5, 5), 'p2':Point(5, 7), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(4, 8), 'p2':Point(4, 11), 'thickness':20 }))
        # gate 2
        walls.append(Wall('maze', **{ 'p1': Point(2, 7), 'p2':Point(2, 10), 'thickness':20 }))
        # gate 3
        walls.append(Wall('maze', **{ 'p1': Point(4, 13), 'p2':Point(6, 13), 'thickness':20 }))
    elif barrier==3:
        # vertical barriers
        walls.append(Wall('maze', **{ 'p1': Point(2.5, 2.5), 'p2':Point(2.5, 6.5), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(7.5, 3.5), 'p2':Point(7.5, 7.5), 'thickness':20 }))
        # horizontal barriers
        walls.append(Wall('maze', **{ 'p1': Point(4, 4), 'p2':Point(6, 4), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(3, 9), 'p2':Point(6, 9), 'thickness':20 }))
        walls.append(Wall('maze', **{ 'p1': Point(4, 13), 'p2':Point(6, 13), 'thickness':20 }))


    walls.append(Wall('line', **{ 'p1': Point(0, 0), 'p2': Point(roomWidth, 0) })) # TOP
    # walls.append(Wall('line', **{ 'p1': Point(0, 0), 'p2': Point(0, roomHeight) })) # LEFT
    walls.append(Wall('line', **{ 'p1': Point(0, 0), 'p2': Point(0, roomHeight/3) })) # LEFT (Top Doorway)
    walls.append(Wall('line', **{ 'p1': Point(0, roomHeight/3 + doorWidth), 'p2': Point(0, roomHeight) })) # LEFT (Bottom Doorway)
    walls.append(Wall('line', **{ 'p1': Point(0, roomHeight), 'p2': Point(roomWidth/5, roomHeight) })) # BOTTOM (Left Doorway)
    walls.append(Wall('line', **{ 'p1': Point(roomWidth/5 + doorWidth, roomHeight), 'p2': Point(roomWidth, roomHeight) })) # BOTTOM (Right Doorway)
    walls.append(Wall('line', **{ 'p1': Point(roomWidth, 0), 'p2': Point(roomWidth, roomHeight/5) })) # RIGHT (Top Doorway)
    walls.append(Wall('line', **{ 'p1': Point(roomWidth, roomHeight/5 + doorWidth), 'p2': Point(roomWidth, roomHeight) })) # RIGHT (Bottom Doorway)


    goals = []
    if num_goals>=1:
        goals.append(Goal('line', **{ 'p1': Point(roomWidth, roomHeight/5), 'p2': Point(roomWidth, roomHeight/5 + doorWidth) })) # RIGHT GOAL
        if num_goals >= 2:
            goals.append(Goal('line', **{ 'p1': Point(roomWidth/5, roomHeight), 'p2': Point(roomWidth/5 + doorWidth, roomHeight) })) # BOTTOM GOAL
            if num_goals >=3 :
                goals.append(Goal('line', **{ 'p1': Point(0, roomHeight/3), 'p2': Point(0,roomHeight/3 + doorWidth) })) #LEFT GOAL

    #goals.append(Goal('line', **{ 'p1': Point(roomWidth/5, roomHeight), 'p2': Point(roomWidth/5 + doorWidth, roomHeight) }))
    # goals.append(Goal('line', **{ 'p1': Point(roomWidth, roomHeight/2 - doorWidth/2), 'p2': Point(roomWidth, roomHeight/2 + doorWidth/2) }))

    instruments = []
    instruments.append(ReachedGoal())


    agents = []
    for _ in range(numAgents):
        # Agent(size, mass, pos, goal, desiredSpeed = 4))
        size = randFloat(.25, .35)
        mass = agentMass
        pos = Point(randFloat(roomWidth/3 - .5, 3*roomWidth/3 - .5), randFloat(.5, roomHeight - .5))
        agents.append(Agent(size, mass, pos, goals, desiredSpeed=desiredSpeed))

    env = Environment(100, walls, goals, agents, {}, instruments)

    if view:
        viewer = EnvironmentViewer(env)
        viewer.draw(layout)

    env.step()

    # print(env.instruments[0].metric)
    # Run until all agents have escaped
    while env.instruments[0].metric[-1] < len(env.agents):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # if ESC key pressed, shut the game window and plot the graph
                    pygame.quit()
                    return env.instruments[0].metric
        env.step()
        if view:
            viewer.draw(layout)
            # pygame.event.wait()
        if (len(env.instruments[0].metric) % 100 == 0):
            message = "num escaped: {}, step: {}".format(env.instruments[0].metric[-1], len(env.instruments[0].metric))
            sys.stdout.write('\r' + str(message) + ' ' * 20)
            sys.stdout.flush() # important

            pygame.display.set_caption(message)

        if len(env.instruments[0].metric) == 6000:
            break


    print()
    return env.instruments[0].metric

def runExperiment():
    x = []
    time_to_escape = []
    for num_agents in range(50, 500, 50):
        statistics = runSimulation()

        x.append(num_agents)
        time_to_escape.append(len(statistics))

    export = [x, time_to_escape]
    # with open("{}.pd".format(datetime.time()), "r") as outfile:
    #     pickle.dump(export, outfile)


def plot(results, title):
    print("Hi")
    plt.plot(list(range(0, len(results))), results)
    plt.xlabel("Time steps")
    plt.ylabel("Number of agents escaped")
    plt.title("Plotting the Number of Escaped Agents Against Time: {}".format(title))
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    simResult = runSimulation(barrier=0, num_goals=3, view=True, desiredSpeed=5, numAgents=40, roomHeight=15, roomWidth=10) # { 'length': 3, 'pos': Point(-1,0)}
    plot(simResult)
    # print(simResult)
    # thinkplot.plot(defaultExperiment)
    # thinkplot.show()