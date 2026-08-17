"""Formal Sciences K1 - 17 specialties in 5 batches (4+4+3+3+3)."""

FORMAL_K1_BATCH1: dict[str, list[dict]] = {
    "formal_sciences_arithmetic_fundamentals": [
        {
            "title": "Arithmetic and Fundamentals - Field Overview",
            "content": """# Arithmetic and Fundamentals

## Definition
Arithmetic and mathematical fundamentals cover the basic number systems, operations, and properties that underlie all of mathematics.

## Core Areas
- Number systems: natural (N), integer (Z), rational (Q), real (R), complex (C)
- Operations: addition, subtraction, multiplication, division
- Properties: commutative, associative, distributive
- Order of operations: PEMDAS/BODMAS
- Factors, multiples, primes
- Exponents and logarithms
- Ratios, proportions, percentages
- Modular arithmetic

## Key Concepts
- Natural numbers: 1, 2, 3, ... (counting)
- Integers: ..., -2, -1, 0, 1, 2, ...
- Rational numbers: p/q where p, q are integers, q != 0
- Real numbers: all numbers on the number line
- Complex numbers: a + bi where i^2 = -1
- Prime: natural number > 1 with exactly two divisors
- GCD/LCM: greatest common divisor, least common multiple
- Fundamental Theorem of Arithmetic: every integer > 1 has unique prime factorization

## Foundational Texts
- Euclid, "Elements" (c. 300 BCE)
- G.H. Hardy, "A Mathematician's Apology"
- Courant & Robbins, "What is Mathematics?"

## Authority Note
Advisory. Arithmetic is established; fundamentals are settled mathematics.""",
            "tags": ["arithmetic", "numbers", "fundamentals", "overview"],
        }
    ],
    "formal_sciences_algebra": [
        {
            "title": "Algebra - Field Overview",
            "content": """# Algebra

## Definition
Algebra is the study of mathematical symbols and rules for manipulating them, generalizing arithmetic to work with variables and unknown quantities.

## Core Areas
- Elementary algebra: variables, equations, polynomials
- Linear algebra: vectors, matrices, linear equations, vector spaces
- Abstract algebra: groups, rings, fields, modules
- Commutative algebra: commutative rings
- Algebraic geometry: solutions of polynomial systems
- Algebraic number theory: algebraic structures in number theory

## Key Concepts
- Variable: symbol representing an unknown or changing quantity
- Equation: statement that two expressions are equal
- Polynomial: sum of terms with variables and coefficients
- Function: mapping from inputs to outputs
- Group: set with one operation (associative, identity, inverses)
- Ring: set with two operations (addition and multiplication)
- Field: ring where every nonzero element has a multiplicative inverse
- Vector space: set of vectors with addition and scalar multiplication

## Foundational Texts
- Birkhoff & Mac Lane, "A Survey of Modern Algebra"
- Dummit & Foote, "Abstract Algebra"
- Strang, "Introduction to Linear Algebra"
- Artin, "Algebra"

## Authority Note
Advisory. Algebra is established mathematics; theorems are proven.""",
            "tags": ["algebra", "equations", "groups", "rings", "fields", "overview"],
        }
    ],
    "formal_sciences_geometry": [
        {
            "title": "Geometry - Field Overview",
            "content": """# Geometry

## Definition
Geometry is the study of shape, size, position, and properties of space. It originated in land measurement and evolved into a rigorous mathematical discipline.

## Core Areas
- Euclidean geometry: flat space, points, lines, planes, angles
- Non-Euclidean: hyperbolic, elliptic (Riemannian)
- Differential geometry: curves, surfaces, manifolds
- Algebraic geometry: solutions of polynomial equations as geometric objects
- Topology: properties preserved under continuous deformation
- Computational geometry: algorithms for geometric problems
- Projective geometry: properties preserved under projection

## Key Concepts
- Point, line, plane: fundamental objects
- Angle: measure of rotation (degrees, radians)
- Triangle: 3-sided polygon; angles sum to 180 (Euclidean)
- Circle: set of points equidistant from center
- Congruence: same shape and size
- Similarity: same shape, possibly different size
- Symmetry: transformation preserving shape
- Manifold: space that locally resembles Euclidean space
- Curvature: measure of how much a curve/surface deviates from flat

## Foundational Texts
- Euclid, "Elements"
- Coxeter, "Introduction to Geometry"
- Do Carmo, "Differential Geometry of Curves and Surfaces"
- Hartshorne, "Geometry: Euclid and Beyond"

## Authority Note
Advisory. Geometry is established; theorems are proven.""",
            "tags": ["geometry", "Euclidean", "differential", "topology", "overview"],
        }
    ],
    "formal_sciences_trigonometry": [
        {
            "title": "Trigonometry - Field Overview",
            "content": """# Trigonometry

## Definition
Trigonometry studies relationships between side lengths and angles of triangles, and the trigonometric functions that generalize these relationships.

## Core Areas
- Right triangle trigonometry: sine, cosine, tangent
- Unit circle: definitions of trig functions for any angle
- Trigonometric identities: Pythagorean, sum/difference, double angle
- Inverse trig functions: arcsin, arccos, arctan
- Laws of sines and cosines: for non-right triangles
- Polar coordinates: alternative to Cartesian
- Trigonometric equations and graphs

## Key Functions
- sin(theta) = opposite/hypotenuse
- cos(theta) = adjacent/hypotenuse
- tan(theta) = opposite/adjacent = sin/cos
- csc = 1/sin, sec = 1/cos, cot = 1/tan
- Radians: 2*pi radians = 360 degrees

## Key Identities
- sin^2 + cos^2 = 1 (Pythagorean)
- sin(A+B) = sinA cosB + cosA sinB
- cos(A+B) = cosA cosB - sinA sinB
- sin(2A) = 2 sinA cosA
- cos(2A) = cos^2A - sin^2A

## Foundational Texts
- Gelfand & Saul, "Trigonometry"
- Axler, "Precalculus"
- Stewart, "Calculus: Early Transcendentals" (trig chapters)

## Authority Note
Advisory. Trigonometry is established mathematics.""",
            "tags": ["trigonometry", "sine", "cosine", "triangles", "overview"],
        }
    ],
}

FORMAL_K1_BATCH2: dict[str, list[dict]] = {
    "formal_sciences_calculus": [
        {
            "title": "Calculus - Field Overview",
            "content": """# Calculus

## Definition
Calculus is the mathematical study of continuous change, comprising differential calculus (rates of change) and integral calculus (accumulation).

## Core Areas
- Limits: value a function approaches
- Derivatives: instantaneous rate of change
- Integrals: area under curve, accumulation
- Differential equations: equations involving derivatives
- Sequences and series: infinite sums, convergence
- Multivariable calculus: functions of several variables
- Vector calculus: gradients, divergence, curl, line/surface integrals

## Key Concepts
- Limit: lim(x->a) f(x) = L
- Derivative: f'(x) = lim(h->0) [f(x+h)-f(x)]/h
- Integral: integral of f(x) dx = area under f
- Fundamental Theorem: differentiation and integration are inverse
- Chain rule: d/dx f(g(x)) = f'(g(x)) * g'(x)
- Product rule: (fg)' = f'g + fg'
- Taylor series: f(x) = sum f^(n)(a)/n! * (x-a)^n

## Foundational Texts
- Stewart, "Calculus: Early Transcendentals"
- Spivak, "Calculus"
- Apostol, "Calculus" (2 vols)
- Hughes-Hallett et al., "Calculus"

## Authority Note
Advisory. Calculus is established; theorems are proven.""",
            "tags": ["calculus", "derivatives", "integrals", "limits", "overview"],
        }
    ],
    "formal_sciences_mathematical_analysis": [
        {
            "title": "Mathematical Analysis - Field Overview",
            "content": """# Mathematical Analysis

## Definition
Mathematical analysis is the branch of mathematics dealing with limits and related theories: differentiation, integration, measure, infinite series, and analytic functions.

## Core Areas
- Real analysis: rigorous study of real-valued functions
- Complex analysis: functions of a complex variable
- Functional analysis: vector spaces of functions
- Measure theory: generalization of length, area, volume
- Harmonic analysis: Fourier series and transforms
- Differential equations: ordinary and partial
- Numerical analysis: approximate solutions

## Key Concepts
- Convergence: sequence approaches a limit
- Continuity: no jumps in function
- Differentiability: smooth, has derivative
- Integrability: can be integrated (Riemann, Lebesgue)
- Compactness: every open cover has finite subcover
- Completeness: every Cauchy sequence converges
- Uniform convergence: convergence independent of point
- Measure: assigns size to sets

## Foundational Texts
- Rudin, "Principles of Mathematical Analysis" (Baby Rudin)
- Rudin, "Real and Complex Analysis"
- Royden & Fitzpatrick, "Real Analysis"
- Stein & Shakarchi, "Princeton Lectures in Analysis" (4 vols)

## Authority Note
Advisory. Analysis is established; proofs are rigorous.""",
            "tags": ["analysis", "real analysis", "complex analysis", "limits", "overview"],
        }
    ],
    "formal_sciences_discrete_mathematics": [
        {
            "title": "Discrete Mathematics - Field Overview",
            "content": """# Discrete Mathematics

## Definition
Discrete mathematics studies mathematical structures that are discrete rather than continuous: finite or countable sets, graphs, combinatorial objects.

## Core Areas
- Set theory: sets, relations, functions
- Combinatorics: counting, arrangements, permutations
- Graph theory: vertices, edges, paths, trees
- Logic: propositional, predicate
- Number theory: integers, divisibility, primes
- Cryptography: discrete structures for security
- Algorithms: complexity, correctness

## Key Concepts
- Set: collection of distinct objects
- Permutation: ordered arrangement
- Combination: unordered selection
- Graph: vertices connected by edges
- Tree: connected acyclic graph
- Recurrence relation: sequence defined by previous terms
- Pigeonhole principle: if n items in m holes and n > m, some hole has >1
- Inclusion-exclusion: |A union B| = |A| + |B| - |A intersect B|

## Foundational Texts
- Rosen, "Discrete Mathematics and Its Applications"
- Graham, Knuth, Patashnik, "Concrete Mathematics"
- Diestel, "Graph Theory"
- Stanley, "Enumerative Combinatorics"

## Authority Note
Advisory. Discrete math is established; theorems are proven.""",
            "tags": ["discrete mathematics", "combinatorics", "graph theory", "sets", "overview"],
        }
    ],
    "formal_sciences_number_theory": [
        {
            "title": "Number Theory - Field Overview",
            "content": """# Number Theory

## Definition
Number theory is the study of integers and their properties, especially the relationships between them.

## Core Areas
- Elementary number theory: divisibility, primes, congruences
- Analytic number theory: using analysis (prime number theorem)
- Algebraic number theory: algebraic structures
- Computational number theory: algorithms
- Diophantine equations: integer solutions
- Additive number theory: partitions, Goldbach
- Probabilistic number theory: distribution of primes

## Key Concepts
- Prime: number > 1 with exactly two divisors
- Composite: non-prime > 1
- GCD: greatest common divisor
- Congruence: a = b (mod n) if n divides (a-b)
- Fundamental Theorem of Arithmetic: unique factorization
- Fermat's Little Theorem: a^(p-1) = 1 (mod p) for prime p
- Euler's theorem: a^phi(n) = 1 (mod n)
- Chinese Remainder Theorem: simultaneous congruences
- Quadratic reciprocity: relationship between Legendre symbols

## Open Problems
- Riemann Hypothesis: zeros of zeta function
- Goldbach Conjecture: every even > 2 is sum of two primes
- Twin Prime Conjecture: infinitely many primes p, p+2
- Collatz Conjecture: 3n+1 sequence reaches 1

## Foundational Texts
- Hardy & Wright, "An Introduction to the Theory of Numbers"
- Niven, Zuckerman, Montgomery, "An Introduction to the Theory of Numbers"
- Ireland & Rosen, "A Classical Introduction to Modern Number Theory"
- Apostol, "Introduction to Analytic Number Theory"

## Authority Note
Advisory. Number theory is established; theorems are proven. Open problems are clearly marked.""",
            "tags": ["number theory", "primes", "congruences", "Diophantine", "overview"],
        }
    ],
}

FORMAL_K1_BATCH3: dict[str, list[dict]] = {
    "formal_sciences_topology": [
        {
            "title": "Topology - Field Overview",
            "content": """# Topology

## Definition
Topology is the study of geometric properties preserved under continuous deformations: stretching, bending, but not tearing or gluing.

## Core Areas
- Point-set (general) topology: open/closed sets, continuity, compactness
- Algebraic topology: homotopy, homology, fundamental group
- Differential topology: smooth manifolds
- Geometric topology: knots, 3-manifolds, 4-manifolds
- Algebraic K-theory

## Key Concepts
- Topological space: set with collection of open sets
- Open/closed sets: defined by topology
- Continuous function: preimage of open is open
- Homeomorphism: bijective continuous with continuous inverse
- Compact: every open cover has finite subcover
- Connected: cannot be split into two open sets
- Homotopy: continuous deformation between maps
- Fundamental group: pi_1(X): loops modulo deformation
- Manifold: locally Euclidean space

## Foundational Texts
- Munkres, "Topology"
- Hatcher, "Algebraic Topology"
- Willard, "General Topology"
- Guillemin & Pollack, "Differential Topology"

## Authority Note
Advisory. Topology is established; theorems are proven.""",
            "tags": ["topology", "continuous", "manifold", "homotopy", "overview"],
        }
    ],
    "formal_sciences_logic": [
        {
            "title": "Logic - Field Overview",
            "content": """# Logic (Formal)

## Definition
Formal logic is the study of valid reasoning through formal systems: syntax, semantics, and inference rules.

## Core Areas
- Propositional logic: AND, OR, NOT, IMPLIES
- Predicate (first-order) logic: quantifiers, predicates
- Modal logic: necessity, possibility
- Intuitionistic logic: constructive reasoning
- Higher-order logic: quantify over predicates
- Set theory: ZFC
- Model theory: structures satisfying theories
- Proof theory: formal proofs
- Computability theory: what can be computed

## Key Concepts
- Valid: conclusion follows from premises
- Sound: valid + true premises
- Tautology: always true
- Satisfiable: true under some assignment
- Decidable: algorithm exists to determine truth
- Complete: all true statements are provable
- Consistent: no contradiction derivable
- Godel's incompleteness theorems: arithmetic cannot be both complete and consistent

## Foundational Texts
- Enderton, "A Mathematical Introduction to Logic"
- Mendelson, "Introduction to Mathematical Logic"
- Boolos, Burgess, Jeffrey, "Computability and Logic"
- Hodges, "Model Theory"

## Authority Note
Advisory. Formal logic is established; theorems are proven.""",
            "tags": ["logic", "propositional", "predicate", "Godel", "overview"],
        }
    ],
    "formal_sciences_probability": [
        {
            "title": "Probability - Field Overview",
            "content": """# Probability

## Definition
Probability is the mathematical study of uncertainty and randomness, quantifying the likelihood of events.

## Core Areas
- Probability theory: axioms, distributions
- Random variables: discrete, continuous
- Joint and conditional probability
- Expectation, variance, moments
- Limit theorems: law of large numbers, central limit theorem
- Stochastic processes: Markov chains, Brownian motion
- Bayesian probability: updating beliefs

## Key Concepts
- Sample space: set of all outcomes
- Event: subset of sample space
- Probability axioms (Kolmogorov):
  1. P(A) >= 0
  2. P(Omega) = 1
  3. P(union of disjoint) = sum of P
- Conditional probability: P(A|B) = P(A and B) / P(B)
- Independence: P(A and B) = P(A) * P(B)
- Bayes' theorem: P(H|E) = P(E|H) * P(H) / P(E)
- Expected value: E[X] = sum x * P(X=x)
- Variance: Var(X) = E[(X - E[X])^2]

## Common Distributions
- Discrete: Bernoulli, Binomial, Geometric, Poisson
- Continuous: Uniform, Normal, Exponential, Beta, Gamma

## Foundational Texts
- Feller, "An Introduction to Probability Theory and Its Applications"
- Ross, "A First Course in Probability"
- Grimmett & Stirzaker, "Probability and Random Processes"
- Williams, "Probability with Martingales"

## Authority Note
Advisory. Probability theory is established; theorems are proven.""",
            "tags": ["probability", "random variables", "Bayes", "distributions", "overview"],
        }
    ],
}

FORMAL_K1_BATCH4: dict[str, list[dict]] = {
    "formal_sciences_statistics": [
        {
            "title": "Statistics - Field Overview",
            "content": """# Statistics

## Definition
Statistics is the science of collecting, analyzing, interpreting, and presenting data. It provides methods for inference from samples to populations.

## Core Areas
- Descriptive statistics: summarize data (mean, median, variance)
- Inferential statistics: estimate, test hypotheses
- Estimation: point, interval (confidence intervals)
- Hypothesis testing: null, alternative, p-values
- Regression: linear, logistic, nonlinear
- Bayesian statistics: prior, likelihood, posterior
- Nonparametric statistics: distribution-free methods
- Multivariate statistics: PCA, factor analysis, clustering

## Key Concepts
- Population: entire group of interest
- Sample: subset of population
- Parameter: population characteristic (usually unknown)
- Statistic: sample-based estimate
- Sampling distribution: distribution of a statistic
- Central Limit Theorem: sample means ~ Normal
- Confidence interval: range likely to contain parameter
- p-value: probability of data under null hypothesis
- Type I error: false positive (reject true null)
- Type II error: false negative (fail to reject false null)

## Foundational Texts
- Casella & Berger, "Statistical Inference"
- Wasserman, "All of Statistics"
- Hogg, McKean, Craig, "Introduction to Mathematical Statistics"
- Gelman et al., "Bayesian Data Analysis"

## Authority Note
Advisory. Statistical methods are established; correct application requires care.""",
            "tags": ["statistics", "inference", "hypothesis testing", "regression", "overview"],
        }
    ],
    "formal_sciences_optimization": [
        {
            "title": "Optimization - Field Overview",
            "content": """# Optimization

## Definition
Optimization is the mathematical study of finding the best solution from a set of alternatives: minimizing or maximizing an objective subject to constraints.

## Core Areas
- Linear programming: linear objective and constraints
- Nonlinear programming: nonlinear objectives/constraints
- Convex optimization: convex objective and feasible set
- Integer programming: integer-valued variables
- Combinatorial optimization: discrete structures
- Stochastic optimization: uncertainty in data
- Multi-objective optimization: trade-offs

## Key Concepts
- Objective function: f(x) to minimize or maximize
- Decision variables: x
- Constraints: g(x) <= 0, h(x) = 0
- Feasible region: set of x satisfying constraints
- Optimal solution: x* minimizing/maximizing f
- Local vs global optimum
- Duality: primal and dual problems
- KKT conditions: necessary conditions for optimality
- Gradient descent: iterative optimization

## Foundational Texts
- Boyd & Vandenberghe, "Convex Optimization"
- Nocedal & Wright, "Numerical Optimization"
- Bertsimas & Tsitsiklis, "Introduction to Linear Optimization"
- Luenberger & Ye, "Linear and Nonlinear Programming"

## Authority Note
Advisory. Optimization theory is established; algorithms are well-studied.""",
            "tags": ["optimization", "linear programming", "convex", "constraints", "overview"],
        }
    ],
    "formal_sciences_numerical_methods": [
        {
            "title": "Numerical Methods - Field Overview",
            "content": """# Numerical Methods

## Definition
Numerical methods are algorithms for approximating solutions to mathematical problems that cannot be solved exactly, using finite-precision arithmetic.

## Core Areas
- Numerical linear algebra: solving Ax=b, eigenvalues
- Numerical integration: quadrature rules
- Numerical differentiation: finite differences
- Root finding: bisection, Newton's method
- Interpolation and extrapolation
- Ordinary differential equations: Euler, Runge-Kutta
- Partial differential equations: finite difference, finite element
- Optimization: gradient descent, Newton's method

## Key Concepts
- Floating-point arithmetic: IEEE 754, roundoff error
- Truncation error: error from approximating infinite process
- Stability: small perturbations don't amplify
- Convergence: approximation approaches true solution
- Order of accuracy: how error decreases with step size
- Conditioning: sensitivity of solution to input perturbations
- Ill-conditioned: small input changes cause large output changes

## Foundational Texts
- Burden & Faires, "Numerical Analysis"
- Trefethen & Bau, "Numerical Linear Algebra"
- Quarteroni, Sacco, Saleri, "Numerical Mathematics"
- Heath, "Scientific Computing"

## Authority Note
Advisory. Numerical methods are established; implementation details matter for correctness.""",
            "tags": ["numerical methods", "approximation", "floating point", "algorithms", "overview"],
        }
    ],
}

FORMAL_K1_BATCH5: dict[str, list[dict]] = {
    "formal_sciences_computational_science": [
        {
            "title": "Computational Science - Field Overview",
            "content": """# Computational Science

## Definition
Computational science uses computational methods to solve scientific problems: simulation, modeling, and data analysis across physics, chemistry, biology, and engineering.

## Core Areas
- Computational physics: simulations of physical systems
- Computational chemistry: molecular modeling, quantum chemistry
- Computational biology: protein folding, genomics
- Scientific computing: high-performance numerical computation
- Simulation: discrete event, continuous, agent-based
- Visualization: scientific data representation
- Parallel computing: MPI, OpenMP, GPU

## Key Concepts
- Model: mathematical representation of system
- Simulation: running a model over time
- Discretization: converting continuous to discrete
- Mesh: grid for spatial discretization
- Time step: temporal discretization
- Verification: solving equations right
- Validation: solving right equations
- Uncertainty quantification: error propagation

## Foundational Texts
- Heath, "Scientific Computing"
- Golub & Van Loan, "Matrix Computations"
- LeVeque, "Finite Difference Methods for Ordinary and Partial Differential Equations"
- Landau, Paez, Bordeianu, "Computational Physics"

## Authority Note
Advisory. Computational science methods are established; results require verification and validation.""",
            "tags": ["computational science", "simulation", "modeling", "HPC", "overview"],
        }
    ],
    "formal_sciences_operations_research": [
        {
            "title": "Operations Research - Field Overview",
            "content": """# Operations Research

## Definition
Operations research (OR) is the application of mathematical methods to decision-making: optimizing operations, allocating resources, and managing systems.

## Core Areas
- Linear programming: simplex method, duality
- Integer programming: branch and bound
- Network optimization: shortest path, max flow, min cost
- Queueing theory: waiting lines
- Inventory theory: stock management
- Game theory: strategic decision-making
- Markov decision processes: sequential decisions
- Simulation: Monte Carlo, discrete event

## Key Concepts
- Decision variable: quantity to choose
- Objective: minimize cost or maximize profit
- Constraints: limitations on resources
- Optimal solution: best feasible decision
- Sensitivity analysis: how solution changes with inputs
- Duality: primal-dual relationship
- Shadow price: value of additional resource

## Foundational Texts
- Hillier & Lieberman, "Introduction to Operations Research"
- Taha, "Operations Research: An Introduction"
- Winston, "Operations Research: Applications and Algorithms"
- Bertsimas & Tsitsiklis, "Introduction to Linear Optimization"

## Authority Note
Advisory. OR methods are established; applications require domain knowledge.""",
            "tags": ["operations research", "linear programming", "optimization", "queueing", "overview"],
        }
    ],
    "formal_sciences_theoretical_computer_science": [
        {
            "title": "Theoretical Computer Science - Field Overview",
            "content": """# Theoretical Computer Science

## Definition
Theoretical computer science is the mathematical study of computation: what can be computed, how efficiently, and what problems are inherently hard.

## Core Areas
- Computability theory: what is computable (Turing machines)
- Complexity theory: P, NP, PSPACE, EXPTIME
- Algorithms: design and analysis
- Data structures: efficient storage and retrieval
- Automata theory: finite automata, pushdown, Turing
- Formal languages: regular, context-free, context-sensitive
- Cryptography: computational hardness assumptions
- Randomized algorithms: probabilistic methods
- Quantum computing: quantum algorithms

## Key Concepts
- Turing machine: abstract model of computation
- Church-Turing thesis: Turing-computable = effectively computable
- Halting problem: undecidable
- P: polynomial time solvable
- NP: polynomial time verifiable
- NP-complete: hardest in NP (SAT, TSP, etc.)
- P vs NP: open problem (one of Millennium Prize)
- Reduction: transform one problem to another
- Big-O notation: asymptotic complexity

## Complexity Classes
- P: solvable in polynomial time
- NP: verifiable in polynomial time
- PSPACE: polynomial space
- EXPTIME: exponential time
- BPP: bounded-error probabilistic polynomial time
- BQP: bounded-error quantum polynomial time

## Foundational Texts
- Sipser, "Introduction to the Theory of Computation"
- CLRS, "Introduction to Algorithms"
- Arora & Barak, "Computational Complexity: A Modern Approach"
- Hopcroft, Motwani, Ullman, "Introduction to Automata Theory"

## Authority Note
Advisory. TCS is established; theorems are proven. P vs NP remains open.""",
            "tags": ["theoretical computer science", "complexity", "algorithms", "Turing", "overview"],
        }
    ],
}
