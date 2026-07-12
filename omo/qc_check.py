"""Poster QC check — iterate until all scores >= 8 and no misalignment."""
import requests, base64, json, sys

KEY = '830e1e1e5d464d6daae6f21323db0e40.UuAiCWFOXcGr62AF'
API = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
GEN = r'J:\code\MI band\腕上词典\release_repo\cover.png'
OUT = r'J:\code\MI band\腕上词典\omo\last_qc_result.txt'


def encode(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def run_qc():
    gen_b64 = encode(GEN)

    q = (
        '看图(腕上词典海报)。\n'
        '请逐项严格评分（低于8分视为不合格）：\n'
        '1) 文字是否有任何错位（不对齐、溢出、偏移、重叠）？请逐行检查。（评分1-10）\n'
        '2) 第二行文字"离线英汉词典 | 抬手即查"是否完整可见，没有被右侧裁切？\n'
        '3) 四个功能条目（中英查词、变形反查、模糊搜索、收藏历史）是否都在画面内且没有重叠？\n'
        '4) 功能标题和各自的描述文字是否左对齐，且描述在标题下方？\n'
        '5) 整体布局是否协调？（评分1-10）\n'
        '如果所有评分>=8且文字无错位，请回复"PASS"。否则给出2-3个具体问题。\n'
        '请用中文回答。'
    )

    body = {
        'model': 'glm-4v-flash',
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{gen_b64}'}},
                {'type': 'text', 'text': q},
            ]
        }],
        'temperature': 0.1,
    }

    r = requests.post(
        API,
        headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
        json=body,
        timeout=60,
    )
    content = r.json()['choices'][0]['message']['content']
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(content)
    return content


if __name__ == '__main__':
    result = run_qc()
    print('=== QC RESULT ===')
    print(result)
    print('=== END ===')
    if 'PASS' in result:
        print('>>> VERDICT: PASS')
        sys.exit(0)
    else:
        print('>>> VERDICT: FAIL - needs iteration')
        sys.exit(1)
