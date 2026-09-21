import json
import os
import subprocess
from datetime import datetime


# =========================
# 日志输出
# =========================

def log(message):
    """打印带时间的日志"""

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"[{time}] {message}")


# =========================
# JSON解析
# =========================

def safe_json_load(text):
    """安全解析JSON"""

    try:
        return json.loads(text)

    except Exception as e:
        log("JSON解析失败")
        log(e)

        return None


# =========================
# 保存JSON
# =========================

def save_json(data, filename):

    with open(filename, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    log(f"JSON已保存: {filename}")


# =========================
# 读取JSON
# =========================

def load_json(filename):

    with open(filename, "r", encoding="utf-8") as f:

        return json.load(f)


# =========================
# 文件保存
# =========================

def save_text(text, filename):

    with open(filename, "w", encoding="utf-8") as f:

        f.write(text)

    log(f"文件已保存: {filename}")


# =========================
# 创建目录
# =========================

def ensure_dir(path):

    if not os.path.exists(path):

        os.makedirs(path)


# =========================
# 启动OpenFTA
# =========================

def open_openfta(openfta_path, xml_file):

    if not os.path.exists(openfta_path):

        log("OpenFTA路径错误")

        return

    cmd = f'"{openfta_path}" "{xml_file}"'

    subprocess.Popen(cmd)

    log("OpenFTA已启动")


# =========================
# 故障列表去重
# =========================

def unique_list(items):

    return list(set(items))


# =========================
# 构建简单FTA结构
# =========================

def build_simple_tree(top_event, events):

    tree = {
        "top": top_event,
        "gate": "OR",
        "children": events
    }

    return tree