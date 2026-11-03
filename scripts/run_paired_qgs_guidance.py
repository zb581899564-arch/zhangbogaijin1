"""Static QGS vs uniform guidance with an identical per-visit local FE/factory schedule."""
import csv
from datetime import datetime
import difflib
from pathlib import Path
import shutil
import time

import numpy as np

from run_long_budget_bridge import (
    FROZEN, ROOT, SEED, STEM, controller_lock, execute, hypervolume, igd_plus,
    nondominated, objectives, read, rows, run_one, verify_frozen, write_once,
)

BRIDGE = ROOT / "runs/long-budget-bridge-20261103-082221-744929"
ANCHOR = ROOT / "runs/static-qgs-paper-ls-audit-20261103-171052-582206"
POINTS = (100, 5100, 15000, 50000, 100000, 250000, 500000)
ORDER = ("allocation-record", "Q-guided", "uniform-actions")
STAGES = ("initialization", "global", "inter", "intra")


def replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Expected exactly one frozen patch anchor: " + old[:120])
    return source.replace(old, new)


def adapt_qgs(source):
    source = replace(source, "int action = table.choose(observation, config.exploration);",
                     "int action = QgsLocalLedger.choose(table, observation, config.exploration);")
    old = '                    offspring.add(local.improve(particle, preference, reference));'
    return replace(source, old, "                    guarded.checkpoint();\n" + old)


def adapt_local(source):
    source = replace(source, "    private final IntraNeighborhoods neighborhoods;",
                     "    private final IntraNeighborhoods neighborhoods;\n"
                     "    private final QgsLocalLedger ledger = QgsLocalLedger.instance();")
    source = replace(source, "        return particle.descend(inter(particle.current, direction, reference));", """
        QgsLocalLedger.Slot slot = ledger.inter(direction.id());
        try { return particle.descend(inter(particle.current, direction, reference, slot)); }
        finally { ledger.end(slot); }""".lstrip("\n"))
    source = replace(source, "for (int round = 0; round < config.localProposalCap; round++)",
                     "for (int round = 0; round < config.localProposalCap && ledger.hasRound(); round++)")
    source = replace(source, "                current = vns(current, factory, direction, reference);", """
                QgsLocalLedger.Slot slot = ledger.round(direction.id(), round, factory);
                int[] remaining = {slot.limit};
                try {
                    do {
                        current = vns(current, slot.factory, direction, reference, remaining);
                        if (slot.fixed && remaining[0] > 0) slot.restarts++;
                    } while (slot.fixed && remaining[0] > 0);
                } finally {
                    slot.paid = slot.limit - remaining[0];
                    ledger.end(slot);
                }""".lstrip("\n"))
    source = replace(source, """            List<PermutationSolution<Integer>> reference) {
        PermutationSolution<Integer> current = parent;
        int operator = 0;
        while (operator < 2) {""", """            List<PermutationSolution<Integer>> reference, QgsLocalLedger.Slot slot) {
        PermutationSolution<Integer> current = parent;
        int operator = 0;
        while (slot.paid < slot.limit && (operator < 2 || slot.fixed)) {
            if (operator == 2) { operator = 0; slot.restarts++; }""")
    source = replace(source, '            state.evaluate(child, "inter", direction);',
                     '            state.evaluate(child, "inter", direction);\n            slot.paid++;')
    source = replace(source, """            Direction direction, List<PermutationSolution<Integer>> reference) {
        PermutationSolution<Integer> incumbent = parent;
        int operator = 0;
        int[] remaining = {chapter == 4 ? Integer.MAX_VALUE : config.localProposalCap};""",
        """            Direction direction, List<PermutationSolution<Integer>> reference) {
        return vns(parent, factory, direction, reference, new int[] {config.localProposalCap});
    }
    private PermutationSolution<Integer> vns(PermutationSolution<Integer> parent, int factory,
            Direction direction, List<PermutationSolution<Integer>> reference, int[] remaining) {
        PermutationSolution<Integer> incumbent = parent;
        int operator = 0;""")
    return replace(source, """        remaining[0]--;
        state.count("intra.neighborhood" + operator + ".proposals");
        return state.evaluate(neighborhoods.propose(parent, factory, operator), "intra", direction);""",
        """        state.count("intra.neighborhood" + operator + ".proposals");
        PermutationSolution<Integer> evaluated = state.evaluate(neighborhoods.propose(parent, factory, operator), "intra", direction);
        remaining[0]--;
        return evaluated;""")


def adapt_entry(source):
    source = replace(source, "        EDHHFSPW source = load(input, setup);", """
        if (!useStatic || !mode.equals("BASELINE")) throw new IllegalArgumentException("Static audit only");
        List<String> options = Files.readAllLines(input.getParent().resolve("paired-audit.txt"), StandardCharsets.UTF_8);
        System.setProperty("research.qgsAudit.mode", options.get(0));
        System.setProperty("research.qgsAudit.guidance", options.get(1));
        System.setProperty("research.qgsAudit.ledger", options.get(2));
        EDHHFSPW source = load(input, setup);""".lstrip("\n"))
    begin = "        context.problem().setObserver((paid, seconds, changed, archive) -> {"
    end = "        try { context.run(search.algorithm); }"
    assert source.count(begin) == source.count(end) == 1
    return source[:source.index(begin)] + """        List<String> initial = new java.util.ArrayList<>();
        context.problem().setObserver(new org.uma.jmetal.util.research.runtime.EvaluationObserver() {
            @Override public void completed(long paid, double seconds, boolean changed,
                    org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive<?> archive) {
                recorder.completed(paid, seconds, changed, archive);
                if (java.util.Arrays.binarySearch(points, paid) >= 0)
                    System.out.println("CHECKPOINT FE=" + paid + " seconds=" + seconds);
            }
            @Override public void completedSolution(org.uma.jmetal.solution.Solution<?> s,
                    long paid, double seconds, boolean changed,
                    org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive<?> archive) {
                if (paid <= 100) {
                    PermutationSolution<?> p = (PermutationSolution<?>) s;
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("fe", paid); row.put("JS", p.getVariables()); row.put("FA", p.getVariablesid());
                    row.put("MA", p.getAttribute("machine")); row.put("WA", p.getVariablesworker());
                    row.put("objectives", p.getObjectives()); initial.add(DynamicJson.encode(row));
                }
                completed(paid, seconds, changed, archive);
            }
        });
""" + replace(source[source.index(end):],
              "        Map<String, Object> receipt = receipt(context, useStatic, mode, search);",
              """        org.uma.jmetal.util.research.search.QgsLocalLedger.finish(out);
        Files.write(out.resolve("initial-population.jsonl"), initial, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        Map<String, Object> receipt = receipt(context, useStatic, mode, search);""")


def build(root):
    cp = (BRIDGE / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    source, classes = root / "source", root / "classes"
    source.mkdir()
    classes.mkdir()
    items = [
        (FROZEN / "source/src/java/search/CanonicalHmopso.java", adapt_qgs),
        (ANCHOR / "source/LocalSearch.java", adapt_local),
        (BRIDGE / "source/LongBudgetRun.java", adapt_entry),
    ]
    files = []
    for path, adapt in items:
        old = path.read_text(encoding="utf-8")
        new = adapt(old)
        (source / path.name).write_text(new, encoding="utf-8")
        (source / (path.stem + ".diff")).write_text("".join(difflib.unified_diff(
            old.splitlines(True), new.splitlines(True), fromfile=str(path), tofile=path.name)), encoding="utf-8")
        files.append(str(source / path.name))
    helper = ROOT / "src/algorithms/diagnostics/QgsLocalLedger.java"
    files.append(shutil.copy2(helper, source / helper.name))
    shutil.copy2(Path(__file__), source / Path(__file__).name)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes), *files],
            root / "compile.log")
    return str(classes) + ";" + cp


def folder(root, label):
    return root / label / "trials/static/BASELINE"


def run(root, label, cp):
    work = root / label
    shutil.copytree(BRIDGE / "inputs", work / "inputs")
    config = ("record", "Q", "-") if label == ORDER[0] else (
        "replay", "Q" if label == ORDER[1] else "UNIFORM", str(folder(root, ORDER[0]) / "local-ledger.csv"))
    (work / "inputs/paired-audit.txt").write_text("\n".join(config) + "\n", encoding="utf-8")
    print("ARM", label, flush=True)
    return run_one(work, cp, "static", "BASELINE", POINTS)


def validate(root, runs):
    previous = rows(ANCHOR / "outerLS30/trials/static/BASELINE/anytime.jsonl")
    anchor = {p["fe"]: p for p in runs[ORDER[0]]["curve"]}
    assert all(objectives(p["front"]) == objectives(anchor[p["fe"]]["front"]) for p in previous)
    init = [(folder(root, label) / "initial-population.jsonl").read_bytes() for label in ORDER]
    assert len(init[0].splitlines()) == 100 and init[0] == init[1] == init[2]
    assert all(objectives(a["front"]) == objectives(b["front"])
               for a, b in zip(runs[ORDER[0]]["curve"], runs[ORDER[1]]["curve"]))
    reference_ledger = None
    totals = {}
    for label, trial in runs.items():
        with (folder(root, label) / "local-ledger.csv").open(encoding="utf-8", newline="") as f:
            full = list(csv.DictReader(f))
        ledger = [tuple(int(r[key]) for key in ("visit", "group", "round", "factory", "paid")) for r in full]
        if reference_ledger is None:
            reference_ledger = ledger
        assert ledger == reference_ledger
        c = trial["receipt"]["search"]
        stages = {stage: c[stage + ".evaluations"] for stage in STAGES}
        assert stages == dict(zip(STAGES, (100, 10000, 586, 489314)))
        assert sum(row[-1] for row in ledger if row[2] == -1) == stages["inter"]
        assert sum(row[-1] for row in ledger if row[2] >= 0) == stages["intra"]
        totals[label] = {"FE": stages, "visits": max(row[0] for row in ledger), "slots": len(ledger),
                         "quotaContinuations": sum(int(row["restarts"]) for row in full),
                         "completedOuterGenerations": c["generations.completed"],
                         "guideActionCounts": {str(a): sum(v for k, v in c.items() if k.endswith(".action" + str(a)))
                                               for a in range(3)},
                         "archiveReplays": trial["replays"], "searchSeconds": trial["receipt"]["searchSeconds"]}
    return totals


def compare(runs, norm):
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    front = lambda p: (np.asarray(p["front"]) - lower) / scale
    q, u = (runs[label]["curve"] for label in ORDER[1:])
    reference = nondominated(np.concatenate([front(q[-1]), front(u[-1])]))
    result = []
    for a, b in zip(q, u):
        fa, fb = front(a), front(b)
        hv_q, hv_u = (float(hypervolume(f, (1.5,) * 3)) for f in (fa, fb))
        result.append({"FE": a["fe"], "HV_Q": hv_q, "HV_UNIFORM": hv_u,
                       "Q_vs_uniform_pct": 100 * (hv_q / hv_u - 1),
                       "IGDplus_Q": float(igd_plus(fa, reference)), "IGDplus_UNIFORM": float(igd_plus(fb, reference)),
                       "sensitivityPct": {str(ref): 100 * (hypervolume(fa, (ref,) * 3) / hypervolume(fb, (ref,) * 3) - 1)
                                          for ref in (1.25, 2.0)}})
    return result


def main():
    root = ROOT / "runs" / datetime.now().strftime("paired-static-qgs-guidance-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("PAIRED_ROOT", root, flush=True)
    start = time.monotonic()
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            verify_frozen(FROZEN)
            norm = read(BRIDGE / "protocol.json")["normalization"]
            write_once(root / "protocol.json", {
                "instance": STEM, "seed": SEED, "FE": POINTS[-1], "checkpoints": list(POINTS),
                "common": "frozen static canonical-v1, S/O QGS, reconstructed SUT and standby, four groups",
                "actions": ["reuse previous gbest", "current-group best", "binary tournament in search archive"],
                "intervention": "Use Q-table epsilon-greedy or draw uniformly from exactly the same three actions",
                "order": list(ORDER), "allocationAnchor": str(ANCHOR), "normalization": norm,
                "allocation": "Extra record run must exactly replay prior QGS. Then freeze every local visit, round, factory and paid quota for both arms; repeat same neighborhood pass on natural early finish until slot credits are spent.",
                "scope": "Single seed; conditional on QGS-derived allocation; no production changes or new tuning",
            })
            cp = build(root)
            (root / "classpath.txt").write_text(cp, encoding="utf-8")
            trials = {label: run(root, label, cp) for label in ORDER}
            write_once(root / "validation.json", validate(root, trials))
            write_once(root / "comparison.json", compare(trials, norm))
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": str(error),
                                         "wallSeconds": time.monotonic() - start})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "pairedFE": 1000000,
                                     "allocationRecordFE": 500000, "wallSeconds": time.monotonic() - start})
    print("PAIRED_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
