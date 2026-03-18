#!/usr/bin/env python3
"""Inspect available diagrams library classes for AWS, Azure, GCP."""
import sys

# AWS modules
print("=== AWS NETWORK ===")
import diagrams.aws.network as n
print(sorted([x for x in dir(n) if not x.startswith('_')]))

print("\n=== AWS SECURITY ===")
import diagrams.aws.security as s
print(sorted([x for x in dir(s) if not x.startswith('_')]))

print("\n=== AWS COMPUTE ===")
import diagrams.aws.compute as c
print(sorted([x for x in dir(c) if not x.startswith('_')]))

print("\n=== AWS STORAGE ===")
import diagrams.aws.storage as st
print(sorted([x for x in dir(st) if not x.startswith('_')]))

print("\n=== AWS DATABASE ===")
import diagrams.aws.database as db
print(sorted([x for x in dir(db) if not x.startswith('_')]))

print("\n=== AWS INTEGRATION ===")
import diagrams.aws.integration as ai
print(sorted([x for x in dir(ai) if not x.startswith('_')]))

print("\n=== AWS MANAGEMENT ===")
import diagrams.aws.management as m
print(sorted([x for x in dir(m) if not x.startswith('_')]))

print("\n=== AWS ANALYTICS ===")
import diagrams.aws.analytics as a
print(sorted([x for x in dir(a) if not x.startswith('_')]))

print("\n=== AWS ML ===")
import diagrams.aws.ml as ml
print(sorted([x for x in dir(ml) if not x.startswith('_')]))

# Azure modules
print("\n=== AZURE NETWORK ===")
import diagrams.azure.network as azn
print(sorted([x for x in dir(azn) if not x.startswith('_')]))

print("\n=== AZURE STORAGE ===")
import diagrams.azure.storage as azst
print(sorted([x for x in dir(azst) if not x.startswith('_')]))

print("\n=== AZURE DATABASE ===")
import diagrams.azure.database as azdb
print(sorted([x for x in dir(azdb) if not x.startswith('_')]))

print("\n=== AZURE COMPUTE ===")
import diagrams.azure.compute as azc
print(sorted([x for x in dir(azc) if not x.startswith('_')]))

print("\n=== AZURE INTEGRATION ===")
import diagrams.azure.integration as azi
print(sorted([x for x in dir(azi) if not x.startswith('_')]))

print("\n=== AZURE IDENTITY ===")
import diagrams.azure.identity as azid
print(sorted([x for x in dir(azid) if not x.startswith('_')]))

print("\n=== AZURE WEB ===")
import diagrams.azure.web as azweb
print(sorted([x for x in dir(azweb) if not x.startswith('_')]))

# GCP modules
print("\n=== GCP COMPUTE ===")
import diagrams.gcp.compute as gc
print(sorted([x for x in dir(gc) if not x.startswith('_')]))

print("\n=== GCP NETWORK ===")
import diagrams.gcp.network as gn
print(sorted([x for x in dir(gn) if not x.startswith('_')]))

print("\n=== GCP STORAGE ===")
import diagrams.gcp.storage as gs
print(sorted([x for x in dir(gs) if not x.startswith('_')]))

print("\n=== GCP DATABASE ===")
import diagrams.gcp.database as gdb
print(sorted([x for x in dir(gdb) if not x.startswith('_')]))

print("\n=== GCP ANALYTICS ===")
import diagrams.gcp.analytics as ga
print(sorted([x for x in dir(ga) if not x.startswith('_')]))

print("\n=== GCP ML ===")
import diagrams.gcp.ml as gml
print(sorted([x for x in dir(gml) if not x.startswith('_')]))

print("\n=== GCP DEVTOOLS ===")
import diagrams.gcp.devtools as gdt
print(sorted([x for x in dir(gdt) if not x.startswith('_')]))
