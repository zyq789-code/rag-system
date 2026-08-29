"""批量导入知识库文档：自动创建知识库并按子目录上传 .md 文档。

用法（需先启动后端）：
    cd backend
    venv\\Scripts\\python.exe -X utf8 scripts\\import_kb.py
    venv\\Scripts\\python.exe -X utf8 scripts\\import_kb.py --dir data/interview_kb --base http://localhost:8080

每个子目录对应一个知识库，目录名即知识库名。
"""

import argparse
import sys
import time
from pathlib import Path

import requests


def _main() -> None:
    parser = argparse.ArgumentParser(description="批量导入知识库文档")
    parser.add_argument("--dir", default="data/interview_kb", help="知识库根目录")
    parser.add_argument("--base", default="http://localhost:8080", help="后端地址")
    parser.add_argument("--wait", type=int, default=180, help="等待处理完成的最大秒数")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    kb_root = Path(args.dir)
    if not kb_root.is_dir():
        print(f"目录不存在: {kb_root}")
        sys.exit(1)

    kbs = requests.get(f"{base}/api/knowledge-bases/").json()
    kb_by_name = {kb["name"]: kb["id"] for kb in kbs}

    doc_ids: list[tuple[str, str]] = []
    for sub in sorted(p for p in kb_root.iterdir() if p.is_dir()):
        kb_name = sub.name
        if kb_name in kb_by_name:
            kb_id = kb_by_name[kb_name]
            print(f"[知识库] {kb_name} 已存在，复用 {kb_id}")
        else:
            resp = requests.post(
                f"{base}/api/knowledge-bases/",
                json={"name": kb_name, "description": f"面试知识库 - {kb_name}"},
            )
            resp.raise_for_status()
            kb_id = resp.json()["id"]
            kb_by_name[kb_name] = kb_id
            print(f"[知识库] 创建 {kb_name} -> {kb_id}")

        for f in sorted(sub.glob("*.md")):
            with open(f, "rb") as fh:
                resp = requests.post(
                    f"{base}/api/documents/upload",
                    files={"file": (f.name, fh, "text/markdown")},
                    data={"kb_id": kb_id},
                )
            resp.raise_for_status()
            doc = resp.json()
            doc_ids.append((f.name, doc["id"]))
            print(f"  上传 {f.name} -> {doc['status']}")

    print(f"\n等待 {len(doc_ids)} 个文档处理完成（最多 {args.wait}s）...")
    deadline = time.time() + args.wait
    while time.time() < deadline:
        pending = [
            name
            for name, did in doc_ids
            if requests.get(f"{base}/api/documents/{did}/status").json()["status"]
            in ("pending", "processing")
        ]
        if not pending:
            break
        time.sleep(3)

    done = failed = 0
    for name, did in doc_ids:
        st = requests.get(f"{base}/api/documents/{did}/status").json()["status"]
        if st == "completed":
            done += 1
        elif st == "failed":
            failed += 1
            print(f"  FAILED: {name}")
        else:
            print(f"  超时未完成: {name} -> {st}")
    print(f"\n导入完成: 成功 {done} / 共 {len(doc_ids)}" + (f"，失败 {failed}" if failed else ""))


if __name__ == "__main__":
    _main()
