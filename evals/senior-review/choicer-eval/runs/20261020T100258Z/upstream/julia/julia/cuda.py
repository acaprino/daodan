"""CUDA configuration and explicit environment diagnostics for the L40S path."""
import importlib.metadata
import json
import os
import platform
import torch


def configure(device_name='cuda', precision='bf16', seed=42):
    device = torch.device(device_name)
    if device.type == 'cuda' and device.index is None:
        device = torch.device('cuda', 0)
    if device.type == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA requested but unavailable. Run nvidia-smi and install the CUDA PyTorch wheel; CPU fallback is disabled.')
    if precision == 'bf16' and device.type == 'cuda' and not torch.cuda.is_bf16_supported():
        raise RuntimeError('This CUDA device does not support BF16; select --precision fp32.')
    torch.set_num_threads(int(os.environ.get('JULIA_CPU_THREADS', '4')))
    torch.manual_seed(seed)
    if device.type == 'cuda':
        torch.cuda.set_device(device)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.cuda.reset_peak_memory_stats(device)
    torch.set_float32_matmul_precision('high')
    return device


def environment(device):
    result = dict(python=platform.python_version(), torch=str(torch.__version__), cuda=torch.version.cuda,
                  transformers=importlib.metadata.version('transformers'), device=str(device))
    if device.type == 'cuda':
        prop = torch.cuda.get_device_properties(device)
        result.update(gpu=prop.name, vram_bytes=prop.total_memory,
                      compute_capability=list(torch.cuda.get_device_capability(device)))
    return result


def move(batch, device):
    return {k: v.to(device, non_blocking=device.type == 'cuda') for k, v in batch.items()}


def main():
    device = configure()
    x = torch.randn(512, 512, device=device, dtype=torch.bfloat16, requires_grad=True)
    (x @ x.T).float().square().mean().backward()
    torch.cuda.synchronize()
    report = environment(device)
    report['bf16_forward_backward_finite'] = bool(torch.isfinite(x.grad).all())
    print(json.dumps(report, indent=2))
    if not report['bf16_forward_backward_finite']:
        raise RuntimeError('CUDA BF16 diagnostic produced nonfinite gradients')


if __name__ == '__main__':
    main()
