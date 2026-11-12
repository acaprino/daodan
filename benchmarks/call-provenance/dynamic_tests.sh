#!/bin/sh
# Runs inside the container, on a network without a route outside.
# Jest in shards, one process at a time. With an interval each shard runs under the
# V8 CPU profiler and its profile is mapped to call sites and removed; with `exact`
# each shard runs under dynamic_record.js, which writes the sites itself.
#
#   dynamic_tests.sh <project root> <test dir> <out dir> <shards> <interval in microseconds | exact> [jest arguments]
#
# DYN_WORKERS=<n> runs each shard with n Jest workers instead of one process;
# DYN_ONLY=<i> runs shard i alone.
root=$1; tests=$2; out=$3; shards=$4; interval=$5
shift 5
tool=$(dirname "$0")
band="--runInBand"
[ -n "$DYN_WORKERS" ] && band="--maxWorkers=$DYN_WORKERS"
cd "$root/$tests" || exit 2
# Babel reprints the code Jest runs: without retainLines the lines are not the source's.
if [ "$interval" = exact ]; then
  printf "module.exports = { retainLines: true, plugins: ['%s/dynamic_record.js'] };\n" "$tool" > babel.config.js
else
  printf 'module.exports = { retainLines: true };\n' > babel.config.js
fi
mkdir -p "$out"
: > "$out/run.log"
started=$(date +%s)
i=${DYN_ONLY:-1}
while [ "$i" -le "${DYN_ONLY:-$shards}" ]; do
  t0=$(date +%s)
  if [ "$interval" = exact ]; then
    rm -f "$out"/observed-"$i"-*.json
    DYN_ROOT="$root" DYN_OUT="$out/observed-$i-%p.json" NODE_OPTIONS="--require $tool/dynamic_record.js" \
      node "$root/node_modules/.bin/jest" $band --shard="$i/$shards" "$@" > "$out/jest-$i.log" 2>&1
    code=$?
    mapped="observed_kb=$(du -ck "$out"/observed-"$i"-*.json 2>/dev/null | tail -1 | cut -f1)"
  else
    rm -rf "$out/prof-$i"; mkdir -p "$out/prof-$i"
    NODE_OPTIONS="--cpu-prof --cpu-prof-dir=$out/prof-$i --cpu-prof-interval=$interval" \
      node "$root/node_modules/.bin/jest" $band --shard="$i/$shards" "$@" > "$out/jest-$i.log" 2>&1
    code=$?
    mapped="profile_mb=$(du -sm "$out/prof-$i" | cut -f1) $(node "$tool/dynamic_map.js" "$root" "$out/prof-$i" "$out/observed-$i.json" 2>&1 | tail -1)"
    rm -rf "$out/prof-$i"
  fi
  summary=$(grep -E "^(Tests|Test Suites):" "$out/jest-$i.log" | tr '\n' ' ')
  echo "shard $i/$shards exit=$code seconds=$(( $(date +%s) - t0 )) $summary $mapped" >> "$out/run.log"
  i=$(( i + 1 ))
done
peak=$(cat /sys/fs/cgroup/memory.peak 2>/dev/null)
echo "done seconds=$(( $(date +%s) - started )) memory_peak_bytes=$peak" >> "$out/run.log"
