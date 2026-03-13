# Example: Inventory JSON to 846

This example converts inventory JSON into a Living Spaces 846 transaction.

Relevant modules:

- input grammar: `bots_airflow.grammar.osas.inventory_json_in`
- output grammar: `bots_airflow.grammar.livingspaces.x12_846_out`
- mapping: `bots_airflow.mappings.json.inventory_to_livingspaces_846.InventoryJsonToLivingSpaces846`

Example:

```python
from pathlib import Path

from bots_airflow import TranslationContext, init
from bots_airflow.grammar.osas import inventory_json_in
from bots_airflow.grammar.livingspaces import x12_846_out
from bots_airflow.mappings.json.inventory_to_livingspaces_846 import InventoryJsonToLivingSpaces846

translator = init(
    grammar_in=inventory_json_in,
    grammar_out=x12_846_out,
    map=InventoryJsonToLivingSpaces846,
)

translator.translate(
    Path("examples/fixtures/sample_inventory_846.json"),
    Path("/tmp/inventory_846.edi"),
    context=TranslationContext(
        values={
            "icn": "123456",
            "as_of_date": "20260313",
        },
    ),
)
```

Important context values:

- `icn`
- `as_of_date`
- `sender_name`
- `sender_id_code`
- `open_qty`
- `qty_qualifier`
- `date_qualifier`
- `reference_prefix`

If `icn` is not provided, the mapping can use an injected `unique_value` service instead.
