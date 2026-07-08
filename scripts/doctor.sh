#!/usr/bin/env bash
set -euo pipefail

echo "== System =="
uname -a
lsb_release -a 2>/dev/null || cat /etc/os-release

echo
echo "== NVIDIA =="
nvidia-smi || true
nvcc --version || true

echo
echo "== Python/Docker/Git =="
python3 --version || true
git --version || true
docker --version || true
docker info >/dev/null 2>&1 && echo "Docker daemon: OK" || echo "Docker daemon: not accessible by this user"

echo
echo "== Disk/RAM =="
df -h /
free -h
