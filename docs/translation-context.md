# TranslationContext and Map Authoring

`TranslationContext` is the explicit per-run input object passed from your Airflow
task into the translation call and then into your mapping.

Use it for values that change from run to run. Do not use it for stable mapping
dependencies or long-lived configuration.

## The data model

`TranslationContext` currently has these fields:

- `frompartner: str`
- `topartner: str`
- `alt: str`
- `testindicator: str`
- `reference: str = "1"`
- `metadata: Mapping[str, Any]`
- `values: Mapping[str, Any]`
- `partners: Mapping[str, Mapping[str, Any]]`

Example:

```python
from bots_airflow import TranslationContext


context = TranslationContext(
    frompartner="LIVINGSPC",
    topartner="PLEASANTMA",
    reference="batch-001",
    metadata={
        "dag_run_id": "manual__2026-03-18T12:00:00+00:00",
        "source_key": "incoming/orders/file1.edi",
    },
    values={
        "customer_id": "900001",
        "po_number_source": "beg03",
    },
    partners={
        "LIVINGSPC": {"erp_id": "900001"},
        "PLEASANTMA": {"reference_number": "645"},
    },
)
```

## What each field is for

- `frompartner`: sender id for this run
- `topartner`: receiver id for this run
- `alt`: explicit alternate route or branch value
- `testindicator`: test or production indicator for this run
- `reference`: caller-supplied reference value; often used for logging or output `ta_info`
- `metadata`: upstream context you want to carry as a block
- `values`: key/value settings that your mapping reads directly
- `partners`: partner-field data keyed by partner id and can contain key:values referenced to the partner

## Common access patterns

These are the current direct access patterns:

- `context.frompartner` returns the single `frompartner` value passed in
- `context.topartner` returns the single `topartner` value passed in
- `context.value("some_key")` searches only `context.values`
- `context.required_value("some_key")` raises immediately if the key is missing
- `context.metadata.get("some_key")` searches only `context.metadata`
- `context.partner_value("from", "some_key")` reads from the partner record for `context.frompartner`
- `context.partner_value("to", "some_key")` reads from the partner record for `context.topartner`
- `context.required_partner_value("from", "some_key")` raises immediately if the partner field is missing

`context.partner_value(...)` also still accepts an explicit partner id:

```python
customer_id = context.partner_value("LIVINGSPC", "customer_id", "")
```

In practice:

- use `values` for settings that affect mapping logic
- use `metadata` for richer upstream payloads you want to inspect or forward
- use `partners` for partner attributes when you do not want a separate database lookup

## How the translator uses context

When you call `translator.translate(...)` or `translator.translate_text(...)`:

- a plain dict is coerced into `TranslationContext`
- `frompartner`, `topartner`, `alt`, `testindicator`, and `reference` are copied
  into the low-level translation request
- the full `TranslationContext` object is passed into your mapping as `context`

That means `context` affects both:

- runtime parse/write metadata
- your mapping logic

If you also pass `mapping_kwargs`, the translator injects `context` automatically
unless you already supplied a `context` key in `mapping_kwargs`.

## Recommended map signature

If you use `BaseMapping`, implement `translate(...)` like this:

```python
from bots_airflow.context import TranslationContext
from bots_airflow.mapping import BaseMapping


class OrdersToCsv(BaseMapping):
    def translate(self, inn, out, *, context: TranslationContext, **kwargs):
        prefix = str(context.value("order_prefix", ""))
        row_count = 0

        for item in inn.getloop({"BOTSID": "root"}):
            out.putloop(
                {
                    "BOTSID": "root",
                    "order_id": f"{prefix}{item.record.get('order_id', '')}",
                    "sku": item.record.get("sku", ""),
                    "quantity": str(item.record.get("quantity", "")),
                }
            )
            row_count += 1

        out.ta_info["reference"] = context.reference
        out.ta_info["botskey"] = str(row_count)
        return {"row_count": row_count}
```

That is the preferred map-authoring model in `bots_airflow`.

## Reading simple values

Use `context.value(key, default)` for run-specific settings:

```python
order_prefix = context.value("order_prefix", "")
customer_id = context.value("customer_id", "")
source_key = context.metadata.get("source_key", "")
```

If the value must exist, use `required_value(...)` to fail fast:

```python
customer_id = context.required_value("customer_id")
sender_name = context.required_value("sender_name", allow_blank=False)
```

This is the cleanest place for:

- feature flags
- per-run constants
- values produced by prior Airflow tasks
- partner-specific overrides decided before translation starts

## Reading partner data

Use `context.partner_value(partner_id, field, default)` when partner data is
already available in the context:

```python
customer_id = context.partner_value("from", "attr2", "")
```

The shortcut aliases currently supported are:

- `"from"` or `"frompartner"` for `context.frompartner`
- `"to"` or `"topartner"` for `context.topartner`

If the partner field must exist, use `required_partner_value(...)`:

```python
customer_id = context.required_partner_value("from", "customer_id")
erp_code = context.required_partner_value("to", "erp_code", allow_blank=False)
```

If you are using `BaseMapping`, prefer `self.partner_value(...)` when you want
service lookup fallback:

```python
customer_id = self.partner_value(
    context,
    "from",
    "attr2",
    default="",
)
```

`BaseMapping.partner_value(...)` checks:

1. injected `services.partner_lookup`, if one exists
2. `context.partners`, if the service did not return a usable value

That lets you support both:

- fully explicit Airflow-supplied partner data
- runtime service lookups for shared partner metadata

## Required-value helpers

`TranslationContext` now includes two fail-fast helpers for mapping code:

- `required_value(key, allow_blank=True)`
- `required_partner_value(partner_id, field, allow_blank=True)`

They are useful when a missing value should be treated as a mapping error instead
of silently becoming a blank output field.

Example:

```python
customer_id = context.required_value("customer_id")
ship_to_code = context.required_partner_value("to", "dc_code")
```

Set `allow_blank=False` if whitespace-only strings should also fail:

```python
sender_name = context.required_value("sender_name", allow_blank=False)
```

## Recommended fallback pattern

For many maps, the best pattern is:

1. check `context.values`
2. fall back to mapping options
3. fall back to parsed input data
4. raise a clear error if the value is still missing

Example:

```python
class ExampleMap(BaseMapping):
    def _setting(self, context: TranslationContext, key: str, default):
        value = context.value(key, None)
        if value is not None:
            return value
        return self.options.get(key, default)
```

This keeps per-run overrides explicit while still allowing reusable map defaults.

## What belongs in context vs options vs services

Use `TranslationContext` for:

- partner ids for this run
- routing decisions made upstream
- batch references
- object storage keys
- values computed by earlier Airflow tasks

Use mapping `options` for:

- stable map defaults
- behavior switches that do not change every run
- configuration shared across many runs

Use injected `services` for:

- partner lookup adapters
- code tables
- unique number generators
- persistence helpers

That split keeps maps deterministic and retry-safe.

## Module-based maps

You do not have to use `BaseMapping`. A module-level `main(...)` function can
also accept `context`:

```python
def main(inn, out, *, context, **kwargs):
    route = context.value("route", "")
    out.ta_info["reference"] = context.reference
    return {"route": route}
```

The same `TranslationContext` object is passed in.

## Common mistakes

Avoid these patterns:

- storing per-run values on `self` instead of using `context`
- mixing upstream task payloads into constructor options
- reading partner ids only from parsed `inn.ta_info` when the caller already
  supplied them in `context`
- hiding required inputs; raise a clear error if a needed context value is missing

## Practical rule

If a value changes from one DAG run to the next, it probably belongs in
`TranslationContext`.

If a value is stable across many runs of the same mapping, it probably belongs in
mapping `options` or an injected service.
