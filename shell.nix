{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [
    pkgs.python3
    pkgs.python3Packages.torch
    pkgs.python3Packages.transformers
    pkgs.python3Packages.accelerate
    pkgs.python3Packages.sentencepiece
    pkgs.python3Packages.safetensors
    pkgs.python3Packages.numpy
  ];
  shellHook = ''
    echo "DET transformer probe shell (NixOS)"
    echo "  python: $(python3 --version)"
    python3 -c "import torch; print('  torch:', torch.__version__)"
    python3 -c "import transformers; print('  transformers:', transformers.__version__)"
    echo "run: python experiment.py"
  '';
}
