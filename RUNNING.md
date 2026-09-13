# 运行帮助

本文件说明如何启动已经完成的 O6 抓握仿真。项目来源、模型修改及实验结果见 [结营报告](README.md)，提交范围见 [提交清单](SUBMISSION.md)。

## 1. 默认入口：打开 Isaac Sim 窗口

在项目根目录打开终端，执行：

```bash
bash run.sh
```

它与下面的命令等价：

```bash
bash start_isaacsim.sh
```

默认行为是打开 Isaac Sim 图形窗口，等待用户启动动作，并在演示结束后保留窗口。

1. 等待 O6、方块和支撑台加载完成。首次启动可能需要编译着色器。
2. 找到 **O6 Grasp Demo** 面板。
3. 点击 **Start grasp**，三秒后开始演示；也可在启动终端按回车。
4. **Whole scene** 显示全景，**Close-up** 显示抓握近景。
5. 观看手指闭合、支撑台撤离、保持、张手掉落的完整过程。不要用时间轴 Play 按钮代替 Start grasp。
6. 面板显示 **PASS. Demo finished.** 后，窗口仍保持打开。关闭 Isaac Sim 窗口才退出程序。

演示为九秒仿真；GUI 播放不会快于实时速度，较慢机器可能需要更长实际时间。想再演示一次，关闭窗口后重新运行启动命令。

## 2. 三个启动脚本的区别

| 脚本 | 窗口 | 开始方式 | 结束行为 | 默认输出 |
|---|---|---|---|---|
| `run.sh` | 打开 | 窗口内 Start grasp | 保留窗口 | `outputs/interactive/` |
| `start_isaacsim.sh` | 打开 | 窗口内 Start grasp | 保留窗口 | `outputs/interactive/` |
| `run_recording.sh` | 无窗口 | 自动 | 录制、验收、合成后退出 | `outputs/run/` |

`run.sh` 是默认入口，实际调用 `start_isaacsim.sh`。需要批量生成视频时才使用 `run_recording.sh`。

## 3. 环境与路径

已验证环境：Ubuntu 22.04.5、Isaac Sim 5.0.0 RC 构建、Isaac Lab 2.2.0、Isaac Sim 自带 Python 3.11、RTX5880-Ada-8Q 8 GB、驱动 570.172.18。

- Isaac Sim 默认路径：`/opt/IsaacSim`。
- Isaac Lab 默认路径：`/opt/IsaacLab`，用于加载 Kit 启动配置。
- 模型默认路径：脚本所在目录下的 `assets/o6_hand.usd`。
- 物理使用 CPU PhysX；相机使用 RTX GPU 渲染。
- 模型和地面均使用本地资源，无需下载远程场景或训练权重。

安装位置不同时：

```bash
ISAAC_SIM_PATH=/path/to/IsaacSim \
ISAAC_LAB_PATH=/path/to/IsaacLab \
bash run.sh /absolute/path/to/output
```

同样的环境变量可用于另外两个启动脚本。请使用 Ubuntu 图形桌面的终端运行窗口模式；仅有命令行、未连接图形显示的会话不适合观看 GUI。

仿真脚本必须用 Isaac Sim 的 `python.sh` 启动。独立验收脚本 `verify.py` 只使用 Python 标准库，可用系统 Python。

## 4. 自己录屏与自动相机视频

### 手动录制 Isaac Sim 窗口

```bash
bash start_isaacsim.sh "$PWD/outputs/my_recording"
```

场景加载完成后，先开启自己的录屏工具，再点击 **Start grasp**。演示完成、面板显示 PASS 后停止录屏。每次使用不同输出目录，可以保留前一轮结果。

### 程序如何生成视频

程序使用 **Isaac Sim 内置 Camera API** 渲染近景和全景两路相机，使用 **imageio/FFmpeg** 将画面编码为 MP4。它没有调用 Isaac Sim 界面中的录屏按钮，也不是桌面截图录制。

窗口模式仍会自动保存：

- `grasp_raw.mp4`：原始近景视频。
- `overview_raw.mp4`：原始全景视频。
- `trajectory.json`：与原始相机帧对应的物理状态和接触力。
- `parameters.json`：本次运行参数。
- `verification.json`：完整验收结果。
- `scene_initial.usd`、`scene_held.usd`：静态快照，不是含完整动作的动画文件。

关闭窗口后，可为刚录制的数据合成双视角字幕视频：

```bash
/opt/IsaacSim/python.sh compose_video.py outputs/my_recording
```

成片为 `outputs/my_recording/O6_grasp_demo.mp4`。前九秒为原速相机画面，最后两秒为验收结果页。

### 无窗口自动完成录制和合成

```bash
bash run_recording.sh
```

成片默认为 `outputs/run/O6_grasp_demo.mp4`。

### 视频依赖

本机的 Isaac Sim Python 已安装 `imageio`、`imageio-ffmpeg`、Pillow。其他机器缺失时，可在对应环境安装：

```bash
/opt/IsaacSim/python.sh -m pip install imageio imageio-ffmpeg Pillow
```

中文字幕默认字体为 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`。字体位置不同时：

```bash
/opt/IsaacSim/python.sh compose_video.py outputs/my_recording \
  --font /path/to/chinese-font.ttc
```

## 5. 独立验收

检查随包提交的记录：

```bash
python3 verify.py results
```

检查刚完成的窗口演示：

```bash
python3 verify.py outputs/interactive
```

输出 `"pass": true` 且退出码为 0，表示全部条件通过。验收检查连续两秒保持、位移、与支撑台分离、手指接触力、支撑台零接触力，以及张手后下落。

只运行物理和日志、不开启相机录制：

```bash
/opt/IsaacSim/python.sh grasp_demo.py --output outputs/physics_only
```

该方式不显示图形窗口。希望在 Isaac Sim 中观看完整过程时，应使用第一节的默认入口。

## 6. 直接调用 Python 入口

需要自定义参数时，可执行：

```bash
/opt/IsaacSim/python.sh grasp_demo.py \
  --isaaclab /opt/IsaacLab \
  --gui --wait-for-start --keep-open \
  --output outputs/manual_recording
```

| 参数 | 默认值 | 含义 |
|---|---|---|
| `--gui` | 关闭 | 打开窗口并录制相机 |
| `--wait-for-start` | 关闭 | 等待窗口按钮或终端回车，需要 `--gui` |
| `--keep-open` | 关闭 | 完成后保留窗口，需要 `--gui` |
| `--render` | 关闭 | 无窗口模式下启用相机录制 |
| `--isaaclab` | `/opt/IsaacLab` | Isaac Lab 根目录 |
| `--asset` | 脚本旁的 `assets/o6_hand.usd` | O6 模型路径 |
| `--output` | `outputs/run` | 相对当前终端目录的输出路径 |
| `--cube-x / --cube-y / --cube-z` | `0.043 / 0 / 0.095` | 方块初始位置；z 相对手腕安装高度 0.22 m |
| `--size` | `0.05` | 方块边长，m |
| `--finger` | `1.30` | 四指 MCP 闭合目标，rad |
| `--thumb-yaw / --thumb-pitch` | `1.20 / 0.50` | 拇指闭合目标，rad |
| `--duration` | `9.0` | 仿真时长，s；完整验收建议保留默认值 |

参数表列的是 Python 入口默认值；`run.sh` 已自动传入 GUI、等待启动和保留窗口的参数。

## 7. 常见问题

- **只在终端运行后退出，没有窗口**：使用 `bash run.sh`，不要使用 `run_recording.sh` 或不带 `--gui` 的 Python 命令。
- **窗口加载后不动**：点击 O6 Grasp Demo 面板的 Start grasp。
- **启动时暂时没有新日志**：首次着色器编译可能较慢，等待场景和操作面板加载。
- **找不到 `isaacsim`**：确认使用对应安装中的 `python.sh`。
- **找不到 Kit 文件**：检查 `ISAAC_LAB_PATH` 或 `--isaaclab`。
- **找不到 O6 模型**：确保 `assets/o6_hand.usd` 随源码一起复制。
- **不知道从哪里重新开始**：当前面板提供单轮演示，关闭后重新运行脚本即可。
- **调整参数后验收失败**：提交参数只验证了当前固定场景，修改后需要重新调试并验收。

## 8. 输出与提交文件

随包的 `results/` 保存已验收成果。新的运行输出放在 `outputs/`，不会被默认提交到 Git。提交时使用 [SUBMISSION.md](SUBMISSION.md) 中的清单，不需要加入调试缓存或整个 Isaac Sim 安装目录。
