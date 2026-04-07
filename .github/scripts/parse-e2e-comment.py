#!/usr/bin/env python3
"""Parse a /run-e2e PR comment and output validated test configurations as JSON.

Input schema (names, types, defaults, choice options) is read dynamically from
the ui-e2e.yaml workflow file so this script never needs updating when inputs change.
"""

import json
import os
import re
import sys
import yaml

MAX_ENTRIES = 10

WORKFLOW_PATH = os.path.join(
    os.path.dirname(__file__), "..", "workflows", "ui-e2e.yaml"
)


def load_input_schema(workflow_path):
    """Read ui-e2e.yaml and extract the workflow_dispatch input definitions.

    Returns a dict keyed by input name with fields: type, default, options (for choice).
    """
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)

    # PyYAML parses the YAML key `on` as boolean True
    on_section = workflow.get(True) or workflow.get("on") or {}
    inputs = on_section.get("workflow_dispatch", {}).get("inputs", {})
    schema = {}
    for name, spec in inputs.items():
        input_type = spec.get("type", "string")
        schema[name] = {
            "type": input_type,
            "default": spec.get("default"),
            "required": spec.get("required", False),
        }
        if input_type == "choice":
            schema[name]["options"] = spec.get("options", [])

    return schema


def extract_yaml_block(comment_body):
    """Extract YAML content from a fenced code block in the comment."""
    match = re.search(r"```ya?ml\s*\n(.*?)```", comment_body, re.DOTALL)
    if not match:
        return None
    return match.group(1)


def validate_entry(entry, index, schema):
    """Validate a single test configuration entry. Returns (validated_dict, errors)."""
    errors = []

    if not isinstance(entry, dict):
        return None, [], [f"Entry {index + 1}: expected a mapping, got {type(entry).__name__}"]

    unknown_keys = set(entry.keys()) - set(schema.keys())
    if unknown_keys:
        errors.append(f"Entry {index + 1}: unknown keys: {', '.join(sorted(unknown_keys))}")

    # Start with defaults from the workflow file
    validated = {}
    user_keys = set()
    for name, spec in schema.items():
        if spec["default"] is not None:
            validated[name] = spec["default"]

    for key in entry:
        if key not in schema:
            continue

        value = entry[key]
        spec = schema[key]

        if spec["type"] == "boolean":
            if isinstance(value, bool):
                validated[key] = value
                user_keys.add(key)
            elif isinstance(value, str) and value.lower() in ("true", "false"):
                validated[key] = value.lower() == "true"
                user_keys.add(key)
            else:
                errors.append(
                    f"Entry {index + 1}: '{key}' must be true or false, got '{value}'"
                )
        elif spec["type"] == "choice":
            str_value = str(value)
            if str_value not in spec["options"]:
                errors.append(
                    f"Entry {index + 1}: '{key}' must be one of: "
                    f"{', '.join(spec['options'])}"
                )
            else:
                validated[key] = str_value
                user_keys.add(key)
        else:
            validated[key] = str(value)
            user_keys.add(key)

    # Check required fields are present
    for name, spec in schema.items():
        if spec["required"] and name not in validated:
            errors.append(
                f"Entry {index + 1}: required field '{name}' is missing and has no default"
            )

    return validated, sorted(user_keys), errors


def parse_comment(comment_body, schema):
    """Parse the comment body and return (configs, user_keys_list, errors)."""
    yaml_content = extract_yaml_block(comment_body)
    if yaml_content is None:
        return None, [], ["No YAML code block found in comment."]

    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return None, [], [f"Invalid YAML: {e}"]

    if not isinstance(data, list):
        return None, [], ["YAML content must be a list of test configurations."]

    if len(data) > MAX_ENTRIES:
        return None, [], [f"Too many entries ({len(data)}). Maximum is {MAX_ENTRIES}."]

    if len(data) == 0:
        return None, [], ["YAML list is empty."]

    all_configs = []
    all_user_keys = []
    all_errors = []

    for i, entry in enumerate(data):
        config, user_keys, errors = validate_entry(entry, i, schema)
        all_errors.extend(errors)
        if config:
            all_configs.append(config)
            all_user_keys.append(user_keys)

    if all_errors:
        return None, [], all_errors

    return all_configs, all_user_keys, []


def main():
    schema = load_input_schema(WORKFLOW_PATH)

    comment_body = sys.stdin.read()
    configs, all_user_keys, errors = parse_comment(comment_body, schema)

    if errors:
        output = {"success": False, "errors": errors}
        print(json.dumps(output))
        sys.exit(1)

    # Convert booleans to strings for workflow_dispatch inputs (GitHub API expects strings)
    for config in configs:
        for key, value in config.items():
            if isinstance(value, bool):
                config[key] = str(value).lower()

    # Build user_overrides: only the keys explicitly provided by the user
    user_overrides = []
    for config, keys in zip(configs, all_user_keys):
        user_overrides.append({k: config[k] for k in keys})

    output = {"success": True, "configs": configs, "user_overrides": user_overrides}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
