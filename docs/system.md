# SIOS System Architecture

Generated: 2026-08-13 16:28

## Overview

SIOS (Sovereign Interactive Operating System) is a local-first
Linux environment with ANUBIS as its intelligence. Everything
runs locally — no cloud, no external services.

## Components

### Knowledge Library
- Documents: 550
- Directors: 14
- Specialties: 268

### Skill Library
- Promoted skills: 41
- Skills: binary_search, bubble_sort, caesar_cipher, checks_if_a, chunk_list, count_vowels, count_words, csv_parser, dedupe_preserving_order, factorial, fibonacci, flatten_list, gcd, hex_to_rgb, int_to_ip, ip_to_int, is_anagram, is_palindrome, is_prime, json_config, matrix_transpose, merge_sort, merge_sorted, ordinal, output_formatting, parse_duration, pluralize, quick_sort, reverse_string, reverse_words, rgb_to_hex, roman_to_int, rot13, slugify, stack_queue, string_compress, sum_even_numbers, title_case, truncate, validate_email, word_frequency

### Evidence Ledger
- Entries: 371
- Integrity: verified

### Governance
- 8 immutable laws
- 5 change classes (routine, sandboxed, promotion, consequential, main engine)
- Court reviews main engine changes
- Policy engine enforces spending limits

### Architecture
- Base: Ubuntu 24.04
- Desktop: Godot 4 spatial environment (13 rooms)
- Model: Ollama local server (qwen2.5-coder:7b)
- Embeddings: nomic-embed-text (768-dim)
- IPC: Unix socket at /tmp/anubis.sock
- Sandbox: unshare + mount namespace, network blocked
