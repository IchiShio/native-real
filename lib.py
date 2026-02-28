#!/usr/bin/env python3
"""lib.py - 問題パイプライン共通ユーティリティ"""

import json
import re

VALID_FIELDS = {"diff", "text", "ja", "answer", "choices", "expl", "kp"}
VALID_DIFFS = {"lv1", "lv2", "lv3", "lv4", "lv5"}


def parse_response(raw, *, raise_on_error=True):
    """APIレスポンスの文字列を問題リストにパース・バリデーション

    raise_on_error=True (デフォルト): JSON パース失敗時に例外を再送出
    raise_on_error=False: JSON パース失敗時に [] を返す（check_batch.py 用）
    """
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        last_obj_end = raw.rfind("},")
        if last_obj_end > 0:
            try:
                questions = json.loads(raw[:last_obj_end + 1] + "\n]")
                print(f"  WARNING: レスポンスが途中で切れたため {len(questions)} 問のみ取得")
                return questions
            except json.JSONDecodeError:
                pass
        if raise_on_error:
            raise
        return []

    valid = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        if VALID_FIELDS - set(q.keys()):
            continue
        if q.get("diff") not in VALID_DIFFS:
            continue
        if not isinstance(q.get("choices"), list) or len(q["choices"]) != 5:
            continue
        valid.append(q)
    return valid
