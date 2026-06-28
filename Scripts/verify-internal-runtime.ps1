$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot 'Runtime\.venv\Scripts\python.exe'
$RuntimePython = Join-Path $RepoRoot 'Runtime\Python'
$RuntimeVenvScripts = Join-Path $RepoRoot 'Runtime\.venv\Scripts'
$SitePackages = Join-Path $RepoRoot 'Runtime\.venv\Lib\site-packages'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Internal Python was not found: $Python"
}

$env:PYTHONNOUSERSITE = '1'
$env:PYTHONPATH = ''
$env:GENIE_DATA_DIR = Join-Path $RepoRoot 'GenieData'
$InternalPathParts = @(
    $RuntimeVenvScripts,
    $RuntimePython,
    (Join-Path $RuntimePython 'Scripts'),
    "$env:SystemRoot\System32",
    $env:SystemRoot
)

$NvidiaRoot = Join-Path $SitePackages 'nvidia'
if (Test-Path -LiteralPath $NvidiaRoot) {
    Get-ChildItem -LiteralPath $NvidiaRoot -Directory | ForEach-Object {
        $bin = Join-Path $_.FullName 'bin'
        if (Test-Path -LiteralPath $bin) {
            $InternalPathParts = @($bin) + $InternalPathParts
        }
    }
}

$env:PATH = $InternalPathParts -join ';'

@'
import os
import sys
import sysconfig
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper
import onnxruntime as ort

repo_root = Path(__file__).resolve().parents[0] if "__file__" in globals() else Path.cwd()
model_path = repo_root / "test" / "internal-cuda-add.onnx"
model_path.parent.mkdir(parents=True, exist_ok=True)

print("python_executable=", sys.executable)
print("python_base_prefix=", sys.base_prefix)
print("python_stdlib=", sysconfig.get_paths()["stdlib"])
print("onnxruntime_version=", ort.__version__)
print("available_providers_before_preload=", ort.get_available_providers())

if hasattr(ort, "preload_dlls"):
    ort.preload_dlls()

print("available_providers_after_preload=", ort.get_available_providers())

x = helper.make_tensor_value_info("x", TensorProto.FLOAT, [2])
y = helper.make_tensor_value_info("y", TensorProto.FLOAT, [2])
z = helper.make_tensor_value_info("z", TensorProto.FLOAT, [2])
node = helper.make_node("Add", ["x", "y"], ["z"])
graph = helper.make_graph([node], "internal_cuda_add_test", [x, y], [z])
model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
model.ir_version = 10
onnx.save(model, model_path)

session = ort.InferenceSession(
    str(model_path),
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
)
print("session_providers=", session.get_providers())
result = session.run(
    None,
    {
        "x": np.array([1, 2], dtype=np.float32),
        "y": np.array([3, 4], dtype=np.float32),
    },
)[0]
print("add_result=", result.tolist())

if "CUDAExecutionProvider" not in session.get_providers():
    raise SystemExit("CUDAExecutionProvider was visible but did not create a CUDA session")
'@ | & $Python -
