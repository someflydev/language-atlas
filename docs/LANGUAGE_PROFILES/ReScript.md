# ReScript: The Fast Path to Typed JavaScript

## Overview
ReScript is a statically typed language that is purpose-built for the JavaScript ecosystem. It is a rebranding and evolution of the ReasonML/BuckleScript toolchain, focused entirely on providing the fastest and most robust way to write typed JS.

## Historical Context
Officially announced in 2020 by Hongbo Zhang and the BuckleScript team, ReScript represents a "branching off" from the broader OCaml/ReasonML ecosystem. The goal was to simplify the toolchain and focus exclusively on producing high-quality JavaScript output without the baggage of OCaml's multi-backend support.

## Mental Model
To excel in ReScript, you must **think in terms of the "Best Possible JavaScript."** The language is a tool for professional JS engineers who want the safety of a functional type system without sacrificing build speed or interop.

Your brain must be wired to:
1. **Prioritize Build Speed:** ReScript is designed to compile in milliseconds, even for massive projects, enabling a truly "instant" feedback loop.
2. **Focus on JS Interop:** The language is designed to map directly to JS patterns, making it easy to use existing NPM packages and produce clean, human-readable code.
3. **Embrace Minimalist Functionalism:** ReScript keeps the most powerful parts of OCaml (pattern matching, variants, modules) but discards more complex features that don't map well to the JS world.

## Key Innovations
- **Blazing Fast Compiler:** One of the fastest compilers in the industry, often several orders of magnitude faster than TypeScript.
- **Zero-Cost Abstractions:** ReScript features like variants and modules are compiled into highly optimized JS that has zero runtime overhead.
- **Human-Readable JS Output:** Unlike many transpilers, ReScript produces code that looks like it was written by a senior JS developer.
- **Refined Type System:** A sound, inferred type system that provides 100% coverage without the need for manual annotations.

## Tradeoffs & Criticisms
- **Smaller Ecosystem:** ReScript has a smaller community and fewer dedicated libraries than TypeScript, requiring more manual binding work.
- **Functional Paradigm Shift:** It still requires developers to embrace functional programming, which can be a hurdle for those accustomed to imperative or OO patterns.
- **Rebranding Confusion:** The transition from BuckleScript/ReasonML to ReScript caused significant friction and loss of momentum in the early years.

## Legacy
ReScript is the premier choice for teams that prioritize build speed and runtime safety above all else. It has set a new bar for what a "JS-focused" compiler can achieve, proving that you don't have to sacrifice performance for safety.

## AI-Assisted Discovery Missions
1. "Compare a ReScript build with a TypeScript build for a project with 1000+ files—why is ReScript so much faster?"
2. "Demonstrate 'JS Interop' in ReScript—how do you call a standard NPM package like 'lodash' or 'axios' with full type safety?"
3. "Analyze the generated JS output of a ReScript 'Variant'—how does it compare to an equivalent 'Enum' or 'Union' in TypeScript?"
