from gen_website import gen_web_open
from sys_mangment import gen_sys_monitering, gen_os_mangment
import re
import sys
import joblib

_model = joblib.load('models/tool_model.joblib')
print('tool model loaded')
def excute_tool(user_input: str, **kwargs):
    tool_id = _model.predict([user_input])[0]
    print(f'predicted tool id {tool_id}')

    tools = {
        "tool_002": lambda: gen_web_open(user_input).main(),
        "tool_003": lambda: gen_sys_monitering.ram_usage(),
        "tool_004": lambda: gen_sys_monitering.cpu_usage(),
        "tool_005": lambda: gen_sys_monitering.gen_sys_analysis(),
        "tool_006": lambda: gen_os_mangment.gen_shutdown(),
        "tool_007": lambda: gen_os_mangment.gen_restart(),
    }

    func = tools.get(tool_id)
    if func is None:
        print(f'invalid tool id by model: {tool_id}')
        return None

    return func()
