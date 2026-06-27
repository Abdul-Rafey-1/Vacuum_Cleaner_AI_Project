Vacuum Cleaner AI Simulator
An interactive real time graphical user interface simulation developed for an Introduction to Artificial Intelligence course. The project models a goal based vacuum cleaner agent operating in a dynamic 10 by 10 grid environment to visually contrast and analyze the efficiency of graph search pathfinding versus an uninformed baseline strategy.

Project Overview
The objective of this project is to simulate an autonomous agent tasked with keeping a changing grid environment clean. The grid handles dynamic elements, capping active dirt tiles at 25 while generating new clean up targets every 40 steps. The simulation provides an analytical comparison between two search architectures:

1. Breadth First Search Agent: An informed pathfinding model. It evaluates the environment globally, targeting the nearest dirty cell using an optimal layer by layer exploration path.
2. Random Walk Agent: An uninformed, purely reactive model. It moves randomly to adjacent spaces, only prioritizing a dirty square if it is directly adjacent.
   
Key Architectural Features
Dynamic Environment Simulation: Generates random dirt drops over regular operational intervals.
Interactive Control Panel: Built completely via Tkinter, allowing live switching between AI strategies, parameter resets, and discrete manual stepping.
Live Speed Scale Manipulation: Integrates adjustable execution speeds ranging from 50 milliseconds up to 800 milliseconds per action step.

Graphical Status Tracking: Live rendering for steps taken, total cells cleaned, remaining grid dirt, and current vector tracking of the vacuum agent.

Core Algorithms Implemented
1. Breadth First Search
The agent calculates its trajectory by searching outward uniformly from its current location until it discovers the closest node flag matching a target configuration.
2. Random Walk
The baseline model polls valid neighbor indexes and selects an arbitrary vector using pseudo random choice, mimicking zero memory structure.

Project Repository Structure
vacuum_cleaner.py: The core production script containing the visual application layer, asset coordinate generation, and path execution rules.
vacuum_cleaner.exe: Precompiled standalone executable file enabling zero dependency runtime environments on Windows machines.

Installation and Execution
Prerequisites
Make sure you have Python installed on your device. Tkinter comes bundled with standard Python distributions.

Evaluation Metrics
When reviewing performance markers via the user interface:
Efficiency: The Breadth First Search Agent completes cleanup workflows with significantly fewer steps by finding shortest paths across the grid.
Redundancy: The Random Walk Agent experiences regular re tracking loops over clean cells, highlighting why systematic pathfinding is crucial for autonomous robotics.  
