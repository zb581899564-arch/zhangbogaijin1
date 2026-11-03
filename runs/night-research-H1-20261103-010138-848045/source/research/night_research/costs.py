"""Additional evidence costs are reported separately, never double-charged as search FE."""
from .mechanism_tables import transfer_counters


def context_counters(run):
    return run["summary"].get("cooperation", {}).get("contextRenewal", {})


def append_evidence_costs(runs, rows):
    by_owner = {(r["instance"], r["seed"], r["variant"]): r for r in runs}
    for row in rows:
        run = by_owner[row["instance"], row["seed"], row["variant"]]
        evidence, context, transfer = run["checkpointEvidence"], context_counters(run), transfer_counters(run)
        row.update({"offlineCheckpointValidationDecodes": evidence["uniqueOfflineDecodes"],
            "checkpointCoveredPoints": evidence["coveredPoints"],
            "checkpointSearchCaptureSeconds": evidence["searchCaptureSeconds"],
            "offlineCheckpointValidationSeconds": evidence["offlineValidationSeconds"],
            "checkpointLateAdmissionsExcluded": evidence["lateAdmissionsExcluded"],
            "contextRenewalMode": context.get("mode"),
            "contextRenewalEventsStarted": context.get("eventsStarted", 0),
            "contextRenewalEventsCompleted": context.get("eventsCompleted", 0),
            "contextRenewalPaidResetFEIncludedInSearchFE": context.get("paidResetEvaluations", 0),
            "contextRenewalPendingResetEvaluations": context.get("pendingResetEvaluations", 0),
            "factoryTransferMode": transfer.get("mode"),
            "factoryTransferScheduledAttempts": transfer.get("scheduledAttempts", 0),
            "factoryTransferPaidFEIncludedInSearchFE": transfer.get("paidTransfers", 0),
            "factoryTransferDeadlineValidPaidFE": transfer.get("deadlineValidPaidTransfers", 0),
            "factoryTransferSourceRandomDraws": transfer.get("sourceRandomDraws", 0),
            "factoryTransferPending": transfer.get("pendingTransfers", 0)})


def evidence_totals(runs):
    return {"offlineCheckpointValidationDecodes": sum(r["checkpointEvidence"]["uniqueOfflineDecodes"] for r in runs),
        "checkpointCoveredPoints": sum(r["checkpointEvidence"]["coveredPoints"] for r in runs),
        "checkpointSearchCaptureSecondsIncludedInT": sum(r["checkpointEvidence"]["searchCaptureSeconds"] for r in runs),
        "offlineCheckpointValidationSeconds": sum(r["checkpointEvidence"]["offlineValidationSeconds"] for r in runs),
        "contextResetFEIncludedInSuccessfulFE": sum(context_counters(r).get("paidResetEvaluations", 0) for r in runs),
        "contextRenewalPartialOwners": sum(context_counters(r).get("pendingResetEvaluations", 0) > 0 for r in runs),
        "factoryTransferPaidFEIncludedInSuccessfulFE": sum(transfer_counters(r).get("paidTransfers", 0) for r in runs),
        "factoryTransferDeadlineValidPaidFE": sum(transfer_counters(r).get("deadlineValidPaidTransfers", 0) for r in runs),
        "factoryTransferPendingOwners": sum(transfer_counters(r).get("pendingTransfers", 0) > 0 for r in runs)}
