# Beelink GTR9 Pro - Full Specification Sheet

## Overview

The Beelink GTR9 Pro is a compact, all-metal mini workstation powered by the AMD Ryzen AI Max+ 395 APU. At ~$2,000, it packs workstation-class AI compute into a chassis smaller than a shoebox. It is the foundation of a solo-dev AI R&D lab.

---

## Processor: AMD Ryzen AI Max+ 395

| Attribute | Value |
|---|---|
| Architecture | AMD Zen 5 (4nm TSMC) |
| Cores / Threads | 16 / 32 |
| Base Clock | 3.0 GHz |
| Boost Clock | 5.1 GHz |
| L3 Cache | 64 MB |
| Socket | FP11 |
| TDP (configured) | 140W |

## AI Compute

| Attribute | Value |
|---|---|
| NPU | AMD XDNA 2 |
| NPU TOPS | 50 TOPS (INT8) |
| Total Platform TOPS | 126 TOPS (CPU + GPU + NPU combined) |

## Integrated GPU: AMD Radeon 8060S

| Attribute | Value |
|---|---|
| Architecture | RDNA 3.5 |
| Compute Units | 40 |
| Stream Processors | 2,560 |
| Base Clock | 1,295 MHz |
| Boost Clock | 2,335 MHz |
| FP32 Performance | ~12-15 TFLOPS (single-issue) / ~29.7 TFLOPS (dual-issue) |
| Max Assignable VRAM | 96 GB (Windows) / ~110 GB (Linux) |
| L2 Cache | 8 MB |
| API Support | DirectX 12 Ultimate (12_2), Vulkan 1.3 |

### GPU Performance Context
- Sits between an RTX 4060 and RTX 4070 Laptop in gaming/graphics benchmarks
- Outperforms RTX 4090 by ~220% in AI efficiency (tokens/watt) per AMD benchmarks
- Can run models up to 128B parameters that don't fit in any discrete consumer GPU's VRAM

## Memory

| Attribute | Value |
|---|---|
| Type | LPDDR5X |
| Speed | 8000 MHz |
| Capacity | 128 GB |
| Bandwidth | ~256 GB/s |
| Soldered | Yes (not upgradeable) |

### Why This Memory Matters for AI
The 128 GB unified memory pool is the single biggest differentiator. Consumer GPUs top out at 24 GB (RTX 4090) or 48 GB (RTX 5090 rumored). The Beelink can assign up to 96-110 GB to the GPU, allowing it to load massive models entirely into GPU-accessible memory that would otherwise require $10,000+ enterprise hardware.

## Storage

| Attribute | Value |
|---|---|
| Included | 2 TB Crucial NVMe SSD |
| Slots | Dual M.2 2280 PCIe 4.0 |
| Max Capacity | 8 TB (2x 4TB) |
| Max Speed | ~7,000 MB/s |

## Networking

| Attribute | Value |
|---|---|
| Wired | Dual Intel 10 GbE E610-XT2 (2x 10Gbps) |
| WiFi | WiFi 7 |
| Bluetooth | 5.4 |

> **Known Issue:** The Intel E610-XT2 NICs have documented instability under sustained mixed GPU + network workloads. This was escalated to Intel and Beelink as of October 2025. Monitor firmware updates.

## Display Output

| Port | Spec |
|---|---|
| HDMI | 2.1 |
| DisplayPort | 2.1 |
| USB4 (x2) | 40 Gbps, 8K@60Hz capable |
| Max Displays | 4 simultaneous, up to 8K resolution |

## Ports & I/O

| Port | Count | Location |
|---|---|---|
| USB4 Type-C | 2 | Rear |
| USB Type-C | 1 | Front |
| USB 3.2 Type-A | 2 | Rear |
| HDMI 2.1 | 1 | Rear |
| DisplayPort 2.1 | 1 | Rear |
| 3.5mm Audio | 2 | Front + Rear |
| SD Card Reader | 1 | Front |

## Cooling & Power

| Attribute | Value |
|---|---|
| Cooling | Dual turbine fans + full-coverage vapor chamber |
| Noise | ~32 dB at 140W TDP |
| PSU | Integrated 230W |

## Physical Dimensions

| Attribute | Value |
|---|---|
| Width | 180 mm |
| Depth | 180 mm |
| Height | 90.8 mm |
| Chassis | All-metal exterior, aluminum internal frame |

## Price

| Configuration | Price |
|---|---|
| Ryzen AI Max+ 395 / 128 GB / 2 TB | ~$1,985 - $2,000 USD |

---

## LLM Inference Benchmarks (Community-Verified)

| Model | Tokens/sec | Notes |
|---|---|---|
| Small models (7B-8B) | 30-50+ TPS | With ROCm on Linux |
| Qwen3:32b | ~15 TPS (Ollama) | Without ROCm optimization |
| GPT-OSS:20b | ~50 TPS | With ROCm, prompt eval 500+ TPS |
| 70B dense models | ~3-5 TPS | Fits in memory; usable for batch, not real-time chat |
| 128B+ models | Runs | Llama 4 Scout 109B confirmed working with vision + MCP |

### Key Advantage
This machine can **load and run 70B-128B parameter models** that physically cannot fit into the VRAM of an RTX 4090 (24 GB), RTX 5090, or even a Mac M4 Pro. Only enterprise GPUs (A100 80GB, H100) or multi-GPU setups can match this capability, at 5-20x the cost.

---

## Sources

- [Beelink Official Product Page](https://www.bee-link.com/products/beelink-gtr9-pro-amd-ryzen-ai-max-395)
- [ServeTheHome Review](https://www.servethehome.com/beelink-gtr9-pro-review-amd-ryzen-ai-max-395-system-with-128gb-and-dual-10gbe/)
- [Amazon Listing](https://www.amazon.com/Beelink-GTR9-Crucial-Computer-DeepSeek/dp/B0FPQQYWQ1)
- [AMD Ryzen AI Max+ 395 Official](https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html)
- [NotebookCheck Specs](https://www.notebookcheck.net/AMD-Ryzen-AI-Max-395-Processor-Benchmarks-and-Specs.942323.0.html)
- [Radeon 8060S Specs](https://www.notebookcheck.net/AMD-Radeon-8060S-Benchmarks-and-Specs.942049.0.html)
- [Level1Techs LLM Benchmarks](https://forum.level1techs.com/t/strix-halo-ryzen-ai-max-395-llm-benchmark-results/233796)
- [Framework Community GPU LLM Tests](https://community.frame.work/t/amd-strix-halo-ryzen-ai-max-395-gpu-llm-performance-tests/72521)
- [Hardware Corner Inference Analysis](https://www.hardware-corner.net/how-fast-ai-max-395-llm-20250317/)
- [GMKTec Benchmarks](https://nishtahir.com/gmktec-evo-x2-ryzen-ai-max-395-benchmarks/)
- [AMD LM Studio Blog](https://www.amd.com/en/blogs/2025/amd-ryzen-ai-max-upgraded-run-up-to-128-billion-parameter-llms-lm-studio.html)
- [Craig Wilson NIC Issues](https://craigwilson.blog/post/2025/2025-09-25-beelink395bsod/)
