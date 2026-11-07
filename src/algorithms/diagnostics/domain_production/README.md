# Finite-support domain production probe

This isolated probe tests whether production outside the initial five-member resource support
changes the result under unchanged role acceptance. It does not establish scientific novelty,
replace the main algorithm, or measure complete four-group algorithm performance.

The frozen context is request q0, with seed `sourceSeed XOR 0x37a9185bL`. Inputs, the original
P100 workspace, model construction, five family receivers, original FOS cursors, donor draws,
round-robin schedule, common paid archive A0, role acceptance, original factory pools, and
terminal shared selector reuse the request-production implementation. Each source is fixed;
no new request is selected based on a probe outcome.

| Arm | Proposal generation |
| --- | --- |
| `GOM` | Original `PaMixingMove`, using the original FOS mask and live family donor. |
| `LEGAL` | Jointly rebind two jobs in one factory to complete legal resource tuples and new priority keys. |
| `NOVEL` | Same draws as LEGAL; the first job's tuple comes from the complement of its frozen initial-five support. The second uses the complete legal domain. |

The word NOVEL names this finite-support treatment only. It does not mean that the generated
schedule is globally new or that the method is a novel algorithm. If the first job's complement
is empty, NOVEL uses the complete legal domain and records `noveltyUnavailable`.

The joint generator uses its own `java.util.Random(probeSeed XOR 0x4f2a91L)`, and never consumes
the original GOM random stream. It freezes each job's resource support after original workspace
preparation. Every legal resource tuple is obtained by enumerating all `FirstStageCatalog` IDs
in increasing order, restricted to the job's fixed factory; the domain is never inferred from
the observed support. Factories and per-factory job lists are ordered by numeric ID.

Every eligible joint proposal consumes the same seven random API calls in LEGAL and NOVEL:
`nextInt(eligibleFactories)`, `nextInt(n)`, `nextInt(n-1)`, then four `nextDouble()` calls for
first rank, second rank, first key, and second key. The second job's index skips the first index.
Rank selection uses `floor(rank * domainSize)`. The first NOVEL resource domain can differ in
size, without changing the random calls. Both selected jobs change resource and key together;
all other genes are preserved. `TypedScheduleGenome.of` validates the resulting genome, with
its original descending-job-ID priority tie rule. There is no repair or free resampling in
LEGAL/NOVEL. If no factory has at least two jobs, an explicitly recorded noop is evaluated
and charged; neither joint arm draws from its private RNG in that case.

Original role acceptance is used in all three arms: objective-specific strict improvement,
or the original CENTER weak-dominance/not-dominated-by-paid-history rule. Every successful
paid candidate enters the shared pool and the reporting archive before receiver acceptance,
including rejected, duplicate, and noop candidates. Request cap/eta affect only the unchanged
terminal shared selector. No new decoding is performed by domain construction or proposal
generation. Existing source-cache import QA and optional paid full-timeline QA remain separate.

## Invocation and evidence

`research.dynamic.DomainProductionRun INPUT SETUP FATIGUE OUT CONTEXT ARM SOURCE_SEED [0]`

- `research.domain.productionFE`: default 4095; use 511 for the old ROLE bridge or 63 for registered engineering checks.
- `research.domain.limit`: default `productionFE + 1`, valid range 1 through that total. A limit at or below productionFE cannot construct the terminal assembly.
- `research.domain.observer`: default true; false disables detailed paid/step evidence, preserving mandatory archive/pool notification and digest.
- Existing `research.pilot.physics`, `research.pilot.failAt`, and `research.ctxGom.prefixFE` retain their engineering meanings.

The final FE is a complete evaluation of the original pool-selected composition, or the
actual request parent fallback if a factory has no feasible record. It is included in the total,
including a duplicate selection. GOM with productionFE=511 preserves original before/models,
after/front, pool, assembly, and paid-digest semantics. Additional domain metadata consumes no
original random draws. Exact bridge equality still requires the Linux engineering check.

Outputs retain the request-production file names and add `domain.json`, containing the complete
catalog, per-factory legal domains and job lists, frozen per-job support/complement, eligible
factories, and the private RNG seed. Existing before/models/after/pool/assembly schemas remain
unchanged. Production records add these fields to both paid and step JSONL:

- `fosMask`: the original scheduled FOS subset; `mask`: the actual generation jobs.
- `resources`, `keys`: complete candidate typed genes; original parent/donor IDs and source FE remain present.
- `donorUsedForProposal`: true only for GOM. All arms still draw and record donorSlot on the common original schedule.
- `generation`: generator identity and, for LEGAL/NOVEL, factory, selected jobs, both ranks/keys/resource IDs, domain sizes, complement size, fallback availability, noop marker, and random API call count.

When no eligible factory exists, selected jobs are empty, factory is -1, rank/key fields are null,
and `randomDraws` is zero. GOM generation metadata identifies the unchanged original move.
Receipt generator counters count generated proposals, including a subsequently failed paid
attempt; successful FE and acceptance counts remain separate. Normal cutoff and injected
evaluation-failure paths preserve the paid prefix, current archive/pools, pending proposal,
receipt, and terminal-assembly status.

Only these new Java files implement the probe; old Request classes and the mainline are unchanged.
All compilation, decoding, bridge checks, independent candidate/acceptance audits, scientific
execution, and statistics are performed on Linux by the external controller.
