"""配置常量 + API Key 读取"""
import os, configparser
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
CFG_FILE = BASE_DIR / "config.properties"
_config = configparser.ConfigParser()
if CFG_FILE.exists():
    _config.read(str(CFG_FILE), encoding="utf-8")

BASE_URL = _config.get("DEFAULT", "DEEPSEEK_BASE_URL", fallback="https://api.deepseek.com")
MODEL = _config.get("DEFAULT", "DEEPSEEK_MODEL", fallback="deepseek-chat")
TIMEOUT = _config.getint("DEFAULT", "DEEPSEEK_TIMEOUT", fallback=30)

KB_ROOT = BASE_DIR / "知识库"
RAW = KB_ROOT / "原始资料"
CPD = KB_ROOT / "编译后知识"
IDX = KB_ROOT / "全局索引.md"
LOG = KB_ROOT / "变更日志.md"
DB = BASE_DIR / "mastery.db"

ENTITIES = ["概念", "算法", "对比", "考试技巧"]
DIFFS = ["自动匹配", "基础", "中等", "困难"]
COUNTS = [3, 5, 8, 10]

DEFAULT_SUBJECTS = ["数据结构", "操作系统", "计算机网络", "计算机组成原理"]
KW_DICT = {
    "数据结构": ["树","图","栈","队列","链表","排序","查找","哈希","堆","遍历","二叉树"],
    "操作系统": ["进程","线程","死锁","内存","CPU","调度","文件系统","中断","信号量","内核"],
    "计算机网络": ["TCP","IP","HTTP","DNS","路由","协议","网络层","传输层","OSI","子网"],
    "计算机组成原理": ["CPU","指令","寄存器","ALU","总线","Cache","存储器","流水线","冯诺依曼"],
    "数学": ["函数","映射","极限","导数","积分","微分","矩阵","向量","概率","数列","定理","证明","集合"],
    "英语": ["vocabulary","grammar","reading","writing","translation","essay","sentence","paragraph","verb","noun"],
    "物理": ["力学","电磁","光学","热学","量子","速度","加速度","能量","电场","磁场"],
}

def get_subjects():
    from config.settings import RAW, CPD
    subs = set(DEFAULT_SUBJECTS)
    for parent in [RAW, CPD]:
        if parent.exists():
            for d in parent.iterdir():
                if d.is_dir():
                    subs.add(d.name)
    return sorted(subs)

def get_api_key():
    key = _config.get("DEFAULT", "DEEPSEEK_API_KEY", fallback="")
    if key and key != "sk-your-key-here":
        return key
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key
    try:
        return st.session_state.get("api_key", "")
    except:
        return ""
