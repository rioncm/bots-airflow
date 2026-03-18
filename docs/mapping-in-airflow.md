# Mapping in Airflow

This page focuses only on the overlap between Airflow and mapping authoring.

The main pattern is simple:

1. an Airflow task decides run-specific values
2. those values are passed into `TranslationContext`
3. the mapping reads them
4. the mapping writes them into the output payload or `ta_info`
5. the task reads `TranslationResult` for downstream decisions

## The boundary

In an Airflow-based flow:

- Airflow should decide which file to process, which partners are involved, and
  what run-specific values apply
- the mapping should turn parsed input plus context values into output records
- the task should handle retries, branching, alerts, and persistence

That means a map is usually not the place to:

- open storage clients
- call external APIs
- fetch Airflow Variables directly
- decide task retries

Those belong in the DAG or task code. The mapping should receive the values it
needs explicitly.

## Basic Airflow pattern

An Airflow task usually creates `TranslationContext` from upstream task results
or DAG parameters:

```python
from bots_airflow import TranslationContext, init


translator = init(
    grammar_in=grammar_in,
    grammar_out=grammar_out,
    map=OrdersToCsv,
)

result = translator.translate_text(
    input_text,
    context=TranslationContext(
        frompartner="WEBSTORE",
        topartner="FULFILLMENT",
        reference="batch-001",
        metadata={
            "dag_run_id": dag_run_id,
            "source_key": source_key,
        },
        values={
            "order_prefix": "WEB-",
        },
    ),
)
```

The mapping then receives that context object automatically.

## Example: context value used in output

This is the clearest Airflow-to-mapping example.

Airflow supplies a run-specific prefix:

```python
context = TranslationContext(
    values={"order_prefix": "WEB-"},
)
```

The mapping uses that value when building the outbound record:

```python
from bots_airflow.context import TranslationContext
from bots_airflow.mapping import BaseMapping


class OrdersToCsv(BaseMapping):
    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        order_prefix = str(context.value("order_prefix", ""))

        for item in inn.getloop({"BOTSID": "root"}):
            out.putloop(
                {
                    "BOTSID": "root",
                    "order_id": f"{order_prefix}{item.record.get('order_id', '')}",
                    "sku": item.record.get("sku", ""),
                    "quantity": str(item.record.get("quantity", "")),
                }
            )
```

If the inbound record contains `order_id = 1001`, the outbound row becomes:

```text
WEB-1001,SKU-001,2
```

That is the core Airflow overlap: Airflow decides the prefix, the mapping places
it into the translated output.

## Example: multiple context values shaping X12 output

The same pattern works for outbound EDI segments.

Airflow supplies values:

```python
context = TranslationContext(
    reference="inv-20260318-01",
    values={
        "sender_name": "Pleasant Mattress",
        "reference_prefix": "run-",
        "as_of_date": "20260318",
    },
)
```

The mapping writes those values into the outbound message:

```python
class InventoryJsonTo846(BaseMapping):
    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        sender_name = context.value("sender_name", "Pleasant Mattress")
        reference_prefix = context.value("reference_prefix", "ref-")
        as_of_date = context.value("as_of_date", "20260318")

        out.put({"BOTSID": "ST"}, {
            "BOTSID": "BIA",
            "BIA03": f"{reference_prefix}000001",
            "BIA04": as_of_date,
        })

        n1loop = out.putloop({"BOTSID": "ST"}, {"BOTSID": "N1"})
        n1loop.put({
            "BOTSID": "N1",
            "N101": "SU",
            "N102": sender_name,
            "N103": "92",
            "N104": "ASSIGNED_ID",
        })
```

Here the Airflow task controls:

- the BIA reference prefix
- the effective date
- the outbound sender name

without hard-coding those values inside the mapping.

## Example: partner-scoped values from context

If Airflow already knows partner-specific fields, pass them in `context.partners`
and let the mapping read them.

Airflow:

```python
context = TranslationContext(
    frompartner="LIVINGSPC",
    partners={
        "LIVINGSPC": {
            "customer_id": "900001",
            "dc_code": "0645",
        },
    },
)
```

Mapping:

```python
customer_id = context.partner_value(context.frompartner, "customer_id", "")
dc_code = context.partner_value(context.frompartner, "dc_code", "")
```

Those values can then be written into outbound CSV columns, JSON fields, or EDI
segments.

## Returning useful data to Airflow

The mapping does not only write the payload. It can also return structured data
for the task to use downstream.

Example mapping return:

```python
return {
    "row_count": row_count,
    "customer_id": customer_id,
}
```

Then the task can read:

```python
result = translator.translate_text(input_text, context=context)
print(result.mapping_result["row_count"])
```

This is useful for:

- branching decisions
- audit logging
- XCom payloads
- downstream file naming

## Using `ta_info` for run metadata

Mappings can also write values to `out.ta_info`:

```python
out.ta_info["reference"] = context.reference
out.ta_info["botskey"] = customer_id
out.ta_info["divtext"] = "inventory_export"
```

Then Airflow can read them from the result:

```python
result = translator.translate_text(input_text, context=context)
reference = result.ta_info.get("reference", "")
```

This is a good fit for:

- human-readable references
- identifiers you want in logs
- lightweight summary metadata

## Practical guidance

Good Airflow inputs for mappings:

- prefixes and suffixes
- dates chosen upstream
- partner ids
- customer ids
- routing decisions
- object storage keys
- batch references

Less suitable mapping inputs:

- live database connections
- storage clients
- retry counters
- scheduler state
- alerting logic

If the value is decided per DAG run, it usually belongs in `TranslationContext`.

## Related pages

- [TranslationContext and Map Authoring](translation-context.md)
- [Translation Execution](translation-execution.md)
- [Runtime Modules](runtime-modules.md)
