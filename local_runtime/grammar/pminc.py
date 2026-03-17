from bots_airflow.specs import GrammarSpec

json_out = GrammarSpec(
    editype='jsonnocheck',
    messagetype='jsonnocheck',
    module='local_runtime.grammars.json.jsonnocheck',
    charset='utf-8',
)
