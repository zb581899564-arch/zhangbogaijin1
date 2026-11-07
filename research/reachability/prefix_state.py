"""Necessary information from an exact stage-zero prefix; later stages remain uncommitted."""
import math


def availability(prefix,factory,stage,kind,index):
    if prefix is None or stage!=0:return 0.
    return prefix['machineEnd' if kind=='M' else 'workerEnd'][factory][index]


def fatigue_floor(prefix,metadata,horizon,factory,worker):
    if prefix is None or horizon is None:return 0.
    stage=metadata['factories'][factory][0]
    # Work increases fatigue; even giving this worker every remaining instant for rest
    # cannot recover below this floor before a completion-time horizon.
    end=prefix['workerEnd'][factory][worker];h=prefix['workerFatigue'][factory][worker]
    return max(0.,max(0.,h-1e-10)*math.exp(-stage['mu'][worker]*max(0.,horizon-end))-1e-10)


def multiplier(prefix,metadata,horizon,factory,stage,worker):
    if stage!=0 or prefix is None or horizon is None:return 1.
    return 1.+metadata['factories'][factory][0]['beta'][worker]*fatigue_floor(prefix,metadata,horizon,factory,worker)
