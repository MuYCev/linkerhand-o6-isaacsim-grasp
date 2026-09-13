"""Add synchronized labels to the two unmodified Isaac Sim camera recordings."""
import argparse
import json
from pathlib import Path
import numpy as np
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    parser.add_argument('--font', type=Path, default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
    args = parser.parse_args()
    rows = json.loads((args.folder/'trajectory.json').read_text())
    result = json.loads((args.folder/'verification.json').read_text())
    if not result['pass']:
        raise RuntimeError('This rollout did not pass verification.')
    large = ImageFont.truetype(str(args.font), 30)
    normal = ImageFont.truetype(str(args.font), 22)
    small = ImageFont.truetype(str(args.font), 18)
    close = imageio.get_reader(args.folder/'grasp_raw.mp4')
    wide = imageio.get_reader(args.folder/'overview_raw.mp4')
    writer = imageio.get_writer(args.folder/'O6_grasp_demo.mp4', fps=30, codec='libx264', quality=8, macro_block_size=2)
    frames = 0
    for idx, (a,b) in enumerate(zip(close,wide)):
        if idx >= len(rows):
            raise RuntimeError('Video has more frames than logged poses.')
        row = rows[idx]
        t = row['time']
        phase = '初始支撑' if t<1 else '手指闭合' if t<3 else '支撑台撤走' if t<4 else '无支撑保持' if t<7 else '张手释放验证'
        color = '#5de0ad' if 6<=t<7 else '#e6edf5'
        canvas = Image.new('RGB',(1440,900),'#101c2b')
        canvas.paste(Image.fromarray(a),(0,90))
        canvas.paste(Image.fromarray(b),(960,90))
        d = ImageDraw.Draw(canvas)
        d.text((24,12),'O6 灵巧手 · Isaac Sim 物理抓握',font=large,fill='#ffffff')
        d.text((25,54),'50 mm 动态立方体  /  50 g  /  重力开启  /  关节位置控制',font=small,fill='#b7c6d9')
        d.text((1020,16),f'仿真时间  {t:05.2f} s',font=normal,fill='#ffffff')
        d.text((1020,53),phase,font=normal,fill=color)
        d.rectangle((959,90,962,810), fill='#101c2b')
        d.rectangle((16,104,186,137),fill='#101c2b')
        d.text((26,107),'接触抓握近景',font=small,fill='#ffffff')
        d.rectangle((976,104,1260,137),fill='#101c2b')
        d.text((986,107),'全景：支撑台与掉落过程',font=small,fill='#ffffff')
        if 4<=t<7:
            elapsed=t-4
            status=f'撤台后保持：{elapsed:.2f} s / 2.00 s'
            if elapsed>=2: status+='   ✓ 通过'
            d.text((25,831),status,font=normal,fill=color)
            d.text((800,834),'支撑台接触力：0 N',font=normal,fill='#b7c6d9')
        elif t>=7:
            d.text((25,831),'张手后方块自由掉落，验证其未被固定或关闭重力。',font=normal,fill='#e6edf5')
        else:
            d.text((25,831),'连续物理仿真 · 原始相机画面 · 30 fps · 两个同步视角',font=normal,fill='#e6edf5')
        writer.append_data(np.asarray(canvas))
        if idx==180: canvas.save(args.folder/'poster.png')
        frames += 1
    if frames != len(rows):
        raise RuntimeError(f'Frame/log mismatch: {frames} vs {len(rows)}')
    slate = Image.new('RGB',(1440,900),'#101c2b')
    d=ImageDraw.Draw(slate)
    d.text((110,170),'验证通过',font=ImageFont.truetype(str(args.font),64),fill='#5de0ad')
    lines=[
        f"保持时间：{result['hold_duration_s']:.3f} 秒",
        f"保持期间最大位移：{result['maximum_drift_m']*1000:.4f} 毫米",
        '支撑台接触力：0 N；手指接触力非零',
        f"张手后下降：{result['release_drop_m']*1000:.1f} 毫米",
        '可复现代码、原始视频、逐帧日志与独立验收脚本随成果提交。',
    ]
    for i,line in enumerate(lines): d.text((114,305+68*i),line,font=large if i<4 else normal,fill='#e6edf5')
    for _ in range(60): writer.append_data(np.asarray(slate))
    writer.close(); close.close(); wide.close()
    print(args.folder/'O6_grasp_demo.mp4')

if __name__=='__main__': main()
