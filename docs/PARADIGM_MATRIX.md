# Paradigm Matrix

This matrix compares major programming languages against the 14 fundamental paradigms explored in the Language Atlas. It highlights the distinction between "Pure" languages, multi-paradigm pragmatic languages, and cases where a paradigm is actively discouraged.

## Legend
- **P (Primary):** The language was designed around this paradigm; it is the "default" way of thinking.
- **S (Supported):** The paradigm is well-supported through first-class features or standard libraries.
- **A (Anti-pattern):** While technically possible, using this paradigm is discouraged or requires significant "hacks."
- **- (N/A):** The paradigm is not natively supported or relevant to the language's core model.

## The Matrix

| Language | Proc | OOP | Func | Log | Arr | Cat | Data | Act | React | Asp | Event | Gen | Const | Meta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ada** | P | S | - | - | - | - | - | S | - | - | S | P | - | - |
| **ALGOL 60** | P | - | - | - | - | - | - | - | - | - | - | - | - | - |
| **APL** | S | - | S | - | P | - | - | - | - | - | - | - | - | - |
| **C** | P | A | - | - | - | - | - | - | - | - | S | - | - | - |
| **C++** | P | P | S | - | - | - | - | S | S | - | S | P | - | P |
| **C#** | S | P | S | - | - | - | S | S | S | S | P | P | - | S |
| **Clojure** | - | A | P | - | - | - | P | - | S | - | - | - | - | P |
| **COBOL** | P | S | - | - | - | - | P | - | - | - | - | - | - | - |
| **Erlang** | - | - | P | - | - | - | - | P | S | - | P | - | - | - |
| **Elixir** | - | - | P | - | - | - | - | P | S | - | P | - | - | P |
| **FORTRAN** | P | - | - | - | S | - | - | - | - | - | - | - | - | - |
| **Forth** | P | - | - | - | - | P | - | - | - | - | - | - | - | P |
| **Go** | P | S | - | - | - | - | - | S | - | - | S | S | - | - |
| **Haskell** | - | - | P | - | - | - | - | - | S | - | - | P | - | S |
| **Java** | S | P | S | - | - | - | - | S | S | S | S | P | - | S |
| **JavaScript** | S | S | S | - | - | - | - | - | S | - | P | - | - | S |
| **Julia** | S | S | S | - | P | - | - | S | S | - | S | P | - | P |
| **Kotlin** | S | P | S | - | - | - | - | S | S | - | S | P | - | S |
| **Lisp** | S | S | P | S | - | - | S | - | - | - | S | S | - | P |
| **ML** | - | - | P | - | - | - | - | - | - | - | - | P | - | - |
| **Nim** | P | S | S | - | - | - | - | - | - | - | S | P | - | P |
| **OCaml** | S | S | P | - | - | - | - | - | - | - | - | P | - | - |
| **Pascal** | P | S | - | - | - | - | - | - | - | - | - | - | - | - |
| **Perl** | P | S | S | - | - | - | S | - | - | - | S | - | - | S |
| **Prolog** | - | - | - | P | - | - | - | - | - | - | - | - | P | - |
| **Python** | P | P | S | - | - | - | - | S | S | - | S | S | - | S |
| **Ruby** | S | P | S | - | - | - | - | - | - | - | S | - | - | P |
| **Rust** | P | S | S | - | - | - | - | S | - | - | S | P | - | P |
| **Scala** | - | P | P | - | - | - | - | S | S | - | S | P | - | P |
| **Smalltalk** | - | P | - | - | - | - | - | S | - | - | P | - | - | P |
| **SQL** | - | - | - | - | S | - | P | - | - | - | - | - | P | - |
| **Swift** | S | P | S | - | - | - | - | S | S | - | S | P | - | S |
| **TypeScript**| S | S | S | - | - | - | - | - | S | - | P | P | - | S |

## Paradigm Crossovers

As seen in the matrix, modern "renaissance" languages like **Rust**, **Scala**, **Swift**, and **Julia** are increasingly multi-paradigm. The historical trend shows a merging of Functional and Object-Oriented concepts to handle the dual requirements of safety and domain modeling.

### Diagram Required: Paradigm crossover graph
A graph showing the evolution of languages from pure single-paradigm (like Smalltalk or ALGOL) toward the highly interconnected multi-paradigm state of the modern era.

## Observations on "Primary" (P) Assignments
- **Clojure** treats Data-driven (P) and Functional (P) as equal citizens, reflecting its philosophy of "de-complecting" state and data.
- **SQL** is one of the few languages where Constraint (P) is a primary way of working, alongside its Data-driven (P) core.
- **Smalltalk** remains the purest example of the "everything is an object" philosophy, even influencing its Event-driven and Metaprogramming models.
- **Prolog** stands almost alone in the Logic (P) and Constraint (P) space among major atlas languages.
