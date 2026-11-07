"""Read-only native fixtures, keeping the author's functions and source bytes unchanged."""
function native_mixer(f, seed; fi=:none, fos=:distance)
    Q.create_qgomea_mixer(f, 6, 4, fi, fos, 0.0, Q.UPGMA(), :ox, MersenneTwister(seed))
end

function synchronization_probe()
    calls, during = Ref(0), Ref(false)
    mixer = Ref{Any}(nothing)
    parents = Vector{Vector{Int}}()
    function f(positions)
        calls[] += 1
        if during[]
            @assert all(point.perm == expected for (point, expected) in zip(mixer[].population, parents))
        end
        -Float64(sum(abs.(positions .- collect(1:6))))
    end
    value = native_mixer(f, 7281)
    mixer[] = value
    for generation in 1:2
        empty!(parents)
        append!(parents, copy(point.perm) for point in value.population)
        during[] = true
        Q.step!(value)
        during[] = false
        @assert value.generations[] == generation
        @assert all(length(mask) < round(value.n/12*10) for mask in value.fos)
        @assert all(sort(point.perm) == collect(1:6) for point in value.population)
    end
    return calls[], maximum(length.(value.fos))
end

function equal_change_probe()
    for seed in 1:64
        calls = Ref(0)
        f(p) = (calls[] += 1; 0.0)
        mixer = native_mixer(f, seed)
        empty!(mixer.fos); push!(mixer.fos, [1,2,3])
        before = copy(mixer.population[1].perm)
        solution = Q.QGomeaSolution(copy(before), 0.0)
        returned = Q.edamixing(solution, mixer; shuffle_fos=false)
        if solution.perm != before
            @assert returned == (false, false)
            return true, seed, calls[]
        end
    end
    return false, -1, 0
end

function forced_probe()
    calls = Ref(0)
    f(p) = (calls[] += 1; -Float64(sum(abs.(p .- collect(1:6)))))
    mixer = native_mixer(f, 1187; fi=:original)
    empty!(mixer.fos); push!(mixer.fos, [1,2])
    elite = Q.QGomeaSolution(collect(1:6), f(collect(1:6)))
    mixer.best[] = elite
    parent = collect(6:-1:1)
    solution = Q.QGomeaSolution(copy(parent), f(parent))
    baseline = calls[]
    returned = Q.edamixing(solution, mixer; shuffle_fos=false, donor_fixed=mixer.best)
    @assert solution.fitness > f(parent)
    @assert returned[2] && solution.perm != parent
    # Last f(parent) above is a fixture-only validation call.
    return calls[] - baseline - 1
end

function raw_budget_probe()
    calls = Ref(0)
    rf(p) = (calls[] += 1; -Float64(sum(abs.(p .- collect(1:length(p))))))
    Q.optimize_qgomea(rf, 6, 100000.0, 4)
    @assert calls[] > 4
    return calls[]
end

function run_lifecycle_checks(path)
    Random.seed!(2026110602) # LCP also calls the global RNG; seed it explicitly for this fixture.
    actual = Q.reduction(Q.UPGMA(), 3, 2, 1, 2.0, 8.0)
    expected = (2*2.0 + 1*8.0)/3
    calls, largest = synchronization_probe()
    changed, seed, equal_calls = equal_change_probe()
    @assert changed
    forced_calls = forced_probe()
    budget_calls = raw_budget_probe()
    open(path, "w") do out
        println(out, "version\t", VERSION)
        println(out, "UPGMA_actual\t", actual)
        println(out, "UPGMA_expected\t", expected)
        println(out, "synchronousToyFunctionCalls\t", calls)
        println(out, "activeFOSLargestForN6\t", largest)
        println(out, "equalChangedButFlagFalse\t", changed)
        println(out, "equalChangeWitnessSeed\t", seed)
        println(out, "equalToyFunctionCalls\t", equal_calls)
        println(out, "forcedEarlySuccessFunctionCalls\t", forced_calls)
        println(out, "rawOptimizerRequestedLimit\t4")
        println(out, "rawOptimizerActualToyFunctionCalls\t", budget_calls)
    end
end
