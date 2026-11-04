#!/usr/bin/env python3
"""Rewrite expected X-Ray trace templates for accounts with Transaction Search enabled.

With the trace segment destination set to CloudWatch Logs, X-Ray builds segments from spans and puts
span/resource attributes directly under "metadata" instead of the "metadata.default" namespace that the
expected-data templates assume. This lifts every "metadata": {"default": {...}} level up one level, drops the "otel.resource." prefix of
resource attributes and moves "aws.span.kind" to aws["span.kind"], as span-derived segments do.
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
        if key == "metadata" and isinstance(value, dict):
            renamed = {}
            for k, v in value.items():
                if k == "aws.span.kind":
                    # span-derived segments carry it as aws["span.kind"]
                    aws = out.setdefault("aws", {}) if "aws" not in node else out.setdefault("aws", flatten(node["aws"]))
                    aws["span.kind"] = v
                    continue
                if k.startswith("otel.resource."):
                    # resource attributes keep their plain names
                    k = k[len("otel.resource."):]
                renamed[k] = v
            value = renamed
            if not value:
                continue  # nothing left to compare; an empty object would be compared as a leaf
        if key == "aws" and isinstance(out.get("aws"), dict) and isinstance(value, dict):
            out["aws"].update(value)
            continue
        out[key] = value
    return out


for path in sys.argv[1:]:
    with open(path) as f:
        data = json.load(f)
    with open(path, "w") as f:
        json.dump(flatten(data), f, indent=2)
        f.write("\n")
    print(f"flattened {path}")
