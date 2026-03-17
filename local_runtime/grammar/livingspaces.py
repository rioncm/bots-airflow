from bots_airflow.specs import GrammarSpec

x12_in = GrammarSpec(
    editype='x12',
    messagetype='x12',
    charset='utf-8',
    module='local_runtime.grammars.x12.x12',
    support_modules={
        '846_4010_living_spaces': 'local_runtime.grammars.x12._846_4010_living_spaces',
        '850_ls_inbound4010': 'local_runtime.grammars.x12._850_ls_inbound4010',
    },
)


x12_846_out = GrammarSpec(
    editype='x12',
    messagetype='846_4010_living_spaces',
    charset='utf-8',
    module='local_runtime.grammars.x12._846_4010_living_spaces',
    support_modules={
        'x12': 'local_runtime.grammars.x12.x12',
    },
)
