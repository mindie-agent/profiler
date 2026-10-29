# A5 V4.1 TP1/DP8/EP8 本地新采集

三份完整 kernel CSV 已落盘，源 SHA 与 DP0/rank0 采集目录已固定。启动日志/engine config 确认 FP8、TP1/DP8/EP8、force EPLB、APC 关闭；没有把 A3 DSpark7 与 Prefix 99% 的条件套用到本批。

| 采集 | CSV MiB | Client c | Profiled token TPOT P50 ms | Unprofiled token TPOT P50 ms |
|---|---:|---:|---:|---:|
| a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1 | 96.36 | 1 | 15.0416 | 12.7866 |
| a5_v41_fp8_tp1_dp8_ep8_tpot10ms_c8 | 91.60 | 8 | 14.8800 | 12.9272 |
| a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64 | 47.85 | 64 | 28.9430 | 29.0685 |

5 ms / 10 ms 是目标标签，实际并未达到。Profile 仅在队列空且所有客户端发出首 token 后打开约 2 秒；客户端 TPOT 仍与设备主体耗时不同。

每源只读取前 160 个事件寻找 ABI 线索，尚未做完整事件分段。HcPre/HcPost 有真实张量描述；MqsmlaKernel___call__ 的输入/输出 shape/dtype 在原 CSV 均为 N/A。缺失不能用 V4 的 ABI 或形状填补。后续应使用独立 V4.1 模型声明及整体结构边界验证，未获得这些证据前 Body/层耗时保持空值。
