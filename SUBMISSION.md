# 最终提交清单

将 `O6_final_submission` 目录中的内容作为 GitHub 仓库根目录上传，或直接提交同名 ZIP。此目录是最终提交版本，包含已经确认可用的 GUI 启动方式。

## 文件结构

```text
O6_final_submission/
├── README.md                  # 结营报告：来源、模型修改、实现和实验结果
├── RUNNING.md                 # 启动、录屏、验收、依赖和问题排查
├── SUBMISSION.md              # 本提交清单
├── PROVENANCE.md              # 模型来源和原始 USD 哈希
├── .gitignore                 # 忽略新输出、缓存和本地环境
├── SHA256SUMS.json             # 此版本的文件校验清单
├── run.sh                     # 推荐入口：打开 Isaac Sim 窗口
├── start_isaacsim.sh           # GUI 入口，等按钮启动，结束后保留窗口
├── run_recording.sh            # 可选：无窗口自动录制和合成
├── grasp_demo.py              # 场景、模型适配、GUI、控制与录制
├── verify.py                  # 独立物理记录验收
├── compose_video.py           # 双视角视频和字幕合成
├── assets/
│   └── o6_hand.usd            # 运行必需的 O6 模型
└── results/
    ├── O6_grasp_demo.mp4      # 提交用成片
    ├── grasp_raw.mp4          # 原始近景视频
    ├── overview_raw.mp4       # 原始全景视频
    ├── poster.png            # 结营报告预览图
    ├── parameters.json       # 录制时的参数
    ├── trajectory.json       # 逐帧物理状态和接触力
    └── verification.json     # 验收结果
```

## 提交前需要补充

- 在 README 顶部填写姓名、训练营名称或期数、完成日期。
- 上传后填写代码仓库地址。
- 根据自己的工作记录调整报告措辞，保留项目来源和软件联动近似的说明。

源码、模型和随包结果已经准备好。不需要上传 `outputs/`、`__pycache__/`、旧调试目录、完整上游仓库或 Isaac Sim / Isaac Lab 安装目录。本机原有运行记录保留在此前的工作目录中，没有放进最终提交目录。

## 建议评阅顺序

1. 阅读 README 了解复现项目、O6 修改和实验结果。
2. 查看 `results/O6_grasp_demo.mp4`。
3. 按 RUNNING 中的 `bash run.sh` 启动 Isaac Sim，点击 Start grasp 观看实时过程。
4. 执行 `python3 verify.py results` 复查物理数据。

## 成果边界

本成果对应任务 3：固定场景下的灵巧手抓握仿真，采用关节位置控制。没有训练 PPO，也没有将另一款手型重新建模为 O6。原始 O6 USD 完整保留，模型适配在新场景中执行。

视频由 Isaac Sim 相机渲染并用 imageio/FFmpeg 编码；默认启动入口显示可交互的 Isaac Sim 窗口。二者不是同一件事，均在代码中保留。

随包参数记录包含原录制机器上的绝对路径，只用于溯源，不作为运行配置读取。运行模型默认从项目自己的 `assets/` 加载。

`SHA256SUMS.json` 对应打包时的文件内容。修改报告或代码后若需要保留严格一致的校验清单，应重新生成该清单。
