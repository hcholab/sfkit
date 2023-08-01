#!/usr/bin/env bash
#
# Determines the micro-architecture of the current system
# and downloads the appropriate release of sfkit.

set -euo pipefail

RED="\e[31m"
NOCOLOR="\e[0m"

if ! uname -a | grep -qE '(Linux|Microsoft)' ; then
  echo -e "${RED}Sorry, at the moment sfkit supports only Linux or WSL =("
  exit 1
fi

check_instr() {
  grep -q "$1" /proc/cpuinfo
}

more_info() {
  echo -e "${NOCOLOR}"
  echo "For more information about these features, please see "
  echo "https://en.wikipedia.org/wiki/X86-64#Microarchitecture_levels"
  echo
}

microarch=""
if check_instr avx2 ; then
  microarch="_v3"
  echo "INFO: Detected a CPU that supports both SSE2 and AVX2 instructions."
  echo "This means your CPU is optimal for full hardware acceleration of all operations! =)"
  more_info
elif check_instr sse2 ; then
  microarch="_v2"
  echo -e "${RED}WARNING: Detected x86-64-v2 microarchitecture, which supports SSE2 but not AVX2." >&2
  echo "This means most operations will be accelerated, but some may run sub-optimically =("
  echo "If possible, please switch to a CPU that supports AVX2."
  more_info
else
  echo -e "${RED}WARNING: Detected x86-64-v1 microarchitecture, which doesn't support SSE2 and AVX2 instructions." >&2
  echo "This means many cryptographic and bioinformatic operations will run sub-optimally =("
  echo "If possible, please switch to a CPU that supports both SSE2 and AVX2"
  more_info
fi

echo Downloading and unpacking sfkit...
url="https://github.com/hcholab/sfkit/releases/latest/download/sfkit_linux_amd64${microarch}.tar.gz"
{ curl -sLo- "${url}" || wget -qO- "${url}" ; } | tar -xzf-
echo

echo Installing sfkit...
cd sfkit
python -m pip install -U ./sfkit*.whl
rm ./sfkit*.whl
mv plink2 ~/.local/bin/
mv sfgwas ~/.local/bin/
mv secure-gwas ~/.local/bin/
echo

if ! type sfkit &>/dev/null && ! echo "$PATH" | grep -q "/.local/bin" ; then
  echo Updating PATH...
  echo "export PATH=\"\$PATH:\$HOME/.local/bin\"" >> ~/.profile
  source ~/.profile
  echo
fi

echo Installation is complete.
echo
sfkit -h
exec $SHELL
