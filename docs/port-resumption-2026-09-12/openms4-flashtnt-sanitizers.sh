#!/bin/bash
set -euo pipefail
W=/scratch/kohlbach/openms4-resume-final-56406032068d
D=/scratch/kohlbach/openms4-5d1e239-20260910/deps
B="$W/flashtnt-sanitizers"
test ! -e "$B"
mkdir -p "$B"
mkdir -p "$B/cli-provider/lib"
cp -a "$W/work/sdk/lib/"libOpenMS_CLI.so* "$B/cli-provider/lib/"
export CC="$D/bin/x86_64-conda-linux-gnu-gcc" CXX="$D/bin/x86_64-conda-linux-gnu-g++"
export PATH="$D/bin:$PATH" LD_LIBRARY_PATH="$B/cli-provider/lib:$D/lib"
export OPENMS_DISABLE_UPDATE_CHECK=ON OMP_NUM_THREADS=2
export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
unset OPENMS_DATA_PATH PYTHONPATH OPENMS_CONTRIB_LIBS
"$D/bin/cmake" -S "$W/source/packages/flashtnt" -B "$B" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DOPENMS4_REQUIRE_CLEAN_SOURCE=ON \
  "-DCMAKE_PREFIX_PATH=$W/work/sdk;$D" \
  "-DCMAKE_BUILD_RPATH=$B/cli-provider/lib" \
  '-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer' \
  '-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined' > "$B/configure.log" 2>&1
"$D/bin/cmake" --build "$B" --parallel 12 > "$B/build.log" 2>&1
"$D/bin/ctest" --test-dir "$B" --parallel 4 --output-on-failure --no-tests=error \
  --output-junit "$B/tests.xml" > "$B/tests.log" 2>&1
tail -20 "$B/tests.log"
