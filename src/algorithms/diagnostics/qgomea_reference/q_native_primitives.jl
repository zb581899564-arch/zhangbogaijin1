using Random
module NativeQ end
Base.include(NativeQ, ARGS[1])
const Q = NativeQ
include(joinpath(@__DIR__, "q_native_lifecycle.jl"))

const reference_seeds = Dict{Tuple, Int}()

function seed_for(mask, reference)
    key = (Tuple(mask), reference)
    get!(reference_seeds, key) do
        for seed in 0:1000000
            if rand(MersenneTwister(seed), mask) == reference
                return seed
            end
        end
        error("No native RNG seed found for required reference")
    end
end

parseints(text) = parse.(Int, split(text, ','))
vector_text(values) = join(values, ',')

function primitive_case(fields)
    parent, donor, mask, refs = parseints.(fields[2:5])
    n, reference = length(parent), refs[1]
    seed = seed_for(mask, reference)
    virtual, storage1, storage2 = collect(1:n), zeros(Int, n), zeros(Int, n)
    Q.create_differential_donor!(virtual, parent, donor, mask, MersenneTwister(seed))
    positioned = copy(parent)
    Q.mix_position_ox!(positioned, virtual, mask, storage1, storage2)
    ordered = copy(parent)
    Q.mix_order!(ordered, donor, mask, Q.IndexSet(n), Q.IndexSet(n), storage1)
    sequential = copy(positioned)
    Q.mix_order!(sequential, donor, mask, Q.IndexSet(n), Q.IndexSet(n), storage1)
    mapping = Q.wrap_assignment_to_permutation(p -> copy(p))(parent)
    values = [virtual[mask], positioned, ordered, sequential, mapping]
    join([fields[1], string(reference), vector_text.(values)...], '\t')
end

open(ARGS[3], "w") do output
    for line in eachline(ARGS[2])
        println(output, primitive_case(split(line, '\t')))
    end
end
run_lifecycle_checks(ARGS[4])
println("QGOMEA_NATIVE_REFERENCE_COMPLETE")
