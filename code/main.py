"""SuperTutor v5.0 — 侧边栏 selectbox 切换页面"""
import os, json, sqlite3
from datetime import datetime, timedelta
import streamlit as st

from config import CFG_FILE, _config, RAW, CPD, IDX, LOG, DB, DIFFS, COUNTS, get_subjects, get_api_key
from database import init_db, db_query, course_list, course_create, course_delete, course_update, course_get
from database import kp_list, kp_upsert, wrong_list_unmastered, wrong_record, wrong_review
from quiz import generate_quiz, kp_update_mastery
from plan import generate_plan, detect_weak_points
from harvest import harvest_file, harvest_fragment
from compile import compile_knowledge, list_compiled
from qa import answer_question

st.set_page_config(page_title="SuperTutor", page_icon="🎓", layout="wide")

st.markdown("""
<style>
/* 按钮 */
.stButton > button {
    border-radius: 10px; font-weight: 600; border: none;
    background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff;
    box-shadow: 0 2px 8px rgba(59,130,246,0.25);
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-2px); box-shadow: 0 6px 20px rgba(59,130,246,0.4);
}
.stButton > button:active { transform: scale(0.97); }

/* 统计卡片 */
div[data-testid="stMetric"] {
    background: #fff; border-radius: 14px; padding: 12px 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: all 0.25s;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

/* 进度条 */
.stProgress > div > div { border-radius: 8px; }

/* 背景 */
.stApp { background: #f5f7fa; }
section[data-testid="stSidebar"] { background: #fff; }
</style>
""", unsafe_allow_html=True)

# ---- init ----
sk = _config.get("DEFAULT", "DEEPSEEK_API_KEY", fallback="")
if sk == "sk-your-key-here": sk = ""
for k, v in {"api_key": sk, "current_course_id": None, "page": "总览",
             "quiz_qs": [], "quiz_idx": 0, "quiz_submitted": False, "quiz_finished": False, "quiz_res": [],
             "plan": "", "today_tasks": [], "today_checked": False,
             "review_mode": None, "last_quiz_params": None}.items():
    if k not in st.session_state: st.session_state[k] = v

init_db()
courses = course_list()
if not courses: st.session_state.current_course_id = course_create("默认课程")
elif st.session_state.current_course_id is None: st.session_state.current_course_id = courses[0][0]
for s in get_subjects(): (RAW / s).mkdir(parents=True, exist_ok=True); (CPD / s).mkdir(parents=True, exist_ok=True)
if not IDX.exists(): IDX.write_text("# 索引\n", encoding="utf-8")
if not LOG.exists(): LOG.write_text("# 日志\n", encoding="utf-8")

cid = st.session_state.current_course_id
course = course_get(cid)
kp_data = kp_list(cid) if cid else []
total_kp = len(kp_data); weak_kp = sum(1 for r in kp_data if r[8])

# ---- sidebar ----
with st.sidebar:
    st.title("🎓 SuperTutor")

    page = st.selectbox("页面", ["📊 总览", "📚 知识库", "🎯 练习", "📅 规划"],
                         index=["总览","知识库","练习","规划"].index(st.session_state.page),
                         key="nav_page", label_visibility="collapsed")
    page = page.replace("📊 ","").replace("📚 ","").replace("🎯 ","").replace("📅 ","")
    if page != st.session_state.page: st.session_state.page = page; st.rerun()

    st.divider()
    key = st.text_input("🔑 API Key", value=st.session_state.api_key, type="password", placeholder="sk-...")
    if key != st.session_state.api_key: st.session_state.api_key = key
    saved = _config.get("DEFAULT", "DEEPSEEK_API_KEY", fallback="")
    if key and key != saved:
        if st.button("💾 保存 Key", use_container_width=True):
            _config.set("DEFAULT", "DEEPSEEK_API_KEY", key)
            with open(str(CFG_FILE), "w", encoding="utf-8") as f: _config.write(f)
            st.success("已保存"); st.rerun()
    elif key and key == saved: st.caption("✅ Key 已保存")
    st.divider()

    course_labels = []; course_id_map = {}; current_label = ""
    for c in courses:
        lab = f"{c[1]}" + (f" 📅{c[3]}" if c[3] else "")
        course_labels.append(lab); course_id_map[lab] = c[0]
        if c[0] == cid: current_label = lab
    sl = st.selectbox("课程", course_labels,
        index=course_labels.index(current_label) if current_label in course_labels else 0, key="cs", label_visibility="collapsed")
    if course_id_map.get(sl, cid) != cid:
        st.session_state.current_course_id = course_id_map[sl]
        st.session_state.quiz_qs = []; st.session_state.quiz_finished = False; st.rerun()
    with st.expander("➕ 新建"):
        if st.button("创建", key="ccb") and st.session_state.get("ncn",""):
            st.session_state.current_course_id = course_create(st.session_state.ncn); st.rerun()
        st.text_input("名称", key="ncn")
    if courses and len(courses) > 1:
        if st.button("🗑️ 删除当前", use_container_width=True):
            course_delete(cid); st.session_state.current_course_id = course_list()[0][0]; st.rerun()
    st.divider()
    overall_pct = f"{(sum(r[5] for r in kp_data)/total_kp*100):.0f}%" if total_kp else "0%"
    st.metric("知识点", f"{total_kp}个", delta=f"掌握 {overall_pct}", delta_color="normal")
    st.metric("薄弱", f"{weak_kp}个")
    with st.expander("📋 知识点详情"):
        for row in kp_data:
            color = "🟢" if row[5] >= 0.8 else ("🟡" if row[5] >= 0.5 else "🔴")
            pct = f"{row[5]:.0%}"
            st.markdown(f"**{pct}** {color} {row[2]}" + (" ⚠️" if row[8] else ""))
    if st.button("🔄 编译知识", use_container_width=True):
        with st.spinner("..."): r = compile_knowledge()
        st.success(r) if "✅" in r or "🔄" in r else st.warning(r); st.rerun()

# ---- 总览 ----
if st.session_state.page == "总览":
    st.subheader("📊 总览")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("知识总数", total_kp)
    c2.metric("已掌握", sum(1 for r in kp_data if r[5] >= 0.7 and r[6] >= 3))
    c3.metric("薄弱", weak_kp)
    c4.metric("待巩固", total_kp - sum(1 for r in kp_data if r[5] >= 0.7 and r[6] >= 3) - weak_kp)
    st.divider()
    st.subheader("📈 各学科掌握度")
    if kp_data:
        for s in get_subjects():
            avg_m = sum(r[5] for r in kp_data) / len(kp_data)
            icon = "✅" if avg_m >= 0.8 else ("⚠️" if avg_m < 0.5 else "")
            st.progress(min(avg_m, 1.0), text=f"{s}  {avg_m:.0%} {icon}")
    st.divider()
    st.subheader("🔴 薄弱知识点")
    wr = sorted([r for r in kp_data if r[8]], key=lambda x: x[5])
    if wr:
        for i, r in enumerate(wr[:5]):
            pri = "⚠️ 最高优先级" if i < 2 else ""
            st.markdown(f"├── **{r[2]}** — 正确率 {r[5]:.0%}  {pri}")
    else: st.success("暂无薄弱点")
    st.divider()
    st.subheader("📅 今日打卡任务")
    tasks = st.session_state.today_tasks
    if not tasks and wr:
        tasks = [(r[2], f"（薄弱）预计 {30 if r[5] < 0.4 else 20} 分钟") for r in wr[:3]]
    if tasks:
        for i, t in enumerate(tasks):
            name, detail = t if isinstance(t, tuple) else (t, "")
            done = st.session_state.get(f"task_{i}", False)
            label = f"✅ ~~{name}~~ {detail}" if done else f"☐ {name}  {detail}"
            if st.button(label, key=f"ck_{i}", use_container_width=True):
                st.session_state[f"task_{i}"] = not done; st.rerun()
        if all(st.session_state.get(f"task_{i}", False) for i in range(len(tasks))):
            st.success("🎉 今日任务全部完成！")
    else:
        st.info("暂无今日任务，请先生成复习计划或在规划页设置考试日期")

# ---- 知识库 ----
if st.session_state.page == "知识库":
    st.subheader("📤 上传资料")
    files = st.file_uploader("选择文件", ["pdf","ppt","pptx","doc","docx","txt","md"],
                             accept_multiple_files=True, label_visibility="collapsed")
    if files:
        for f in files:
            with st.spinner(f"处理 {f.name}..."):
                r = harvest_file(f, cid); st.success(r[0] if isinstance(r, tuple) else r)
    st.divider(); st.subheader("✍️ 碎片收割")
    frag = st.text_area("输入笔记", height=68, label_visibility="collapsed", placeholder="易错点或顿悟笔记...")
    if st.button("💾 收割碎片") and frag.strip(): st.success(harvest_fragment(frag, cid))
    st.divider()
    cf1, cf2 = st.columns([1,2])
    with cf1: fst = st.selectbox("状态", ["全部", "已掌握 ✅", "待巩固 ⚠️", "薄弱 🔴"], key="kbf")
    with cf2: fsearch = st.text_input("搜索", placeholder="关键词...", key="kbs")
    dk = kp_data
    if "已掌握" in fst: dk = [r for r in dk if r[5] >= 0.8 and r[6] >= 3]
    elif "待巩固" in fst: dk = [r for r in dk if 0.5 <= r[5] < 0.8]
    elif "薄弱" in fst: dk = [r for r in dk if r[8]]
    if fsearch: dk = [r for r in dk if fsearch.lower() in r[2].lower()]
    for row in dk:
        kp_id, _, name, desc, imp, mastery, tot, corr, iw, reason, lr = row
        icon = "✅" if mastery >= 0.8 else ("⚠️" if mastery >= 0.5 else "🔴")
        text = "已掌握" if mastery >= 0.8 else ("待巩固" if mastery >= 0.5 else "薄弱")
        st.markdown(f"{icon} **{name}** — {text}（{mastery:.0%}）| {imp or '知识点'} | {tot}次/{corr}对" + (f" | {reason}" if reason else ""))
    st.caption(f"共 {len(dk)} 个知识点")
    st.divider(); st.subheader("❓ 知识问答")
    q = st.text_input("问题", placeholder="例如：进程和线程的区别？", label_visibility="collapsed", key="qa_in")
    if st.button("🔍 提问") and q.strip():
        if not list_compiled(): st.warning("请先上传资料")
        else:
            with st.spinner("思考中..."): ans, srcs = answer_question(q, cid)
            if srcs: st.caption("📎 " + " | ".join(srcs))

# ---- 练习 ----
if st.session_state.page == "练习":
    st.subheader("🎯 练习")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        subjects = get_subjects(); sc = [s for s in subjects if list_compiled(s)]
        labels = [f"{s} ✅" if s in sc else s for s in subjects]
        q_subject = st.selectbox("学科", labels, index=subjects.index(sc[0]) if sc else 0, key="qs").replace(" ✅","")
    with c2: q_mode = st.selectbox("模式", ["薄弱点优先", "全面练习", "专项突破", "模拟考试"], key="qm")
    with c3: q_count = st.selectbox("题量", COUNTS, key="qc")
    with c4:
        has_w = any(r[8] for r in kp_data)
        weak_first = q_mode == "薄弱点优先" and has_w
        desc = {"薄弱点优先": "薄弱优先", "全面练习": "全面随机", "专项突破": "自选知识点", "模拟考试": "全科综合"}
        st.caption(desc.get(q_mode, ""))

    focus_kp_ids = []
    if q_mode == "专项突破" and kp_data:
        kp_names = {r[2]: r[0] for r in kp_data}
        selected_names = st.multiselect("选择要练习的知识点", list(kp_names.keys()), key="focus_kps")
        focus_kp_ids = [kp_names[n] for n in selected_names]

    exam_subject = q_subject if q_mode != "模拟考试" else None
    if st.button("🎲 生成题目", type="primary", use_container_width=True):
        with st.spinner(f"生成{q_count}道题..."):
            qs, _ = generate_quiz(exam_subject, "自动匹配", q_count, cid, weak_first, focus_kp_ids)
            if isinstance(qs, str): st.error(qs); st.session_state.quiz_qs = []
            elif qs:
                st.session_state.quiz_qs = qs; st.session_state.quiz_finished = False
                st.session_state.quiz_idx = 0; st.session_state.quiz_submitted = False; st.session_state.quiz_res = []
                st.session_state.last_quiz_params = (q_subject, "自动匹配", q_count, weak_first); st.rerun()

    qs = st.session_state.quiz_qs
    if qs and not st.session_state.quiz_finished:
        idx = st.session_state.quiz_idx; qz = qs[idx]
        is_weak_q = bool(qz.get("knowledge_point_id") in {r[0] for r in kp_data if r[8]})
        st.markdown(f"**📝 第 {idx+1} / {len(qs)} 题**" + ("  [`薄弱点`]" if is_weak_q else ""))
        st.markdown(f"### {qz['question']}")
        choice = st.radio("选项", qz["options"], key=f"qo_{idx}", index=None, disabled=st.session_state.quiz_submitted)
        st.progress((idx + (1 if st.session_state.quiz_submitted else 0)) / len(qs))
        if not st.session_state.quiz_submitted:
            if st.button("✅ 提交答案", type="primary", key="sub1"):
                if choice:
                    ul = choice[0] if choice else ""; cl = qz["answer"].strip()[0]; ok = ul == cl
                    st.session_state.quiz_res.append({
                        "i": idx, "q": qz["question"], "ua": choice, "ca": qz["answer"],
                        "ok": ok, "exp": qz.get("explanation",""), "src": qz.get("source_page",""),
                        "diff": qz.get("difficulty","")
                    }); st.session_state.quiz_submitted = True; st.rerun()
                else: st.warning("请选择一个选项")
        else:
            last = st.session_state.quiz_res[-1]
            if last["ok"]: st.success(f"✅ 正确！")
            else: st.error(f"❌ 错误！正确答案 {last['ca']}")
            if last.get("exp"):
                with st.expander("解析"): st.markdown(last["exp"]); st.caption(f"来源：{last['src']}")
            if is_weak_q: st.info("💡 这是薄弱点题目，答对可降低优先级")
            if idx + 1 < len(qs):
                if st.button("➡️ 下一题", type="primary", use_container_width=True):
                    st.session_state.quiz_idx += 1; st.session_state.quiz_submitted = False; st.rerun()
            else:
                if st.button("🏁 完成测验", type="primary", use_container_width=True):
                    res = st.session_state.quiz_res; correct_n = sum(1 for r in res if r["ok"])
                    qr_conn = sqlite3.connect(str(DB)); qr_conn.execute("PRAGMA foreign_keys = ON")
                    qr_conn.execute("INSERT INTO quiz_record(course_id,quiz_type,total_questions) VALUES(?,'periodic',?)", (cid, len(qs)))
                    qr_id = qr_conn.execute("SELECT last_insert_rowid()").fetchone()[0]; qr_conn.commit(); qr_conn.close()
                    for r in res:
                        qz2 = qs[r["i"]]; kp_id = qz2.get("knowledge_point_id")
                        valid_ids = {rr[0] for rr in kp_data}
                        if kp_id not in valid_ids: kp_id = None
                        if not kp_id:
                            src = qz2.get("source_page","未知")
                            for rr in kp_data:
                                if rr[2] in src or src in rr[2]: kp_id = rr[0]; break
                        if not kp_id: kp_id = kp_upsert(cid, src, f"自动创建：{src}")
                        kp_update_mastery(kp_id, r["ok"])
                        db_query("""INSERT INTO quiz_question(quiz_record_id,course_id,knowledge_point_id,
                            question_index,content,options,correct_answer,user_answer,explanation,difficulty)
                            VALUES(?,?,?,?,?,?,?,?,?,?)""",
                            (qr_id, cid, kp_id, r["i"]+1, r["q"],
                             json.dumps(qz2.get("options",[]), ensure_ascii=False),
                             qz2["answer"], r["ua"], qz2.get("explanation",""), qz2.get("difficulty","")))
                        if not r["ok"]:
                            qq_id = db_query("SELECT last_insert_rowid()", fetch=True)[0][0]
                            wrong_record(cid, kp_id, qq_id, "choice", r["q"],
                                         json.dumps(qz2.get("options",[]), ensure_ascii=False),
                                         qz2["answer"], r["ua"], qz2.get("explanation",""))
                    db_query("UPDATE quiz_record SET correct_count=?, accuracy=? WHERE id=?", (correct_n, correct_n/len(qs) if qs else 0, qr_id))
                    st.session_state.quiz_finished = True; st.rerun()

    if st.session_state.quiz_finished:
        res = st.session_state.quiz_res; cc = sum(1 for r in res if r["ok"])
        st.markdown(f"## 成绩：{cc}/{len(res)}（{cc/len(res)*100:.0f}%）")
        for r in res: st.markdown(f"{'✅' if r['ok'] else '❌'} **{r['i']+1}. {r['q']}**")
        if st.button("🔄 再来一组", use_container_width=True):
            st.session_state.quiz_qs = []; st.session_state.quiz_finished = False
            st.session_state.quiz_idx = 0; st.session_state.quiz_res = []; st.rerun()

    st.divider(); st.subheader("📕 错题本")
    wrong_rows = wrong_list_unmastered(cid)
    if wrong_rows:
        for row in wrong_rows[:10]:
            wid, wcid, kp_id2, qq_id, qtype, content, opts, correct_ans, user_ans, expl, rc, lr, mastered, created = row
            kp_name = next((r[2] for r in kp_data if r[0] == kp_id2), "")
            with st.expander(f"❌ {content[:50]}... [{kp_name}] {user_ans}→{correct_ans}"):
                if st.session_state.get("review_mode") == wid:
                    try: opts_list = json.loads(opts) if isinstance(opts, str) else opts
                    except: opts_list = []
                    ra = st.radio("重选", opts_list, key=f"rw_{wid}", index=None)
                    if st.button("确认", key=f"cf_{wid}") and ra:
                        ok2 = ra[0] == correct_ans[0]; wrong_review(wid, ra, ok2)
                        if ok2 and kp_id2: kp_update_mastery(kp_id2, True)
                        st.session_state.review_mode = None; st.rerun()
                else:
                    st.markdown(f"题目：{content}"); st.markdown(f"正确答案：{correct_ans} | 你的：{user_ans}")
                    if st.button("🔄 重新作答", key=f"redo_{wid}"): st.session_state.review_mode = wid; st.rerun()
    else: st.success("🎉 暂无错题")

# ---- 规划 ----
if st.session_state.page == "规划":
    st.subheader("📅 复习规划")
    if not course: st.warning("请先创建课程")
    else:
        dh = st.number_input("每日学习（分钟）", 30, 960, value=course[4] if course[4] else 240, step=30)
        if dh != course[4]: course_update(cid, daily_minutes=dh)

        # 各科考试日期（折叠面板）
        active_subjects = get_subjects()
        if "exam_dates" not in st.session_state: st.session_state.exam_dates = {}
        with st.expander("📋 各科考试日期（点击展开）", expanded=False):
            for s in active_subjects:
                default_d = st.session_state.exam_dates.get(s)
                if not default_d:
                    default_d = datetime.strptime(course[3], "%Y-%m-%d").date() if course and course[3] else datetime.now().date() + timedelta(days=30)
                c1, c2 = st.columns([3,1])
                with c1:
                    d = st.date_input(f"{s}", value=default_d, min_value=datetime.now().date(), key=f"ed_{s}")
                    st.session_state.exam_dates[s] = d
                with c2:
                    days = (d - datetime.now().date()).days
                    st.metric("剩余", f"{days}天")

        st.subheader("📊 掌握度总览")
        if kp_data:
            for row in kp_data:
                color = "🟢" if row[5] >= 0.8 else ("🟡" if row[5] >= 0.5 else "🔴")
                st.progress(min(row[5], 1.0), text=f"{color} {row[2]} {row[5]:.0%}" if row[6] > 0 else f"{color} {row[2]} 未练习")
        st.divider(); st.subheader("🔴 薄弱点")
        weak, obs = detect_weak_points(cid)
        for w in weak: st.markdown(f"⚠️ **{w['page']}** — {w['accuracy']:.0%}，{w['reason']}")
        for o in obs: st.markdown(f"👀 **{o['page']}** — {o['reason']}")
        if not weak and not obs: st.success("暂无薄弱点")
        custom_req = st.text_area("✏️ 自定义要求（选填）", height=68,
                                  placeholder="如：每天上午安排数据结构、下午安排操作系统；周末不安排学习...",
                                  key="custom_req", label_visibility="collapsed")
        if st.button("📋 生成复习计划", type="primary", use_container_width=True):
            if not list_compiled(): st.warning("请先上传资料")
            else:
                with st.spinner("生成中..."):
                    st.session_state.plan = generate_plan(cid, dh, custom_req, st.session_state.exam_dates)
                    # 从薄弱点自动生成今日打卡任务
                    wr2 = sorted([r for r in kp_data if r[8]], key=lambda x: x[5])
                    st.session_state.today_tasks = [
                        (r[2], f"（薄弱）预计 {30 if r[5] < 0.4 else 20} 分钟，正确率 {r[5]:.0%}")
                        for r in (wr2[:4] if wr2 else kp_data[:3])
                    ] if (wr2 or kp_data) else []
                    for i in range(10): st.session_state.pop(f"task_{i}", None)
        if st.session_state.plan:
            # 日期选择器
            today = datetime.now().date()
            dates_in_plan = []
            for s, d in st.session_state.exam_dates.items():
                days = (d - today).days
                if days > 0:
                    for i in range(days):
                        dt = today + timedelta(days=i)
                        if dt not in dates_in_plan:
                            dates_in_plan.append(dt)
            if not dates_in_plan:
                dates_in_plan = [today + timedelta(days=i) for i in range(30)]
            dates_in_plan.sort()
            date_labels = ["📋 完整计划"] + [d.strftime("%m/%d (%a)") for d in dates_in_plan]
            selected_date = st.selectbox("查看日期", date_labels, key="plan_date")

            # 本周视图
            ws = today - timedelta(days=today.weekday())
            st.subheader(f"📋 本周计划（{ws.strftime('%m/%d')} - {(ws+timedelta(days=6)).strftime('%m/%d')}）")
            wc = st.columns(7)
            for i, wd in enumerate(["周一","周二","周三","周四","周五","周六","周日"]):
                day = ws + timedelta(days=i)
                icon = "✅" if day < today else ("⏳" if day == today else "")
                wc[i].caption(f"{wd}\n{day.strftime('%m/%d')} {icon}")

            st.divider()
            if selected_date == "📋 完整计划":
                st.markdown(st.session_state.plan)
            else:
                st.info(f"📅 {selected_date} — 滚动查看当天内容")
                st.markdown(st.session_state.plan)

            st.download_button("📥 下载计划", st.session_state.plan, f"复习计划_{datetime.now().strftime('%Y%m%d')}.md", "text/markdown")
