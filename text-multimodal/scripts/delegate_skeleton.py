#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""delegate_skeleton.py — 多模态委托脚本骨架（适配器模式，与具体模型解耦）

这是"阶段 0 委托通道"的施工起点。按 SKILL.md 流程使用：
  1. 运行前把 baseURL/模型名填入下方 CONFIG；密钥只从环境变量或本地凭据文件读取
     （见 load_secret —— 绝不硬编码、绝不打印明文，输出一律用 mask() 脱敏）
  2. 每个能力一个适配器：OpenAI 兼容（本骨架已实现）/ 文档推导 / 任务式（视频生成需按
     用户提供的文档补全 提交→轮询→下载 三步，本骨架给出流程注释）
  3. 结果默认存当前工作区 media_out/，打印绝对路径 + 相对路径

用法:
  python delegate_skeleton.py recognize <图片路径> [指令]
  python delegate_skeleton.py imagegen "<生成指令>" [--size 2K] [--ratio 16:9] [--image 图1,图2]
  python delegate_skeleton.py videorecognize <视频路径> [指令] [--max-tokens 8000]
  python delegate_skeleton.py videogen "<生成指令>" [--seconds 5] [--fps 24] [--size 720p] [--dry-run]
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from urllib import error, request

DEFAULT_OUT = Path.cwd() / 'media_out'
MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
        '.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime'}

# ---- 配置（按用户确认的《能力-模型匹配表》填写；密钥不写在这里）----
CONFIG = {
    'baseURL': '',            # 例如 https://api.example.com/v1
    'recogModel': '',         # 图片/视频识别模型
    'imageGenModel': '',      # 图片生成模型
    'videoGenModel': '',      # 视频生成模型
    'outputBaseURL': '',      # 任务式接口的存储桶地址（如无可留空）
    'keyEnv': 'MM_API_KEY',   # 密钥所在环境变量名
    'keyFile': None,          # 或本地凭据文件路径（如 ~/.config/keys.json）
}


def mask(key):
    """脱敏: sk-abc123 -> sk-***123"""
    if not key:
        return ''
    return key[:3] + '***' + key[-4:] if len(key) > 8 else '***'


def load_secret():
    v = os.environ.get(CONFIG['keyEnv'])
    if not v and CONFIG['keyFile'] and Path(CONFIG['keyFile']).expanduser().exists():
        v = json.loads(Path(CONFIG['keyFile']).expanduser().read_text()).get('apiKey')
    if not v:
        raise SystemExit(f'缺少凭据: 请设置环境变量 {CONFIG["keyEnv"]} 或提供本地凭据文件 —— '
                         f'先向用户索要 baseURL 与 API Key，收到后再继续（已加载: {mask(v)}）')
    return v


def to_data_url(p):
    p = str(p)
    if p.startswith(('http://', 'https://')):
        return p
    mime = MIME.get(Path(p).suffix.lower())
    if not mime:
        raise SystemExit(f'不支持的素材格式: {p}（支持: {", ".join(MIME)}）')
    return f'data:{mime};base64,' + base64.b64encode(Path(p).read_bytes()).decode()


def http_json(method, url, headers, body=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw else {}
    except error.HTTPError as e:
        return e.code, {'error': e.read().decode()[:500]}


def save_bytes(buf, out_path):
    DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(buf)
    print(f'已保存: {p.resolve().as_posix()}')
    print(f'相对路径: {p.as_posix()}')


# ---- 适配器：OpenAI 兼容（图片/视频识别 + 图片生成） ----
class OpenAiAdapter:
    def __init__(self, base, key):
        self.base, self.key = base, key
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': f'Bearer {key}'}

    def recognize(self, media_path, instruction, kind='image'):
        # kind: 'image' -> image_url 内容块；'video' -> video_url 内容块
        block_type = 'image_url' if kind == 'image' else 'video_url'
        body = {'model': CONFIG['recogModel'], 'max_tokens': 2000, 'messages': [{
            'role': 'user', 'content': [
                {'type': 'text', 'text': instruction},
                {'type': block_type, block_type: {'url': to_data_url(media_path)}},  # 必须带 type 字段（OpenAI 规范）
            ]}]}
        st, data = http_json('POST', f'{self.base}/chat/completions', self.headers, body)
        if st != 200:
            raise SystemExit(f'识别失败 ({st}): {data}')
        m = data['choices'][0]['message']
        return m.get('content') or m.get('reasoning_content')

    def imagegen(self, prompt, size=None, ratio=None, refs=None, dry=False):
        body = {'model': CONFIG['imageGenModel'], 'prompt': prompt, 'n': 1}
        if size:
            body['size'] = size
        if ratio:
            body['ratio'] = ratio
        if refs:  # 图生图/多图合成；b64_json 也必须放 extra_body 内
            body['extra_body'] = {'image': [to_data_url(r) for r in refs]}
        if dry:
            print('dry-run 请求体:\n' + json.dumps(body, ensure_ascii=False, indent=2))
            return
        st, data = http_json('POST', f'{self.base}/images/generations',
                             self.headers, body, timeout=300)
        if st != 200:
            raise SystemExit(f'图片生成失败 ({st}): {data}')
        item = (data.get('data') or [data])[0]
        if item.get('b64_json'):
            save_bytes(base64.b64decode(item['b64_json']),
                       DEFAULT_OUT / 'image.png')
        elif item.get('url'):
            st2, buf = http_bytes(item['url'])
            if st2 == 200:
                save_bytes(buf, DEFAULT_OUT / 'image.png')
            else:
                raise SystemExit(f'图片下载失败 ({st2})')
        else:
            raise SystemExit(f'返回格式无法解析: {json.dumps(data)[:500]}')


def http_bytes(url, timeout=180):
    try:
        with request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read()
    except error.HTTPError as e:
        return e.code, b''


# ---- 适配器：任务式（视频生成。端点/参数以用户提供的文档为准） ----
def videogen(prompt, seconds, fps, size, negative, seed, start_img, dry):
    # 按用户文档确认端点与参数；以下为通用流程骨架（TODO: 按文档补全）：
    # 1) 提交:  POST {baseURL}/videos
    #    body = {model, prompt, num_frames, frame_rate, width, height,
    #            seed, negative_prompt, image(图生视频)}
    #    num_frames 满足 8n+1 且 ≤ 上限（如 441）；时长 = 帧数 ÷ fps，推荐 24fps
    # 2) 轮询:  GET {baseURL}/videos/{task_id}（404 时尝试文档推荐的备选查询接口）
    #    10 秒间隔、10 分钟超时；completed/failed/error 才停止
    # 3) 下载:  优先任务返回的 url；其次 {outputBaseURL}/videos/{model}/{task_id}.mp4
    # 注意: 队列满(503)/限流(429) 退避重试(20/40 秒，最多 20 次)；
    #       多域名时选带存储桶的端点；下载失败如实报告任务 id，不谎称成功
    frames = max(1, min(441, round(seconds * fps)))
    frames = round((frames - 1) / 8) * 8 + 1  # 8n+1 规则
    if dry:
        print(f'dry-run: prompt={prompt} 时长={frames / fps:.1f}s @ {fps}fps '
              f'frames={frames} size={size} seed={seed}')
        return
    raise SystemExit('TODO: 按用户提供的视频生成接口文档补全提交/轮询/下载实现')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='task', required=True)

    p1 = sub.add_parser('recognize')
    p1.add_argument('media'); p1.add_argument('instruction', nargs='?', default='请详细描述内容')

    p2 = sub.add_parser('imagegen')
    p2.add_argument('prompt'); p2.add_argument('--size', default=None)
    p2.add_argument('--ratio', default=None); p2.add_argument('--image', default=None)
    p2.add_argument('--dry-run', action='store_true')

    p3 = sub.add_parser('videorecognize')
    p3.add_argument('media'); p3.add_argument('instruction', nargs='?', default='请详细描述内容')
    p3.add_argument('--max-tokens', type=int, default=8000)
    p3.add_argument('--thinking', action='store_true')

    p4 = sub.add_parser('videogen')
    p4.add_argument('prompt'); p4.add_argument('--seconds', type=float, default=5)
    p4.add_argument('--fps', type=int, default=24); p4.add_argument('--size', default='720p')
    p4.add_argument('--negative', default=None); p4.add_argument('--seed', type=int, default=None)
    p4.add_argument('--image', default=None); p4.add_argument('--dry-run', action='store_true')

    a = ap.parse_args()
    if not CONFIG['baseURL']:
        raise SystemExit('请先按《能力-模型匹配表》填写 CONFIG（baseURL/模型名）')

    key = load_secret()
    print(f'凭据已加载: {mask(key)}（来源: {CONFIG["keyEnv"] or CONFIG["keyFile"]}）')
    api = OpenAiAdapter(CONFIG['baseURL'], key)

    if a.task == 'recognize':
        print(api.recognize(a.media, a.instruction, kind='image'))
    elif a.task == 'imagegen':
        refs = a.image.split(',') if a.image else None
        api.imagegen(a.prompt, a.size, a.ratio, refs, a.dry_run)
    elif a.task == 'videorecognize':
        print(api.recognize(a.media, a.instruction, kind='video'))
    elif a.task == 'videogen':
        videogen(a.prompt, a.seconds, a.fps, a.size, a.negative, a.seed, a.image, a.dry_run)


if __name__ == '__main__':
    main()
