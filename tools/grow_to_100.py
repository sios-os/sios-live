#!/usr/bin/env python3
"""Grow skills to 100+ using the mission queue."""
import sys
sys.path.insert(0, ".")
from pathlib import Path
from anubis.queue import MissionQueue
from anubis.loop import SelfDevelopmentLoop
from anubis.model import OllamaAdapter
from anubis.skills import SkillLibrary
from anubis.ledger import Ledger
from anubis.sandbox import Sandbox, SandboxPolicy

ROOT = Path(".")
model = OllamaAdapter("qwen2.5-coder:7b", require_tools=False)
library = SkillLibrary(ROOT / "skills")
ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
sandbox = Sandbox(SandboxPolicy(timeout_s=30, memory_mb=512, cpu_seconds=20))
loop = SelfDevelopmentLoop(model, library, ledger, sandbox, max_attempts=3)
queue = MissionQueue(ROOT / "mission_queue")

# 60 missions to reach 100+ skills
MISSIONS = [
    ("is_perfect_number", "Write a function that checks if a number is a perfect number (sum of its proper divisors equals the number)"),
    ("fibonacci_sequence", "Write a function that returns the first n Fibonacci numbers as a list"),
    ("prime_factors", "Write a function that returns the prime factors of a number as a list"),
    ("decimal_to_binary", "Write a function that converts a decimal integer to its binary string representation"),
    ("binary_to_decimal", "Write a function that converts a binary string to a decimal integer"),
    ("decimal_to_hex", "Write a function that converts a decimal integer to a hexadecimal string"),
    ("hex_to_decimal", "Write a function that converts a hexadecimal string to a decimal integer"),
    ("is_leap_year", "Write a function that checks if a given year is a leap year"),
    ("days_in_month", "Write a function that returns the number of days in a given month and year"),
    ("date_to_day_of_year", "Write a function that converts a date (year, month, day) to the day of the year (1-366)"),
    ("day_of_year_to_date", "Write a function that converts a day of the year back to a date (year, month, day)"),
    ("weekday", "Write a function that returns the day of the week (0=Sunday) for a given date"),
    ("time_ago", "Write a function that formats a timestamp as a human-readable 'time ago' string (e.g., '3 hours ago')"),
    ("format_bytes", "Write a function that formats a byte count as a human-readable string (e.g., '1.5 KB', '2.3 MB')"),
    ("parse_bytes", "Write a function that parses a human-readable byte string (e.g., '1.5KB') into a byte count"),
    ("temperature_convert", "Write a function that converts between Celsius, Fahrenheit, and Kelvin given a value, from_unit, and to_unit"),
    ("distance_convert", "Write a function that converts between meters, kilometers, miles, and feet"),
    ("weight_convert", "Write a function that converts between kilograms, grams, pounds, and ounces"),
    ("string_to_list", "Write a function that splits a comma-separated string into a list of trimmed strings"),
    ("list_to_string", "Write a function that joins a list of items into a comma-separated string"),
    ("count_vowels_and_consonants", "Write a function that counts vowels and consonants in a string, returning both counts"),
    ("remove_punctuation", "Write a function that removes all punctuation from a string"),
    ("capitalize_words", "Write a function that capitalizes the first letter of each word in a string"),
    ("snake_to_camel", "Write a function that converts a snake_case string to camelCase"),
    ("camel_to_snake", "Write a function that converts a camelCase string to snake_case"),
    ("kebab_to_snake", "Write a function that converts a kebab-case string to snake_case"),
    ("snake_to_kebab", "Write a function that converts a snake_case string to kebab-case"),
    ("repeat_string", "Write a function that repeats a string n times with a separator"),
    ("pad_string", "Write a function that pads a string to a given length with a specified character on the left or right"),
    ("contains_substring", "Write a function that checks if a string contains a substring, case insensitive"),
    ("count_substring", "Write a function that counts the occurrences of a substring in a string"),
    ("replace_all", "Write a function that replaces all occurrences of a substring with another in a string"),
    ("split_by_delimiter", "Write a function that splits a string by a delimiter and returns a list"),
    ("join_with_delimiter", "Write a function that joins a list of strings with a delimiter"),
    ("max_in_list", "Write a function that returns the maximum value in a list of numbers"),
    ("min_in_list", "Write a function that returns the minimum value in a list of numbers"),
    ("sum_list", "Write a function that returns the sum of all numbers in a list"),
    ("average_list", "Write a function that returns the average of a list of numbers"),
    ("median_list", "Write a function that returns the median of a list of numbers"),
    ("mode_list", "Write a function that returns the most common value in a list"),
    ("range_list", "Write a function that returns the range (max - min) of a list of numbers"),
    ("variance", "Write a function that calculates the variance of a list of numbers"),
    ("std_deviation", "Write a function that calculates the standard deviation of a list of numbers"),
    ("percentile", "Write a function that calculates the nth percentile of a list of numbers"),
    ("quartiles", "Write a function that returns Q1, Q2, and Q3 of a list of numbers"),
    ("is_sorted", "Write a function that checks if a list is sorted in ascending order"),
    ("find_duplicates", "Write a function that returns a list of duplicate values in a list"),
    ("remove_nulls", "Write a function that removes None values from a list"),
    ("chunk_list_size", "Write a function that splits a list into chunks of a given size, returning a list of lists"),
    ("interleave_lists", "Write a function that interleaves two lists into one"),
    ("rotate_list", "Write a function that rotates a list by n positions (positive = right, negative = left)"),
    ("find_peak", "Write a function that finds a peak element in a list (an element greater than its neighbors)"),
    ("count_occurrences", "Write a function that counts occurrences of each element in a list and returns a dict"),
    ("deep_flatten", "Write a function that deeply flattens a nested list of any depth"),
    ("unique_preserve_order", "Write a function that removes duplicates from a list while preserving order"),
    ("zip_dicts", "Write a function that takes two lists and returns a dict mapping keys to values"),
    ("invert_dict", "Write a function that inverts a dictionary (keys become values and vice versa)"),
    ("merge_dicts", "Write a function that merges two dictionaries, with the second taking priority on conflicts"),
    ("dict_to_sorted_list", "Write a function that converts a dict to a list of (key, value) tuples sorted by key"),
    ("filter_dict_by_value", "Write a function that filters a dict to only entries where the value satisfies a predicate"),
]

existing = set(library.names())
new_missions = [(name, task) for name, task in MISSIONS if name not in existing]
print(f"Current skills: {len(existing)}")
print(f"New missions to queue: {len(new_missions)}")
print()

# Add to queue
ids = queue.add_batch(new_missions)
print(f"Queued {len(ids)} missions")
print()

# Process all
print("--- Processing missions ---")
promoted = 0
failed = 0
skipped = 0

for mission_name, mission_task in new_missions:
    if mission_name in existing:
        skipped += 1
        continue
    print(f"  {mission_name}...", end=" ", flush=True)
    result = loop.run_mission(mission_task, mission_name)
    if result.success:
        promoted += 1
        existing.add(mission_name)
        print(f"PROMOTED (v{result.skill.version})")
    else:
        failed += 1
        print(f"FAILED ({result.denied_reason or 'unknown'})")

print()
print(f"=== SUMMARY ===")
print(f"  Promoted: {promoted}")
print(f"  Failed: {failed}")
print(f"  Skipped: {skipped}")
print(f"  Total skills: {len(library.names())}")
