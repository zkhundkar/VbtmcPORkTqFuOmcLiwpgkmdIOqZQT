# Training a Q-Learning Agent

#### Introduction

In this project, we used `pygame` to simulate a world where multiple vehicle agents were travelling around a rectangular 6x8 grid following traffic rules, and a principal agent was assigned the task of getting from point A to point B. The goal was to use reinforcement learning (specifically Q-learning) to train the principal agent (also the driving agent, could be representing a smart-cab) to accomplish the assigned task in an optimal fashion. In a real-world scenario, optimal fashion would imply getting to the destination in the least amount of time and avoiding any accidents along the way. In our simulation, we equated "avoiding accidents" to "always following traffic rules". We define a metric for the "least time" optimal duration that takes into consideration both the distance between start and end grid points and the stochastic delays added by traffic lights. 
.
The environment provides the following information about the world (in a local sense) to the agent at each turn intersection:
•	The next way-point location relative to its current location and heading.
•	The state of the traffic light at the intersection and the presence of oncoming vehicles from other directions.
•	The current time left from the allotted deadline.
Code for the guts of the simulation, the environment, planner and a basic stationary agent was provided by Udacity. 

#### State space
We evaluated several combinations of input variables (information provided by the environment to the agent), including both a minimal set and an exhaustive set and presented arguments to justify excluding some variables and creating "engineered" features for others. We completed the full analysis described below with three sets of states.

#### Performance metrics
We used four performance measures to compare several different policies:
- percentage of _success_ -- a trip being counted a _success_ when the cab was able to reach its destination in the allotted time
- percentage of _bad moves_ -- a bad move being one where the agent moved in a direction other than one indicated by the planner (with allowances for obeying traffic rules, e.g., no move when light was red and the planner indicated a left turn)
- average number of traffic violations per trip -- a violation was a move not permitted by US traffic laws
- average trip duration ratio -- the ratio of actual trip duration to optimal duration, averaged over the full training session.


#### Random benchmark
To gain a sense of how the simulation works and establish a baseline against which to compare our training algorithms, we first explored a policy where the driving agent chose a random action from the set of possible actions without considering any of the information available from the environment. In a typical run we observed the driving agent wander around the grid,  as would be expected from a random policy. The agent reached its destination 1 in 6 trips; about 50% of the moves very considered _bad_ moves and a similarly high number of them were traffic violations. The average trip duration was more than three times longer than the optimal duration.

#### Q-learning
We implemented Q-learning with greedy and e-greedy policies. we trained the agent over 100 trips and ran multiple sets of training sessions for different learning parameters to gather good statistics to find optimal learning parameters. With our selected set of learning rate and discount rate, the agent attained success in 98% of the trips, made _bad_ moves 2% of the time and the average trip duration was 15% longer than the optimal duration. We achieved the best results with the greedy policy.

#### Full report

Available [here](./report.pdf).

## Usage ##
 
The content included here is for review only. Please do not fork, clone or download without permission.

## License ##
All rights reserved

## Usage ##
 
The content included here is for review only. Please do not fork.

## License ##
All rights reserved
