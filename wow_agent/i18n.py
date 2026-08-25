# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""轻量双语支持：tr(中文文案, 英文文案) 按当前语言返回；默认英文。
/language 命令切换，WOW_LANGUAGE 持久化到 ~/.wow-agent.env。"""

LANG = "en"


def set_lang(lang):
    """设置语言，返回是否成功；非法值忽略。"""
    global LANG
    if lang in ("en", "zh"):
        LANG = lang
        return True
    return False


def tr(zh, en):
    return zh if LANG == "zh" else en
