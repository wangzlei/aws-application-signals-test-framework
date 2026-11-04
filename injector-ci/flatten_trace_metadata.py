#!/usr/bin/env python3
"""Rewrite expected X-Ray trace templates for accounts with Transaction Search enabled.

With the trace segment destination set to CloudWatch Logs, X-Ray builds segments from spans and puts
span/resource attributes directly under "metadata" instead of the "metadata.default" namespace that the
expected-data templates assume. This lifts every "metadata": {"default": {...}} level up one level.
Usage: flatten_trace_metadata.py <template> [<template> ...]  (files are rewritten in place)
"""
import json
import sys


def flatten(node):
    if isinstance(node, list):
        return [flatten(n) for n in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        value = flatten(value)
        if key == "metadata" and isinstance(value, dict) and isinstance(value.get("default"), dict):
            merged = {k: v for k, v in value.items() if k != "default"}
            merged.update(value["default"])
            value = merged
        out[key] = value
    return out


for path in sys.argv[1:]:
    with open(path) as f:
        data = json.load(f)
    with open(path, "w") as f:
        json.dump(flatten(data), f, indent=2)
        f.write("\n")
    print(f"flattened {path}")
