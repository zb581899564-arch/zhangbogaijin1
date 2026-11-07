# Classic 4V engineering handoff

Final verification: `ClassicChecks.log`, Java 8 target, JDK 17 compiler, JVM `-Xmx256m`.
This directory records mechanism/engineering checks only. It contains no performance calibration, quality comparison, algorithm ranking or scientific acceptance claim.

## API

- `org.uma.jmetal.util.research.classic.ClassicConfig(String mode, int settingIndex)`.
- `ClassicAlgorithm(Problem<PermutationSolution<Integer>> guarded, Instance in, ClassicConfig cfg, Runnable timeCheckpoint)`.
- Implements `Algorithm<List<PermutationSolution<Integer>>>`; exposes `diagnostics(): Map<String,Object>` and `configuration(): String`.
- Check entry: `org.uma.jmetal.util.research.classic.ClassicChecks`.
- `OrdinaryVns` is the public narrow facade in the existing `search` package.

## Primary sources checked online

1. Deb et al. (2002), DOI [10.1109/4235.996017](https://doi.org/10.1109/4235.996017), IEEE original text [mirror](https://dynamics.org/~altenber/UH_ICS/EC_REFS/MULTI_OBJ/DebPratapAgarwalMeyarivan.pdf), pp.184-186: nondominated fronts, normalized crowding, rank/crowding comparison and elitist union selection.
2. Zitzler, Laumanns and Thiele (2001), [ETH TIK 103](https://sop.tik.ee.ethz.ch/publicationlistfiles/zlt2001a.pdf), report pp.6-8, sections 3.1/3.2: strength, summed dominating strengths, nearest-neighbor density, archive fill and lexicographic distance truncation. The text does not prescribe physical objective units or a normalization rule.
3. Zhang and Li (2007), DOI [10.1109/TEVC.2007.892759](https://doi.org/10.1109/TEVC.2007.892759), IEEE original text [mirror](https://tiezhongyu2005.github.io/resources/popularization/MOEA-D_2007.pdf), pp.713-716: Tchebycheff decomposition, weight-space neighbors, paid offspring updates of the reference point and neighboring subproblem replacement.

## Explicit adaptations frozen before calibration

- Chapter 4, three minimization objectives and four positional vectors only.
- Shared variation: crossover probability .9; OX on JS, independent uniform inheritance of each FA/MA/WA gene after alignment by job identity; no crossover inherits the first parent's bindings. JS mutation tests each position for a swap; each resource vector independently tests each job for alternative-value resampling. Every probability is `min(1, mutationScale/jobs)`. Settings 0/1/2 have scales 1/.5/2 and otherwise identical rules. Resource resampling uses the current factory's local bounds. Common deterministic repair is immediately before each guarded evaluation.
- Population 100 for all methods, SPEA2 internal archive 100, and the independent external result archive remains owned by RunContext.
- NSGA-II retains rank/crowding from the evaluated parent+offspring union for the next tournament. Constant objective spans add no interior crowding; stable boundary/tie policy prevents NaNs. Tournament ties consume only SeededRandom.
- SPEA2 uses strict dominance and multiset strength/raw-fitness formulas. Density is `1/(sigma_k+2)` with `k=floor(sqrt(union size))`, counting other solutions and excluding self. Density and truncation share the same Euclidean metric after dividing by each objective's absolute initial-100 mean; a zero mean uses 1. The scale is frozen and never uses future populations. This is an explicit numerical unit adaptation, not a normalization rule attributed to TIK103.
- MOEA/D uses the same frozen initial-mean scale, 100 deterministic maximin directions from the H=30 simplex lattice including all three vertices, 20 weight neighbors including self, neighborhood probability .9, and at most two replacements per child. Zero weights use 1e-6. Initial ideal values and later minima come only from that run's paid solutions. The direction-count construction, scale choice, delta and replacement cap are registered adaptations, not claims about every original-2007 parameter setting. Weight construction uses no search RNG.
- NSGA2_VNS retains NSGA-II selection and invokes the same chapter-4 LocalSearch, support=null, Direction.CENTER, after each 50 successful global offspring. Its reference is the current NSGA population. `localProposalCap=30` has the existing intra-only meaning; inter proposals are additional paid work. It adds no QGS, Q learning, four-subgroup logic or shared candidate pool.
- Initialization uses guarded.createSolution. Every new global/local candidate uses repair then guarded.evaluate, and no free full decoding or algorithm-owned external result archive exists. Budget/time exceptions are not caught by the algorithms.

## Focused evidence

- Hand-computed NSGA fronts, normalized crowding, elitism, constant-span safety and retained union-front crowding.
- Hand-computed SPEA strength/raw/density, dominated archive fill and a truncation tie requiring the second neighbor distance; duplicate objectives do not strictly dominate.
- SPEA density/truncation invariant to positive independent objective-unit conversions; frozen scale arrays cannot be altered through a caller alias; zero-mean fallback checked.
- MOEA/D simplex, 100 distinct weights, three vertices, self-containing 20-neighbor lists, RNG independence, frozen scales, ideal update and Tchebycheff scalar values.
- Shared variation: 360 candidates across all mutation settings checked for complete JS permutations, nonempty factories and local MA/WA bounds; both parents unchanged. Fixed seed 4 with identity/reversed parents explicitly verifies job-bound resource inheritance under nontrivial OX order.
- Four methods each checked at FE limits 0,1,99,100,101,149,150,151,251,351. Actual decoder completions equal charged successful FE; initialization/global/inter/intra diagnostics account for all paid evaluations. FE=150/151 exercises VNS entry/partial local-search exhaustion.
- Every previously evaluated object is fingerprinted by four vectors and objectives and checked unchanged before later evaluations. Re-evaluating the same object is rejected by the fixture; result copies cannot mutate algorithm state.
- Complete external archive and diagnostics reproduce at seed 7319, 333 FE, separately for every method. Every returned archive solution is fully decoded offline and its objectives compared; this offline QA never feeds search or its budget.
- Expected decoder failure at attempt 102 propagates unchanged; 101 successes plus one charged failure. Actual .02-second wall-clock stops checked for all methods.
- Injected checkpoint failures during NSGA objective sorting, SPEA dominated-fill sorting and MOEA/D neighbor sorting propagate unchanged.

## Scope limits

No performance seed sweep, calibration choice, search-quality conclusion or expansion-screen experiment was run by this module task. Full dynamic-entry integration and final real-instance replay remain the coordinating agent's responsibility. The algorithms are disclosed discrete scheduling adaptations of standard selection/decomposition mechanisms; they do not claim reproduction of the original papers' benchmark scores.
