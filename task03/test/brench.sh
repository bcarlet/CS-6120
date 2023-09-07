#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: bash $0 TOML [BENCHMARK_DIRS...]"
    exit 1
fi

brench_dir() {
    brench "$1" "$2"/*.bril |
        awk -v suite="$(basename "$2")" -v OFS=, "$3 NR>1 {print suite, \$0}"
}

for suite in "${@:2:1}"; do
    brench_dir "$1" "$suite" 'NR==1 {print "suite", $0}'
done

for suite in "${@:3}"; do
    brench_dir "$1" "$suite"
done
