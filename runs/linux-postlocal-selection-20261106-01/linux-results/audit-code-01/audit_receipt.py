"""Reconcile successful, failed and truncated native evidence with saved receipts."""
import math

from audit_core import read_json, require, same_front
from audit_replay import same_members


def check_receipt(replay):
    receipt, folder = replay.receipt, replay.folder
    total = len(replay.paid)
    require(receipt["passFE"] == replay.B and receipt["expectedFE"] == 3 * replay.B and
            receipt["successful"] == total == replay.local and
            receipt["attempted"] == total + receipt["failed"], "Overall paid accounting differs")
    require(total == 0 or replay.last_detail["fe"] == total, "Final successful FE has no complete raw detail")
    require(receipt["paidSHA256"] == replay.digest.hexdigest(), "Full paid stream SHA256 differs")
    for fee, digest in receipt["paidPrefixes"].items():
        require(replay.prefixes.get(fee) == digest, "Paid prefix SHA256 differs at " + fee)
    require(receipt["prefix2BSHA256"] == replay.prefixes.get(str(2 * replay.B)), "Two-pass SHA256 differs")
    require(math.isfinite(receipt["searchSeconds"]) and receipt["searchSeconds"] > 0, "Invalid search duration")
    require(sum(p["successful"] for p in replay.pass_records) == total and
            sum(p["attempted"] for p in replay.pass_records) == receipt["attempted"] and
            sum(p["failed"] for p in replay.pass_records) == receipt["failed"], "Pass/overall fee reconciliation failed")
    complete = verify_termination(replay)
    details = receipt["probe"]
    require(details == read_json(folder / "probe.json"), "Saved probe receipt differs")
    require(details["passes"] == read_json(folder / "passes.json") == replay.pass_records,
            "Saved pass receipts differ from full timeline")
    require(details["selectionComplete"] is (replay.selected is not None) and
            details["finalPopulationComplete"] is complete, "Final readiness flags differ")
    require(details["evidence"] == dict(events=replay.sequence, validatedViews=replay.views),
            "Evidence or neutral-view counters differ")
    replay.check_native(details["native"])
    check_result(replay, details)
    physics = receipt["physicsQA"]["fullTimelineChecks"]
    require(physics in (0, total), "Physics QA covered only part of a paid timeline")
    require(receipt["importQA"]["fullDecodes"] in (0, 200), "Partial imported-objective QA")
    return dict(passed=True, mode=replay.mode, sourceSeed=receipt["sourceSeed"], passFE=replay.B,
                attemptedFE=receipt["attempted"], successfulFE=total, failedFE=receipt["failed"],
                feLimit=receipt["feLimit"], failAt=receipt["failAt"], complete=complete,
                nativeObserver=receipt["nativeObserver"], paidSHA256=replay.digest.hexdigest(),
                paidPrefixes=replay.prefixes, prefix2BSHA256=replay.prefixes.get(str(2 * replay.B)),
                proposalPrefixes=replay.proposal_prefixes,
                passes=replay.pass_checks, modelChecks=replay.model_results,
                views=replay.views, completePrograms=replay.programs, completePasses=replay.completed,
                selection=replay.selection_checks, publicArchiveSize=len(replay.public.points),
                nativeMixingLiveDonorsAndFourRoleAcceptance=True, allPaidArchiveIncludesUnselected=True,
                privatePolishArchivesIndependentA0=True, noFutureSourceState=True,
                physicalObjectivesIndependentlyDecoded=False, existingTimelinePhysicsQACount=physics,
                existingImportFullQACount=receipt["importQA"]["fullDecodes"],
                newSearchFE=0, newDecoderCalls=0, performanceProved=False)


def verify_termination(replay):
    receipt, total = replay.receipt, len(replay.paid)
    if receipt["failAt"] > 0:
        require(receipt["failAt"] == 2 and receipt["attempted"] == 2 and total == receipt["failed"] == 1,
                "Injected-failure accounting differs")
        require(receipt["stopReason"] == "FAILED" and "EXPECTED_PAID_FAILURE" in receipt["error"],
                "Expected injected failure was not retained")
        require(replay.current.pending is not None and replay.current.pending["beforePaid"] == total,
                "Injected failure lost its unpaid pending proposal")
        return False
    require(receipt["failed"] == 0 and receipt["error"] is None and total == receipt["feLimit"],
            "Unexpected failed, incomplete or wrong-budget execution")
    complete = total == 3 * replay.B
    require(receipt["stopReason"] == ("ALGORITHM_RETURNED" if complete else "FE_LIMIT"),
            "Stop reason differs from completion/cutoff")
    require(replay.completed == total // replay.B and
            (not complete or len(replay.pass_records) == 3), "Wrong number of completed passes")
    return complete


def check_result(replay, details):
    all_paid = details["allPaid"]
    require(all_paid["successfulObserved"] == len(replay.paid) and all_paid["importedAlreadyPaid"] == 200 and
            all_paid["nativeObserver"] == replay.receipt["nativeObserver"], "Observer accounting differs")
    same_front(read_json(replay.folder / "front.json"), replay.public.points, "Saved final public frontier")
    same_front(all_paid["publicArchive"], replay.public.points, "Receipt public frontier")
    same_front(all_paid["lastInternalArchive"], replay.private.points, "Receipt last private frontier")
    require(replay.current is not None, "No started pass evidence")
    expected = replay.current.output_members()
    same_members(read_json(replay.folder / "after.json"), expected, "Saved final working population")
