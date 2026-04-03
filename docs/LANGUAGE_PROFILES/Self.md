# Self: The Purity of the Prototype

## Overview
Self is a prototype-based, object-oriented programming language and environment that takes the principles of Smalltalk to their logical conclusion. It eliminates the concept of "classes," treating every object as a unique entity that can be cloned and refined.

## Historical Context
Developed by David Ungar and Randall Smith at Xerox PARC (and later Stanford and Sun Microsystems) starting in 1987, Self was a research language designed to simplify the Smalltalk model. It became a pioneer in Just-In-Time (JIT) compilation techniques that are now standard in modern JavaScript engines.

## Mental Model
To understand Self, you must **stop thinking in blueprints**. There are no "classes" to define how an object *should* look; there are only "prototypes" that define how an object *is*.

Your brain must be wired to:
1. **Clone and Refine:** To create a new object, you don't call a constructor; you clone an existing object and add or modify its "slots."
2. **Think in Slots:** Everything (state and behavior) is stored in a slot. Accessing a slot is the same whether it's a variable or a method, enforcing a "Uniform Access Principle."
3. **Embrace Dynamic Inheritance:** Objects inherit directly from other objects (parents). Changing a parent object immediately affects all its descendants, allowing for extreme flexibility.

## Key Innovations
- **Prototypal Inheritance:** Replacing the class hierarchy with a much simpler model based on cloning and delegation.
- **JIT Compilation Pioneer:** Self's virtual machine introduced many optimization techniques, such as polymorphic inline caching, that paved the way for modern, high-performance VMs.
- **Direct Manipulation UI:** The Self environment allowed programmers to literally "pick up" and move objects on the screen, blurring the line between the program and the user interface.
- **Uniform Access:** Treating data members and methods identically, simplifying the conceptual model of the object.

## Tradeoffs & Criticisms
- **Performance Overhead:** The extreme dynamism of Self required massive effort in VM optimization to reach acceptable speeds, making it complex to implement.
- **Conceptual Shift:** For programmers raised on class-based languages (Java, C++), the shift to prototypes can be disorienting and difficult to manage at scale.
- **Academic Niche:** Despite its brilliance, Self never gained widespread commercial adoption, remaining largely a research tool for VM and UI designers.

## Legacy
Self's greatest legacy is **JavaScript**. The prototypal inheritance model and the JIT techniques developed for Self are the foundation of the modern web. It also influenced NewtonScript, Lua, and the development of the Dart language.

## AI-Assisted Discovery Missions
1. "How did Self's 'Prototypal Inheritance' influence the design of JavaScript, and why did JS eventually add 'classes' back in?"
2. "Explore the concept of 'Polymorphic Inline Caching'—how did this Self-pioneered technique make dynamic languages fast enough for production?"
3. "What does it mean to have an environment where you can 'directly manipulate' objects? How does this differ from modern IDEs?"
