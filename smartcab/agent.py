import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator
import itertools
import math
import json

"""
Note
----
This module was provided as part of a project curated by Udacity
as part of their Machine Learning Engineer nanodegree. It is expected to implement a 
software agent that uses Q-learning to discover an optimum policy for navigating 
lights and other agents in a grid-world simulation of driving in a city.

Code stubs were provided for the LearningAgent class constructor, reset and update methods,
as well as the run method in the module.

My contributions are:
LearningAgent
    __init__		    all code below the ##TODO comment (line 43)
    _set _learning_rates    all code
    _get_state 		    all code
    _random_gibbs	    all code
    reset		    all code below the #TODO comment (line 133)
    update		    all code below the #TODO comment (line 147)
    
module functions
    main	    essentially all code
    summarize	    all code
    output	    all code
    
While the module is runnable, it has dependencies that are not met in
the code included in this repository. Those dependencies, while available
in public repositories or archives, are not work I can share without
permission. 
"""
        
class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'green'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here

        # Set up two small indexes to assist with storing actions in columns
        #  of a matrix (for ease of computation)
        self.action_index = {0:None, 1:'forward', 2:'left', 3:'right'}
        self.action_rev = dict([(v, j) for j,v in self.action_index.iteritems() if v])

        # Set up state space and 
        signals = ['red', 'green']
        traffic = [None,'forward','left','right']
        waypoints = [x for x in traffic if x] # should be one of left, forward or right
        # Set up time-remaining as a binary engineered feature
        #    < 6 steps = 0
        #    >= steps = 1, use 1000 as an upper limit to the time remaining
        self.trip_markers = [6, 1000]

        # Initialize an array for all states, qmatrix and the transition-state matrix
        state_val_sets = [signals]+[traffic]*2 + [waypoints] + [[str(tm) for tm in self.trip_markers]]
        self.statelist = list(itertools.product(*state_val_sets))
        num_states = len(self.statelist)
        # Initialize the Q-matrix with 0
        self.qmatrix = [[0]*len(self.env.valid_actions) for _ in range(num_states)] # Q-matrix initialized 
        # Initialize the Transition-state matrix with 0
        self.transmatrix = [[0]*num_states for i in range(num_states)]        
   
        # variables and parameters for e-greedy (used in _random_giibs)
		# The arbitrary limits are designed to avoid math overflow errors
        self.max_temp = 10.0
        self.min_temp = 0.02

        # variables to track performance of simulations
        self.success_rate = 0
        self.demerits = []
        self.rewards = []
        self.time_remaining = 0
        self.episodes = []
        self.this_episode = None
        self.last_deadline = None

    def _set_learning_rates(self, alpha, gamma, epsilon):
        """Set the learning rate parameters once per simulation
        
        Arguments
        ---------
            gamma<float>	discount rate
            alpha<float>	learning rate
            epsilon<float>	gibbs or boltzmann factor
                
        Note
        ----
            The boltzmann factor (epsilon) is set into self.bfactor. It is a
            variable used to control how quickly the selection criteria switches
            from random to greedy. 
            High b-factor, e.g. 5 or 10 -- selection stays random for many visits
            b-factor = 1 -- selection switches to greedy in 5 or 6 visits
            smaller b-factor e.g., 0.5 -- faster switch to greedy
            b-factor < 0.1 -- effectively greedy 
        """
        self.gamma = gamma      # discount rate
        self.alpha = alpha      # learning rate
        self.bfactor = epsilon  # gibbs or boltzmann factor

    def _get_state(self, inputs, nextdir, dist):
        """Calculate the index of the state in which we are now and the appropriate trip marker
        
        Arguments
        ---------
            inputs<dict>	- dictionary of observations of the current state
            nextdir<string>	- direction we want go as directed by the route planner
            dist<int>		- distance (manhattan) to goal
            
        Return
        ------
            <int>	index of current state in self.statelist 
                
        Note
        ----
        The trip marker determines the value of the engineered feature based on remaining time
            dist < 6 -- value is 0
            dist >= 6 -- value is 1
        """
		
        d = max(0,int(dist))
        if self.trip_markers[-1]-1 < d:
            tripm = self.trip_markers[-1]
        else:
            comp = [1 if x > d else 0 for x in self.trip_markers]
            tripm = self.trip_markers[ comp.index(1) ]
            
        # compute the tuple for the current state and return its index
        return self.statelist.index( tuple([inputs[x] for x in ['light', 'oncoming', 'left']]\
					+ [nextdir, str(tripm)]) )

    def _random_gibbs(self, s, k):
        """Calculate the action to be selected using a gibbs/boltzmann distribution.
			based on the current set of Q-values in the transition matrix and the
			number of times this state has been visited.
        
        Arguments
        ---------
                s<list>	list of Q-values for observed transitions from state S.
                                There will be one entry for each action
                k<int>	number of visits to state S
                
        Return
        ------
                <int>	index of action in (state, action, state') transition matrix
        
        Note
        ----
                temp - calculates the temperature for the probability distribution
                                for selecting one from the set of possible actions. When
                                k is small, the distribution is wide and the choice becomes
                                closer to random. When k becomes large, temp get very small
                                and the probability distribution shifts to weigh the
                                greedy choice (one with the highest Q-value) more heavily.
                sg	 - calculates a raw weight for each action
        
        """
        try:
            temp = max(self.min_temp, self.max_temp*math.exp(-k/self.bfactor))
            sg = [math.exp(x*1.0/temp) for x in s]
        except OverflowError as e:
            print e, s, k, temp
            raise

        acc = 0
        ch = random.random() # selects a random number (float) between 0 and 1
        _ssum = sum(sg)
        for i,x in enumerate(sg):
                        acc += x/_ssum	# calculate the cumulative sum of probabilities
                        if ch<acc:
                                return i	# index of selected action
        return len(s)-1	#	
        
    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required

        # add a new episode as trip is starting
        self.this_episode = {}
        self.episodes.append(self.this_episode)
        self.rewards = self.this_episode['rewards'] = []
        self.this_episode['trip'] = []
 
    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        # TODO: Update state

        # Calculate the manhattan distance to the destination
        dest = self.planner.destination
        here = self.env.agent_states[self]['location']
        dist = str(abs(dest[0] - here[0]) + abs(dest[1] - here[1]))
        xaction = self.next_waypoint

        this_state = self._get_state(inputs, xaction, deadline)
        self.state = str(self.statelist[this_state])

        # gather additional information for tracking episodes for performance
        if len(self.this_episode['trip']) == 0:
            self.this_episode['trip'] = [here, dest, int(dist), deadline, int(dist) ]
        
        if inputs['light']=='red' and (xaction != 'right') and (self.this_episode['trip'][4] > len(self.rewards)):
            self.this_episode['trip'][4] +=  1   
                            
        # TODO: Select action according to your policy
        ## needs to pick the best possible action
		## self.next_waypoint is the action necessary to get to the next waypoint determined by the planner
            
        if self.bfactor < 0: #greedy choice, with random selection over multiple actions equal to max
            max_action = max(self.qmatrix[this_state])
            action = random.choice([a_index for a_index, act in enumerate(self.qmatrix[this_state]) if act==max_action])
            action = self.action_index[action]
            
        elif self.bfactor > 200: # force random choice all the time
            action = random.choice(self.env.valid_actions) # random moves for now
        else:
            # use the e-greedy action selection method
            # the sum over all columns of the transition matrix
            # gives us the number of times we've chosen an action from
            # the current state previously
            action = self._random_gibbs(self.qmatrix[this_state], sum(self.transmatrix[this_state]))
            action = self.action_index[action]
            
        # Execute action and get reward
        reward = self.env.act(self, None if action=='none' else action)

        # TODO: Learn policy based on state, action, reward
        this_action = self.action_rev[action] if action else 0
        new_state = self.env.agent_states[self]['location']
        next_inputs = self.env.sense(self)
        next_dir = self.planner.next_waypoint()
        if not next_dir:
            next_dir = random.choice(['forward', 'left', 'right'])

        next_state = self._get_state(next_inputs, next_dir, deadline-1)

        self.transmatrix[this_state][next_state] += 1
        
        self.rewards.append(reward)
        self.this_episode['remaining'] = deadline-1
        self.last_deadline = deadline
        
        if reward > 2.0: #reached destination
            # we landed in a terminal state which has no transitions, so all further
            # actions have value = 0
            maxr = 0

            # gather performance info
            self.success_rate += 1
        else:
            #  maximum reward for all actions from the state we landed in
            maxr = max( self.qmatrix[next_state] )

        # update qmatrix - include learning rate, discount rate, immediate reward and
        #    maximum reward for all actions from the state we landed in
        qs = self.qmatrix[this_state][this_action]*(1-self.alpha) + self.alpha*(reward + self.gamma*maxr)
        self.qmatrix[this_state][this_action] = qs
        return

def run(alpha=0.5, gamma=0.5, epsilon=-15.0, summary_output=None):
    """Run the agent for a finite number of trials."""

    ## added optional inputs to pass in values of alpha, gamma, and episilon
    # We use the value of epsilon as a temperature factor with some special values
    #       random (epsilon > 200) - forced random
    #       greedy (epsilon < -1.0)
    #    e-greedy   0 < epsilon < 5.0 - value higher than 5 will use the e-greedy algorithm, but
    #                                   behave like random selection
    #   Larger values of epsilon imply more likely the selection action uses a random policy
    #
    # summary_output is an optional list provided by the calling routine to hold the summary of
    # the performance of a run (set of n_trials). The calling routine will generate any permanent output
    

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
    # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

    # Set learning parameters for driving agent
    a._set_learning_rates(alpha, gamma, epsilon)
    
    # Now simulate it
    sim = Simulator(e, update_delay=0.2, display=True)  # create simulator (uses pygame when display=True, if available)
    # NOTE: To speed up simulation, reduce update_delay and/or set display=False

    sim.run(n_trials=100)  # run for a specified number of trials
    # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line
    #output_results(100, a, summary_output)

    return

def output_results(n_trials, sim_results, _output):
    # produce output to be used in report
    if isinstance(_output, list):
        results = { 'metrics': summarize(sim_results.episodes, n_trials)}
        
        results['alpha']=sim_results.alpha
        results['gamma']=sim_results.gamma
        if False:
            results['episodes']=sim_results.episodes
            _output.append(results)
        else:
            _output.append(sim_results.episodes)
    
    a = sim_results
    print("Agent reached destination within time limits {} times.".format(a.success_rate))
    print('\nLearning parameters: alpha={}, gamma={}, boltzmann-factor={}'.format(a.alpha, a.gamma, a.bfactor))

    with open('smartcab5q_greedyopt.json','wb') as fp:
        json.dump([sim_results.episodes, sim_results.statelist, sim_results.qmatrix], fp)

    return
    print('\n\t\tQ-matrix \t\t\t {}'.format([x for x in a.action_index.values()]))
    for state, row in enumerate(a.qmatrix):
        visits = sum(a.transmatrix[state])
        if visits > 0:
            print(" {} | {} | \t{:4d} | \t {}".format( state, ", ".join([aa if aa else 'none' for aa in a.statelist[state]]), visits, " | ".join([str(round(x,3)) for x in row])))
    

def summarize(episodes, numsim):
    # Summary of several sets of simulations for optimizing alpha and generating heatmap for report
    successes=[]
    demerits= []
    accidents = []
    trip_length = []
    tot_reward = []
    opt_reward = []

    
    for e in episodes:
        if e['remaining']>0:
            success = True
            successes.append(1)
        else:
            successes.append(0)
        x = [1 if reward<0 else 0 for reward in e['rewards'] ]
        trip_steps = len(e['rewards'])
        demerits.append(100.0*sum(x)/trip_steps)
        tot_reward.append(sum(e['rewards']))
        violations = len([x for x in e['rewards'] if x < -0.5])
        accidents.append(violations)
        dist = int(e['trip'][4])
        trip_length.append(1.0*trip_steps/dist)
            
        opt_reward.append( e['trip'][2]*2.0 +  10.0 )
    return [numsim, successes, demerits, accidents, trip_length, tot_reward, opt_reward]
        
ssm=[]
if __name__ == '__mainx__':

    if False:
        for gm in range(1, 10, 1):
            for al in range(1, 10, 1):
                for x in range(20):
                    run(al*0.1, gm*0.1, -5.0, ssm)
    else:
        for x in range(1):
            run(0.4, 0.1, -2.0, ssm)
