"""Compile only two isolated classes for an acceptance ablation; mainline untouched."""
from run_long_budget_bridge import ROOT, read, rows, write_once, execute
from pa_capability_support import run_case, SOURCE, initial_key
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes

INTERFACE = ROOT / "runs/pa-capability-interfaces-20261105-175043-036508"
POLICY_AUDIT = ROOT / "runs/pa-role-policy-audit-20261105-212142-589056"
PROPERTY = "research.pa.blockSpecialistBridge"


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Frozen hook not unique: " + old[:70])
    return text.replace(old, new)


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir(); classes.mkdir()
    base = (INTERFACE / "classpath.txt").read_text("utf-8-sig").strip()
    population = (INTERFACE / "source/PaPopulation.java").read_text("utf-8-sig")
    population = replace_once(population, "    private static boolean accepts(", "    private boolean accepts(")
    population = replace_once(population, "    private boolean accepts(",
        "    private static final boolean BLOCK_BRIDGE = Boolean.getBoolean(\"" + PROPERTY + "\");\n"
        "    public long specialistOnlyAcceptanceCandidates, blockedSpecialistOnly;\n\n    private boolean accepts(")
    original = """        return parent.role == Direction.CENTER ? PaInternalArchive.weaklyDominates(a, b) || !flags.dominated
                : a[parent.role.objective()] < b[parent.role.objective()];"""
    revised = """        boolean center = PaInternalArchive.weaklyDominates(a, b) || !flags.dominated;
        if (parent.role == Direction.CENTER) return center;
        boolean own = a[parent.role.objective()] < b[parent.role.objective()];
        if (own && !center) {
            specialistOnlyAcceptanceCandidates++;
            if (BLOCK_BRIDGE) { blockedSpecialistOnly++; return false; }
        }
        return own;"""
    population = replace_once(population, original, revised)
    (source / "PaPopulation.java").write_text(population, encoding="utf-8")
    search = (INTERFACE / "source/PaCapabilitySearch.java").read_text("utf-8-sig")
    search = replace_once(search,
        '        if(population!=null)result.put("completeGenerations",population.completedGenerations); return result;',
        '        if(population!=null) { result.put("completeGenerations",population.completedGenerations);\n'
        '            result.put("specialistOnlyAcceptanceCandidates",population.specialistOnlyAcceptanceCandidates);\n'
        '            result.put("blockedSpecialistOnly",population.blockedSpecialistOnly);\n'
        '            result.put("blockSpecialistBridge",Boolean.getBoolean("' + PROPERTY + '")); } return result;')
    (source / "PaCapabilitySearch.java").write_text(search, encoding="utf-8")
    execute(["java", "-version"], root / "jdk-version.log")
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base, "-d", str(classes),
             *map(str, source.glob("*.java"))], root / "compile.log")
    cp = str(classes) + ";" + base
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write_once(root / "class-hashes.json", class_hashes(classes))
    write_once(root / "java-source-hashes.json", {p.name: digest(p) for p in source.glob("*.java")})
    return cp


def engineering(root, cp, plan, completed):
    expected = {r["stem"]: r for r in read(INTERFACE / "analysis.json")["equivalence"]}
    policies = {r["stem"]: r for r in read(POLICY_AUDIT / "analysis.json")["instances"]}
    results = []
    for spec in plan["instances"]:
        stem, limit = spec["stem"], spec["feLimit"]
        source = SOURCE / stem / "11730007/sources.tsv"
        off, receipt = run_case(root, cp, stem, "PA_JOINT", "ENGINEERING-OFF", limit, 13630003,
            audit=True, source_tsv=source, vm_settings={PROPERTY: "false"})
        completed.append((off, receipt))
        prior, = rows(INTERFACE / stem / "PARITY/run-receipt.jsonl")
        assert receipt["paidSHA256"] == expected[stem]["paidSHA256"] == prior["paidSHA256"]
        want = sum(r.get("specialistOnlyAccept", 0) for r in policies[stem]["policyComparisons"].values())
        assert receipt["search"]["specialistOnlyAcceptanceCandidates"] == want
        assert receipt["search"]["blockedSpecialistOnly"] == 0
        old_front = {tuple(r["objectives"]) for r in rows(INTERFACE / stem / "PARITY/checkpoint-solutions.jsonl")
                     if r["checkpointKind"] == "FE" and r["checkpoint"] == limit}
        new_front = {tuple(r["objectives"]) for r in rows(off / "checkpoint-solutions.jsonl")
                     if r["checkpointKind"] == "FE" and r["checkpoint"] == limit}
        assert old_front == new_front and receipt["search"]["completeGenerations"] == 2
        on, changed = run_case(root, cp, stem, "PA_JOINT", "ENGINEERING-BLOCKED", limit, 13630003,
            source_tsv=source, vm_settings={PROPERTY: "true"})
        completed.append((on, changed))
        assert initial_key(off) == initial_key(on)
        assert changed["search"]["blockedSpecialistOnly"] > 0
        assert changed["search"]["blockedSpecialistOnly"] == changed["search"]["specialistOnlyAcceptanceCandidates"]
        assert changed["search"]["completeGenerations"] == 2
        results.append({"stem": stem, "offPaidSHA256": receipt["paidSHA256"],
            "frozenPaidSequenceAndFinalFrontEqual": True, "offSpecialistOnlyCandidates": want,
            "blockedCandidates": changed["search"]["blockedSpecialistOnly"], "commonInitialEqual": True})
    write_once(root / "engineering.json", {"passed": True, "instances": results})
