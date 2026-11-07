# Request-conditioned production probe

This isolated probe changes production acceptance. It does not replace the main algorithm,
reuse the earlier `DEMAND` factory-routing mechanism, or measure full four-group algorithm performance.

Each context imports the mature pre-global P100 and the common post-global paid archive A0.
The original `GomWorkspace` and `GomDomainModels` build the same factory-block FOS from P100.
Only the prescribed fixed family's five original receivers produce candidates: M1/C2/E1/W1.
All arms use a common round-robin schedule, frozen model, original `PaMixingMove`, shuffled
FOS orders, and live donors from the same five-member family. The 511 production evaluations
are distributed 103/102/102/102/102 in original receiver order. A receiver reshuffles its
same FOS after reaching the end. This common schedule is a bounded conditional probe,
not a complete original sequential GOM pass.

| Arm | Production acceptance |
| --- | --- |
| `ROLE` | Original strict objective improvement; CENTER uses original weak-dominance or not-dominated-by-paid-history rule. |
| `REQUEST` | Lower actual-cap violation wins; exact equality uses original role acceptance. |
| `ORDINARY` | Lower actual-cap violation wins; exact equality requires strict improvement in E/energyScale + eta*W/wageScale for every receiver. |
| `SHUFFLED` | Same as REQUEST, with the next cyclic request's cap from the same source and fixed family. |

Violation is `sum_f max(C_f-cap,0)/cap`, with exact double comparisons. REQUEST and SHUFFLED
do not use eta during production. Each arm's final shared selector uses the actual request's
cap, eta, and scales, including SHUFFLED. The original `FactoryPool.offer`, `truncate`, and
`choose` implementations are called directly through a same-package helper. Every successful
paid candidate, including rejected and unused candidates, enters both the private paid archive
and the original retained factory pools before production acceptance.

Evaluation 512 constructs and completely evaluates the original selected composition.
If any factory has no feasible retained record, the already-paid actual request parent is
copied and evaluated again, with fallback recorded. A physically duplicate chosen composition
is also charged; this fixed-budget terminal probe deliberately retains the duplicate marker.
No assembly is constructed for cutoffs below 512. Imported QA reconstructions are never
offered to the algorithm's paid archive.

## Input and CLI

`research.dynamic.RequestProductionRun INPUT SETUP FATIGUE OUT CONTEXT ARM SOURCE_SEED [requestIndex]`

The probe seed is `sourceSeed XOR 0x37a9185bL XOR (requestIndex * 0x9e3779b9L)`.
One JVM runs one arm and one context. All TSVs are UTF-8, without headers:

- `points.tsv`: the existing ten columns `P, slot, paidByFE, role, family, objectivesCSV, JSCSV, FACSV, MACSV, WACSV`; exactly 100 ordered rows.
- `background.tsv`: common A0 objective triples, three tab-separated columns.
- `request.tsv`: one row `requestId, family, cap, eta, energyScale, wageScale, parentObjectivesCSV, JSCSV, FACSV, MACSV, WACSV`.
- `effective-request.tsv`: the same 11-column schema, always containing the next cyclic request. All four arms read both request files for identical import QA; only SHUFFLED uses this second request for acceptance.
- `pools.tsv`: `factory, paidFE, localObjectivesCSV, jobsCSV, machinesCSV, workersCSV`, preserving original retained-record order within each factory.

Import reconstructs 100 mature receiver schedules plus both request parents using complete
decodes and verifies their already-paid objective triples exactly. Every retained local record
is inserted into its source parent's compatible factory job set, completely decoded, and checked
against its source local objective triple. These extra decodes restore source caches and allow
construction of original immutable `FactoryRecord` objects; their count and time are separately
reported. The QA combination's whole objective is never treated as a free candidate.

Properties:

- `research.request.limit`: 1..512, default 512; engineering cutoff only.
- `research.request.observer`: default true; false disables detailed paid/step writing, while mandatory archive/pool notifications and digest remain active. Detailed record construction/append time is measured separately; final close and snapshot IO are excluded from these evidence timers. This probe makes no time-performance claim.
- `research.pilot.physics`: true enables original every-paid full-timeline QA, separately counted; this synchronous QA time is included in the run clock.
- `research.pilot.failAt`: inject a charged evaluator failure, for example 2.
- `research.ctxGom.prefixFE`: comma-separated digest checkpoints.

Outputs are `receipt.json`, `before.json`, `models.json`, `after.json`, `front.json`,
`paid.jsonl`, `steps.jsonl`, `assembly.json`, `initial-pools.json`, and `final-pools.json`.
Successful cutoff and evaluator-failure paths preserve the paid prefix, final private archive,
pool state, and pending proposal. Files use CREATE_NEW to protect prior evidence.

Compilation, decoding, source replay, probe execution, and statistics run on Linux only.
Source-capture authorization, snapshot/barrier compatibility, shuffle construction, engineering
gates, metrics, and scientific interpretation belong to the external controller/protocol.
