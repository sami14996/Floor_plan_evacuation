'''
Plain layout figure.
'''


from Environment1 import runSimulation, plot


def main():
    # set variables
    barrier_layouts = [0, 1, 2, 3]
    barrier_layout = barrier_layouts[3]
    goals = [1, 2, 3]
    goal = goals[2]
    caption = "\nBarrier Layout = 0; Gates = 3"
    agent_velocity = 5
    num_agents = 40
    # run the simulation
    simResult = runSimulation(barrier=barrier_layout, 
        num_goals=goal, 
        view=True, 
        desiredSpeed=agent_velocity, 
        numAgents=num_agents, 
        roomHeight=15, 
        roomWidth=10, 
        layout=False
    )
    plot(simResult, title=caption)

if __name__ == "__main__":
    main()