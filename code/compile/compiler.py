"""知识编译：碎片 → 结构化页面 + 双向链接"""
import re, json
from datetime import datetime
from config.settings import CPD, IDX, LOG, get_subjects
from compile.frontmatter import parse_fm, list_compiled
from harvest.file_harvest import list_raw
from ai.client import call_ai

def compile_knowledge():
    raws = list_raw()
    if not raws:
        return "⚠️ 没有待编译的原始资料"
    cp_list = list_compiled()
    compiled_sources = set()
    for cp in cp_list:
        fm, _ = parse_fm(cp.read_text(encoding="utf-8"))
        if fm.get("source"):
            compiled_sources.add(fm["source"])
    new_raws = [rf for rf in raws if rf.name not in compiled_sources]
    if not new_raws:
        return "✅ 所有资料已编译（无新文件需要处理）"
    existing_str = "\n".join(f"- {p.stem}（{p.parent.name}）" for p in cp_list) if cp_list else "（无已有页面）"
    results, backlinks, failed = [], {}, []

    for rf in new_raws:
        subject = rf.parent.name
        _, body = parse_fm(rf.read_text(encoding="utf-8"))
        prompt = f"""将以下学习资料编译为结构化知识页面。

【去重规则（必须遵守）】：
1. 先与已有页面对比，如果内容高度重叠（>70%相似），则 is_new=false，merge_with 填要合并的已有页面名
2. 如果跟已有页面是同一知识点的不同角度，合并到已有页面而非新建
3. 只有当内容确实在已有页面中不存在时，才 is_new=true
4. 标题要精确区分，不要出现多个页面标题本质相同

返回JSON：
{{"title":"页面标题（20字内）","subject":"学科","page_type":"概念/算法/对比/考试技巧","is_new":true,"merge_with":"","content":"Markdown内容","linked_pages":["被引用的页面名"]}}

已有页面：
{existing_str}

原始资料：{body[:5000]}"""
        r = call_ai(prompt, json_mode=True)
        if not r or r.startswith("⚠️"):
            err_detail = r[2:] if r and r.startswith("⚠️") else str(r)[:100]
            failed.append(f"❌ {rf.name}（{err_detail}）")
            continue
        try:
            d = json.loads(r)
        except:
            failed.append(f"❌ {rf.name}（AI返回格式异常，请重试）")
            continue
        title = d.get("title", rf.stem)
        ps = d.get("subject", subject)
        safe = re.sub(r"[\\/:*?\"<>|]", "_", title)[:80]
        now = datetime.now().strftime("%Y-%m-%d")
        is_new = d.get("is_new", True)
        merge_with = d.get("merge_with", "")

        if not is_new and merge_with:
            target_safe = re.sub(r"[\\/:*?\"<>|]", "_", merge_with)[:80]
            target_path = CPD / ps / f"{target_safe}.md"
            if target_path.exists():
                existing_content = target_path.read_text(encoding="utf-8")
                existing_content = re.sub(r"updated: .*", f"updated: {now}", existing_content)
                new_body = d.get("content", body)
                if new_body not in existing_content:
                    existing_content += f"\n\n---\n{new_body}"
                target_path.write_text(existing_content, encoding="utf-8")
                results.append(f"🔄 合并到：{target_safe}（{ps}）")
            else:
                content = f"---\ntype: {d.get('page_type','概念')}\nsubject: {ps}\nsource: {rf.name}\ncreated: {now}\nupdated: {now}\n---\n\n{d.get('content', body)}"
                (CPD / ps).mkdir(parents=True, exist_ok=True)
                (CPD / ps / f"{safe}.md").write_text(content, encoding="utf-8")
                results.append(f"✅ {safe}（{ps}）")
        else:
            content = f"---\ntype: {d.get('page_type','概念')}\nsubject: {ps}\nsource: {rf.name}\ncreated: {now}\nupdated: {now}\n---\n\n{d.get('content', body)}"
            (CPD / ps).mkdir(parents=True, exist_ok=True)
            (CPD / ps / f"{safe}.md").write_text(content, encoding="utf-8")
            for lp in d.get("linked_pages", []):
                backlinks.setdefault(lp, []).append(safe)
            results.append(f"✅ {safe}（{ps}）")

    if not results:
        return "⚠️ 编译失败：\n" + "\n".join(failed)

    for page, refs in backlinks.items():
        for s in get_subjects():
            pp = CPD / s / f"{page}.md"
            if pp.exists():
                txt = pp.read_text(encoding="utf-8")
                txt = re.sub(r"\n## 被以下页面引用\n.*", "", txt, flags=re.DOTALL)
                txt += "\n## 被以下页面引用\n" + "\n".join(f"- [[{r}]]" for r in set(refs)) + "\n"
                pp.write_text(txt, encoding="utf-8")
                break

    idx_lines = [f"# 知识库全局索引\n\n> 更新于 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
    for s in get_subjects():
        idx_lines.append(f"\n## {s}\n")
        d = CPD / s
        if d.exists():
            for f in sorted(d.glob("*.md")):
                fm, _ = parse_fm(f.read_text(encoding="utf-8"))
                idx_lines.append(f"- [[{f.stem}]]  ({fm.get('type','')})")
        else:
            idx_lines.append("- （暂无页面）")
    IDX.write_text("\n".join(idx_lines) + "\n", encoding="utf-8")

    today = datetime.now().strftime("%Y-%m-%d")
    log_content = LOG.read_text(encoding="utf-8") if LOG.exists() else "# 知识库变更日志\n"
    if today not in log_content:
        log_content += f"\n## {today}\n"
    for entry in results:
        if entry not in log_content:
            log_content += f"- {entry}\n"
    LOG.write_text(log_content, encoding="utf-8")

    msg = "\n".join(results)
    if failed:
        msg += "\n\n" + "\n".join(failed)
    return msg if results else ("⚠️ 编译全部失败：" + "\n".join(failed))
