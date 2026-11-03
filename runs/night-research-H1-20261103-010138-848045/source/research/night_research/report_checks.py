"""Synthetic H2 factorial and mechanism-report smoke check; no scheduling calls."""
from research.semantic_repair.evidence import read
from .protocol import ROOT, CLASSICS, make_protocol
from .metrics import comparisons
from .interactions import interactions
from .gate import admission
from .mechanism_tables import transfer_tables
from .transfer_checks import fixture
from .report import write_report


def run_report_check(folder):
    protocol = make_protocol(read(ROOT / "research/night_research/h2_packet_v1.json"))
    levels = {"ROLE_PACKET": 1.03, "ROLE_MOSAIC": 1.01, "RANDOM_PACKET": 1.01, "SPEA2_4V": 1.01}
    modes = {"ROLE_PACKET": "PACKET_ROLE", "ROLE_MOSAIC": "MOSAIC_ROLE",
        "RANDOM_PACKET": "PACKET_RANDOM", "RANDOM_MOSAIC": "MOSAIC_RANDOM"}
    records, runs = [], []
    for instance in protocol["instances"]:
        for seed in protocol["algorithm_seeds"]:
            for label in protocol["variants"]:
                value = levels.get(label, 1.)
                records.append({"instance": instance["stem"], "seed": seed, "variant": label,
                    "hv": {str(point): value for point in (1.25, 1.5, 2.)}, "hv_half": value,
                    "hv_fe15000": value, "igdplus": .1})
                if label in modes:
                    _, summary = fixture(modes[label])
                    runs.append({"instance": instance["stem"], "seed": seed, "variant": label, "summary": summary})
    effects, selected = comparisons(records, protocol)
    for label in modes:
        for control in ("SHARE_STATIC", "TAIL", *CLASSICS):
            assert label + "__vs__" + control in effects
    factorial = interactions(records, protocol)
    assert abs(factorial["packet_integrity_x_role_source_scoring"]["T"]["meanInteractionPercent"] - 1.) < 1e-12
    mechanisms = transfer_tables(runs)
    for method in mechanisms["methodSummary"]:
        assert method["owners"] == 30 and method["paidTransfers"] == 30
        assert method["instanceMeanLocalEncodingPreservedRate"] == int(method["mode"].startswith("PACKET"))
    audit = {"runs": 300, "fixedFEReached": 300, "returnedSolutionsReplayed": 300,
        "offlineCheckpointValidationDecodes": 300}
    output = folder / "h2-report"
    output.mkdir()
    write_report(output, protocol, effects, selected, admission(protocol, effects, selected), audit, factorial, mechanisms)
    report = (output / "report.md").read_text(encoding="utf-8")
    assert "本厂完整率" in report and "实际付费次数" in report and "其他厂不变由已验收Java见证" in report
    assert all(label in report for label in modes)
    return {"allFourVersionsVsAllClassicsAndControls": True, "onePercentFactorialRecovered": True,
        "actualPaidCountsAndPreservationRatesReported": True, "reportWrittenAndReadBack": True}
