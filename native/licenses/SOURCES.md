# 本地口语组件


- 法语模型：bofenghuang/whisper-large-v3-french，MIT；固定提交 `90a7cd1fea9cd69f80f5a0fc49738418dba96083`。文件、大小和 SHA-256 见 model-manifest.json。作者模型卡随附。权重单独下载，不随软件分发。
- whisper.cpp / ggml：ggml-org/whisper.cpp `v1.8.3`，MIT。Windows 使用该版本的官方 x64 动态库；安卓由相同源码编译 ARM64 CPU 实现。
- Opus：Xiph.Org `1.5.2`，BSD。https://downloads.xiph.org/releases/opus/opus-1.5.2.tar.gz
- JSON-java：stleary/JSON-java `20240303`，附原始许可。安卓使用系统 org.json。
- Windows Java 运行环境：Eclipse Temurin `21.0.13+9` JRE x64，GPLv2 with Classpath Exception；完整 LICENSE、NOTICE 和 legal 目录随运行环境提供。来源与 SHA-256 见 runtime-source.json。
- Windows C++ 辅助库：MinGW-w64 GCC 8.1.0，GCC Runtime Library Exception；winpthreads 原许可随附。
- Microsoft Visual C++ OpenMP Runtime：`vcomp140.dll` x64，14.44.35211.0。取自 Microsoft 官方 Visual C++ 2015–2022 Redistributable，下载来源与校验值见 runtime-source.json；许可见 Microsoft-Visual-C++-Runtime.rtf。仅按可再分发组件随 Windows 运行包提供。
- Android NDK `r27d` 只用于构建，不随软件分发。
- 小智协议参考：78/xiaozhi-esp32 的 OTA 激活、WebSocket 与 MCP 实现。客户端不包含小智云端服务、他人身份或任何共享 AI 密钥。

本应用源码按 GPL-3.0-only 提供。模型与各依赖按各自许可提供。
