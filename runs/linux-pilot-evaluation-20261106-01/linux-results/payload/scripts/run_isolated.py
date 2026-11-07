"""One explicitly requested run using the shared isolated kernel; never auto-dispatch."""
from pathlib import Path
import argparse
from run_support import run_case


def main(args):
    if not args.global_search and not args.local_search:
        raise ValueError('At least one search phase must be enabled')
    phase = 'FULL' if args.global_search and args.local_search else 'GLOBAL_ONLY' if args.global_search else 'LOCAL_ONLY'
    return run_case(args.payload.resolve(), args.build.resolve(), args.java.resolve(), args.output.resolve(),
                    args.instance, args.seed, phase, args.fe_limit, seconds=args.time_seconds)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=['SHARE_CTX_GOM'], default='SHARE_CTX_GOM')
    parser.add_argument('--global-search', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--local-search', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--instance', choices=['20_8_5_1','100_2_3_1'], required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--fe-limit', type=int, required=True, help='Actual attempt cap, including initialization')
    parser.add_argument('--time-seconds', type=float, help='True TIME_LIMIT; FE remains a safety cap')
    for name in ('payload','build','java','output'):
        parser.add_argument('--'+name, type=Path, required=True)
    main(parser.parse_args())
