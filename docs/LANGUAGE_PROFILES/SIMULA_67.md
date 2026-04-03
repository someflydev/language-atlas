# SIMULA 67: The Mother of Objects

## Overview
SIMULA 67 is the birthplace of Object-Oriented Programming (OOP). Originally designed for simulation, it introduced the concepts of classes, objects, and inheritance, fundamentally changing how we represent and organize complex software systems by modeling them after the real world.

## Historical Context
Developed in the mid-1960s at the Norwegian Computing Center by Ole-Johan Dahl and Kristen Nygaard, SIMULA 67 was an extension of ALGOL 60. It was a reaction to the difficulty of modeling complex, interacting systems using traditional procedural techniques. While ALGOL focused on the flow of algorithms, SIMULA realized that some problems—like traffic simulation or warehouse management—are better described as a collection of autonomous entities (objects) interacting with each other. It reacted to the "passive data" model of its time by making data "active" through the inclusion of behavior.

## Mental Model
To be effective in SIMULA 67, you must **think in terms of independent actors with their own state and behavior**. A program is not a sequence of instructions; it is a simulated world where entities coexist, maintain their own internal state, and interact through well-defined interfaces.

Your brain must be wired to:
1. **Abstract into Classes:** Stop thinking about "the data" and start thinking about "the thing." What is its nature? What can it do?
2. **Visualize Interaction:** See the program as a set of concurrent or quasi-concurrent processes. In SIMULA, objects aren't just data structures; they can have their own execution lifecycle.
3. **Embrace Hierarchy:** Understand that an object can be a "specialized version" of another. This was the first time programmers had to think about "is-a" relationships (Inheritance).

## Key Innovations
- **Classes and Objects:** The first implementation of templates for creating multiple instances of data-plus-behavior.
- **Inheritance:** The ability to define a new class by extending an existing one.
- **Virtual Procedures:** Allowing a subclass to redefine the behavior of its parent, the foundation of polymorphism.
- **Co-routines:** Support for quasi-parallel execution, essential for simulation.

## Tradeoffs & Criticisms
- **Performance Overhead:** The introduction of garbage collection and dynamic dispatch in 1967 came with a performance cost that the hardware of the time struggled to handle.
- **Complexity:** For simple tasks, the overhead of defining classes and managing objects was seen as unnecessary compared to the directness of ALGOL or FORTRAN.
- **Limited Scope:** Initially, many saw it only as a "simulation tool" rather than a general-purpose programming revolution.

## Legacy
SIMULA 67's legacy is virtually every modern mainstream language. Bjarne Stroustrup directly used SIMULA as the blueprint for C++, and Alan Kay used it as the inspiration for Smalltalk. Java, Python, Ruby, and C# all trace their object-oriented lineage back to the Norwegian Computing Center. It was the "Big Bang" of modern software architecture.

## AI-Assisted Discovery Missions
1. "Trace the lineage from SIMULA 67's 'Classes' to the 'Objects' in Smalltalk and the 'Classes' in C++."
2. "Examine how SIMULA 67's approach to simulation influenced the development of discrete event simulation (DES) today."
3. "Analyze the implementation of inheritance in SIMULA 67 and how it differed from the 'Prototypes' found in later languages like Self or JavaScript."
