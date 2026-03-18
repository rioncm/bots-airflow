# Translation Execution

This page describes what happens when you call `Translator.translate(...)` or
`Translator.translate_text(...)`, what gets written, what comes back on success,
and how to handle failures in Airflow code.

## Two entry points

Use `translate_text(...)` when your input is already in memory:

```python
result = translator.translate_text(
    input_text,
    filename="input.edi",
    output_filename="output.csv",
    context=context,
)
```

Use `translate(...)` when you want `bots_airflow` to read an input file and write
the final output file for you:

```python
result = translator.translate(
    "input.edi",
    "output.csv",
    context=context,
)
```

Both methods return a `TranslationResult` on success.

## What the runtime does

For each translation call, `bots_airflow` currently performs these steps:

1. Initialize the extracted runtime.
2. Create a temporary task directory under the runtime root.
3. Write the input text to a temporary input file inside that task directory.
4. Parse the input using `from_editype` and `from_messagetype`.
5. Split the parsed interchange into messages and require exactly one message.
6. Create the outbound message using `to_editype` and `to_messagetype`.
7. Call your mapping with `inn`, `out`, and the injected `context`.
8. If the mapping marks the outbound message as `DONE`, stop without writing output.
9. Otherwise serialize the outbound message and return the result.

This package is direct parse/map/write execution. It does not use Bots routes,
channels, or the translate table.

## What gets written

Every translation currently writes temporary runtime files, even when you use
`translate_text(...)`.

On every call:

- the input text is written to `TranslationResult.input_path`
- a temporary task directory is created at `TranslationResult.task_dir`
- serialized output is written to a temporary output file unless the mapping marks
  the run as `DONE`

When you call `translate(...)`:

- `bots_airflow` also writes the final output text to the `output_path` argument
  you passed in

One important detail: `TranslationResult.output_path` points to the temporary
runtime output file, not the final path you passed to `translate(...)`.

## Success result fields

On success, the return object includes:

- `runtime`: runtime path information returned by the bootstrap layer
- `task_dir`: the temporary working directory for this translation
- `input_path`: the temporary input file path
- `output_path`: the temporary serialized output path, or `None`
- `output_text`: the serialized output text, or `None`
- `mapping_result`: whatever your mapping returned
- `ta_info`: the final outbound `ta_info` dictionary

Typical things callers read from the result are:

- `result.output_text` for the serialized payload
- `result.mapping_result` for map-specific counters or metadata
- `result.ta_info["reference"]` or `result.ta_info["botskey"]` for logging

## Output behavior

The output behavior depends on what your mapping does.

Normal case:

- your mapping populates `out`
- `bots_airflow` serializes the outbound message
- `result.output_text` contains the payload
- `result.output_path` points to the temporary runtime file
- `translate(...)` also writes the payload to the caller's requested output path

No-output case:

- your mapping sets `out.ta_info["statust"] = DONE`
- `result.output_path` is `None`
- `result.output_text` is `None`
- `translate(...)` does not create the caller's output file

Example no-output map pattern:

```python
from botscore.constants import DONE


def main(inn, out, **kwargs):
    if should_skip(inn):
        out.ta_info["statust"] = DONE
        return {"skipped": True}
```

## Failure model

`bots_airflow` does not currently convert failures into a structured error result.
If parsing, mapping resolution, mapping execution, or file writing fails, the
exception is raised to the caller.

Common failure points include:

- invalid or missing grammar references
- mapping import errors
- parser validation errors from the inbound message
- multiple split messages in one call
- exceptions raised by your mapping
- file read or write errors in `translate(...)`

If a failure occurs, you do not get a `TranslationResult`.

## Error capture in Airflow code

If you want structured error reporting, wrap the translation call yourself:

```python
import traceback


def run_translation(translator, input_path, output_path, context):
    try:
        result = translator.translate(
            input_path,
            output_path,
            context=context,
        )
        return {
            "ok": True,
            "reference": result.ta_info.get("reference", ""),
            "output_text": result.output_text,
            "mapping_result": result.mapping_result,
        }
    except Exception as exc:
        error_payload = {
            "ok": False,
            "reference": context.reference,
            "frompartner": context.frompartner,
            "topartner": context.topartner,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        # log, persist, or push this to XCom here
        raise
```

That is the current place to do:

- user-facing error messages
- structured logging
- retry decisions
- dead-letter storage
- alert payload generation

## Recommended caller pattern

For most DAGs, treat `bots_airflow` as a translation primitive:

- pass explicit grammars, mapping, and context in
- read `output_text`, `mapping_result`, and `ta_info` on success
- catch exceptions outside the translator
- handle cleanup, retries, and reporting in Airflow or your application code

If you need retention rules for temporary task directories, implement that outside
the translation call as well. The current runtime creates temp working files but
does not expose a cleanup API on `TranslationResult`.
