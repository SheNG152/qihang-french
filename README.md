# 启航法语

中法双语词汇、语法和 DELF A1 口语练习。

## 下载测试版

[打开测试版下载页](https://github.com/zyh307/qihang-french/releases/tag/v2.2.0)

| 设备 | 下载文件 | 打开方式 |
|---|---|---|
| Windows | [Windows ZIP](https://github.com/zyh307/qihang-french/releases/download/v2.2.0/QihangFrench-Windows-v2.2.0.zip) | 完整解压，双击“启动启航法语.bat” |
| 安卓 | [APK](https://github.com/zyh307/qihang-french/releases/download/v2.2.0/QihangFrench-Android-v2.2.0.apk) | 下载后安装 |
| 口语练习，两端通用 | [ggml-model-q5_0.bin](https://github.com/zyh307/qihang-french/releases/download/v2.1.1-beta.1/ggml-model-q5_0.bin) | 设置 → 口语 → 导入本地模型 |
| 非课内单词和例句语音，两端通用 | [语音包 ZIP](https://github.com/zyh307/qihang-french/releases/download/v2.2.0/QihangFrench-ExtraAudio-v1.zip) | 设置 → 语音 → 下载语音包，或导入本地语音包 |

课内录音已内置。课外词库包含 18,655 个词条，支持逗号导入；单词与例句录音通过 GitHub 下载，支持暂停、继续和删除。网络无法连接 GitHub 时，可下载 ZIP 后在同一入口导入。

只用词汇或语法功能，不需要下载识别模型。识别模型约 1.08 GB，口语转写在当前设备运行；考官回复需要联网。

## 口语开始使用

1. 导入下载页提供的原识别模型，等待校验完成。
2. 允许麦克风，点击“绑定小智”。
3. 在自己的小智账号创建法语考官，粘贴应用提供的考官配置，选择模型和法语音色，使用绑定码添加设备。
4. 返回应用选择练习。说完自动转写并发送，无需确认或修改文字。

电脑和手机分别绑定。模型、绑定和记录保存在各自设备，更新时不要先卸载。AI 点评依据文字，不评发音，也不提供官方成绩。

## 词汇与语法

词汇支持逐课背诵、选择、拼写、收藏、错题及定期复习。语法按单元进入课次，先看本课概览，再逐个学习语法点，各单元综合练习分别保存进度。教材分别记住上次选择的 Lesson；导入本每课 30 词，与 Inspire 共用卡片背诵和五词练习。

[资料导入教程](docs/使用教程.md)

## 源码

Node.js 20+：`npm ci`、`npm run dev`。口语运行时构建见 [构建说明](native/BUILD.md)。用户直接下载成品，无需安装开发工具。

程序采用 GPL-3.0-only，第三方模型及依赖保留其许可。Copyright (C) 2026 启航 AI 俱乐部。
