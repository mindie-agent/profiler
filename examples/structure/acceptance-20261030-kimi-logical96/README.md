# Kimi 逻辑与物理 head 分离回放

固定 Sim `aeb66892a20588825e0eb443894d5d9b6b71c641`，package SHA `7f30d18bcf75f1f4974fb9a1cc4301d063636f7156431ad4f93019b5e3a70200`。12 份 A5 TP8 输入明确修正为全局 96 个有效 MLA head（每 TP 12），保留原生 Prolog/FIA 的 16 个 padded slot；router 使用 BF16 操作数、FP32 输出。原 DP4 p32k 的 128-head 输入未改。

原 618 个完整 93 层 Body、采集 SHA、extraction SHA 与所有时长不变；12 份 case 输入 SHA 明确变化并分别保存。12/12 预测完成，0 失败，0 达标；4,568 项独立数值检查全部通过。单 worker 峰值 167.70 MiB，最大执行 7.30 秒。

[逐源对照](body-runtime-delta.md) 中预测相对 corrected86 只减少 0.043–0.047 ms，误差仍为 -25.01% 至 -31.88%。这次修正解决结构合同，不证明通信、Attention 或 MoE 的资源配方已足够准确。新的 MC2、KDA、paged MLA、BF16 grouped 源码机制应作为明确输入条件继续回放，不把它们计为本臂已选中。

[P4K 回放](decode-forward-p4k-replay.md)、[P16K 回放](decode-forward-p16k-replay.md) 保留 Body、逐层、运行时与模型输入身份。本轮未重新扫描采集、未启动真机。
