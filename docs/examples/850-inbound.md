# Example: 850 Inbound to SSCC CSV

This example converts a Living Spaces 850 purchase order into an SSCC CSV file.

Relevant modules:

- input grammar: `bots_airflow.grammar.livingspaces.x12_in`
- output grammar: `bots_airflow.grammar.osas.sscc_out`
- mapping: `bots_airflow.mappings.x12.ls_to_osas_sscc.LivingSpacesToOsasSscc`

Example:

```python
from pathlib import Path

from bots_airflow import TranslationContext, init
from bots_airflow.grammar.livingspaces import x12_in
from bots_airflow.grammar.osas import sscc_out
from bots_airflow.mappings.x12.ls_to_osas_sscc import LivingSpacesToOsasSscc

translator = init(
    grammar_in=x12_in,
    grammar_out=sscc_out,
    map=LivingSpacesToOsasSscc,
)

translator.translate(
    Path("examples/fixtures/sample_850.edi"),
    Path("/tmp/sscc.csv"),
    context=TranslationContext(
        frompartner="DEMORETAIL",
        topartner="DEMOFULFILL",
        partners={
            "DEMORETAIL": {"attr2": "900001"},
        },
    ),
)
```

Context values can override the default mapping behavior. Useful examples:

- `customer_id`
- `customer_id_partner_field`
- `po_number`
- `po_number_source`
- `po_number_placeholder`
- `item_id_qualifier`
- `customer_part_qualifier`
- `serial_qualifier`

This lets Airflow provide business decisions directly instead of storing them in Bots partner tables.
