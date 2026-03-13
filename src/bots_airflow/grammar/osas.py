from bots_airflow.specs import GrammarSpec


inventory_json_in = GrammarSpec(
    editype='json',
    messagetype='inventory_846_json',
    charset='utf-8',
    module='bots_airflow.grammars.json.inventory_846_json',
)


sscc_out = GrammarSpec(
    editype='csv',
    messagetype='850_ls_to_osas_sscc',
    charset='utf-8',
    module='bots_airflow.grammars.csv._850_ls_to_osas_sscc',
)
