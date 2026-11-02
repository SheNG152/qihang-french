# 原生口语回归检查

本组检查使用临时目录、协议替身与模拟识别结果，不读取模型、用户身份或正式学习记录。

Java协议检查需要JDK 17或更新版本，以及项目使用的官方 `org.json:json:20240303` jar：

```sh
python native/tests/run-tests.py --jdk /path/to/jdk --json-jar /path/to/json-20240303.jar
node --experimental-vm-modules native/tests/local-client.test.mjs
```

Java检查覆盖陪练、模拟和评价的短任务请求、MCP实际发言证据、未读任务的等待上限、题卡读取后的回复等待、没有start的空stop、平台错误提示和密钥脱敏。替身解码器不证明真实音频播放正常。

JS检查覆盖已经完成的识别任务立即取回、进行中的任务继续轮询、识别失败时保留原声且不提交考官，以及实际文字随题卡提交并得到回复。

实际平台仍需额外联调：记录“录音停止→识别完成→读取题卡→回复文字→首段声音”的时间。识别模型推理与平台回复耗时分开统计；本次不调整模型精度或推理参数。
