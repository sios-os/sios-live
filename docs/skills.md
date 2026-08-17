# ANUBIS Skill Library

Generated: 2026-08-13 16:28
Total skills: 41

## binary_search v1

### `binary_search()`
  Perform binary search on a sorted list and return the index or -1.
  Parameters: lst, target

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `9978184faeed4acad84e3693c179f7e9...`

## bubble_sort v1

### `bubble_sort()`
  Sorts a list using bubble sort.
  Parameters: lst

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `7f03ab3c3e83bbc75f93ea23db619c75...`

## caesar_cipher v1

### `caesar_cipher()`
  Encode a string using a Caesar cipher with a given shift.
  Parameters: text, shift

  Model: qwen2.5-coder:7b
  Attempt: 3
  Hash: `a99111e6a71358301c1f5ee0c92059e8...`

## checks_if_a v4

### `checks_if_a()`
  Checks if a string is a palindrome.
  Parameters: s

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `c44a21d08faa5102a12368eb2786839b...`

## chunk_list v1

### `chunk_list()`
  Split a list into chunks of a given size. Return a list of lists. The last chunk may be smaller than size. If size <= 0, raise ValueError. Empty input list returns empty list.
  Parameters: lst, size

  Model: qwen2.5-coder:7b
  Attempt: 3
  Hash: `516c11032858479dcc39028cf3e0dbad...`

## count_vowels v1

### `count_vowels()`
  
    Count the number of vowels (a, e, i, o, u) in a string.
    
    Args:
        s (str): The input string to count vowels from.
    
    Returns:
        int: The total number of vowels found in the string.
    
  Parameters: s

  Model: llama3.1:8b
  Attempt: 1
  Hash: `306b9acae2e58011fb2788f8be7299a7...`

## count_words v1

### `count_words()`
  Count the number of words in a string.
  Parameters: s

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `b9c1eb769464296299ad7549712f23f3...`

## csv_parser v1

### `parse_csv_line()`
  Parse a CSV line handling quoted fields containing delimiters.
  Parameters: line, delimiter

### `strip_quotes()`
  Remove surrounding quotes from a field.
  Parameters: field

  Model: qwen2.5-coder:7b
  Attempt: 4
  Hash: `a23e04252c293182b28978e76d1c9404...`

## dedupe_preserving_order v1

### `dedupe_preserving_order()`
  
    Remove duplicates from an iterable while preserving the order of first appearance.
    
    This function uses a combination of hashability and slower comparison for unhashable elements.
    
    :param iterable: The input iterable to remove duplicates from
    :return: A new list with duplicates removed, preserving the order of first appearance
    
  Parameters: iterable

  Model: llama3.1:8b
  Attempt: 2
  Hash: `7d888e430b5d43f11d1e38fd2a8c90a7...`

## factorial v1

### `factorial()`
  Compute the factorial of a non-negative integer.
  Parameters: n

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `d7f16ead0c261993403c9f862ba9e465...`

## fibonacci v1

### `fibonacci()`
  Return the nth Fibonacci number.
  Parameters: n

  Model: qwen2.5-coder:7b
  Attempt: 2
  Hash: `7c82ca7eac809133573852001b5ae5d2...`

## flatten_list v1

### `flatten_list()`
  Flatten a nested list of arbitrary depth.
  Parameters: nested_list

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `8a59fa5a63e723c8b1e97b642f6a49d0...`

## gcd v1

### `gcd()`
  Compute the greatest common divisor of two numbers.
  Parameters: a, b

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `6ac99aa6573b48a94581067ddbfcd01b...`

## hex_to_rgb v1

### `hex_to_rgb()`
  Converts a hex color string to an RGB tuple.
  Parameters: hex_str

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `90c4e6f30a8918f70d1a115ae84b4081...`

## int_to_ip v1

### `int_to_ip()`
  Convert an integer to an IPv4 address string.
  Parameters: n

  Model: qwen2.5-coder:7b
  Attempt: 5
  Hash: `702db19029632da489113b276488075e...`

## ip_to_int v1

### `ip_to_int()`
  Convert an IPv4 address string to an integer.
  Parameters: ip

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `18bc1be5c357dbfe29bade10e4769a20...`

## is_anagram v1

### `is_anagram()`
  Check if two strings are anagrams of each other.
  Parameters: str1, str2

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `8fee147fa81bf966ae820e78c3e45a1c...`

## is_palindrome v1

### `is_palindrome()`
  Check if a string is a palindrome.
  Parameters: s

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `8694f547c66bb1f46efebfd2796af112...`

## is_prime v1

### `is_prime()`
  Check if a number is prime.
  Parameters: n

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `c712ee17faf7304c91662958e9a6fecb...`

## json_config v1

### `load_config()`
  Parse JSON string and return a dictionary.
  Parameters: json_str

### `get_value()`
  Safely get a nested value using dot notation (e.g. 'a.b.c').
  Parameters: config, key, default

### `merge_configs()`
  Deep-merge two dictionaries.
  Parameters: base, override

  Model: qwen2.5-coder:7b
  Attempt: 4
  Hash: `167c7b8080f5fbf1c387fcb17654bcfa...`

## matrix_transpose v1

### `matrix_transpose()`
  Transposes a 2D matrix.
  Parameters: matrix

  Model: qwen2.5-coder:7b
  Attempt: 2
  Hash: `e6eb6c5754d3dd0bd07b025f4db55dbd...`

## merge_sort v1

### `merge_sort()`
  Sorts a list using merge sort.
  Parameters: lst

### `merge()`
  Merges two sorted lists into one sorted list.
  Parameters: left, right

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `de46988f3691441c4835f68b60bbec50...`

## merge_sorted v1

### `merge_sorted()`
  Merge two sorted lists into one sorted list.
  Parameters: list1, list2

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `cdfefc6de24b8d7bf1b5e868ebd46934...`

## ordinal v1

### `ordinal()`
  Converts a number to its ordinal string.
  Parameters: n

  Model: qwen2.5-coder:7b
  Attempt: 2
  Hash: `5bc07432f1a9072c9513800a360f5ca8...`

## output_formatting v1

### `output_formatting()`
  Format word frequencies and unique words as JSON.
  Parameters: word_frequencies, unique_words

  Model: qwen2.5-coder:7b
  Attempt: 5
  Hash: `c526d9e4955e502be9316ab41b4af037...`

## parse_duration v1

### `parse_duration()`
  
    Parse a duration string like '2h30m', '45s', or '1h' into an integer number of seconds.
    
    Args:
        s (str): A duration string with h, m, and/or s units in any combination.
        
    Returns:
        int: The number of seconds represented by the input string.
        
    Raises:
        ValueError: If the input string is invalid.
    
  Parameters: s

  Model: llama3.1:8b
  Attempt: 2
  Hash: `2e86e3bb4449a0386e0c946034b5fde6...`

## pluralize v1

### `pluralize()`
  Return the plural of an English noun.
  Parameters: word

  Model: qwen2.5-coder:7b
  Attempt: 4
  Hash: `517a718fc84e46ad47137adef91c723c...`

## quick_sort v1

### `quick_sort()`
  Sorts a list using quicksort.
  Parameters: lst

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `233664ca7683a72e247fa7bcadfec85a...`

## reverse_string v1

### `reverse_string()`
  Reverses a string.
  Parameters: s

  Model: llama3.1:8b
  Attempt: 5
  Hash: `14656f6b773bfdb6ffb67c592137755a...`

## reverse_words v1

### `reverse_words()`
  Reverse the order of words in a sentence.
  Parameters: sentence

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `29ccdefe512a5be34e5ee211b4348bcf...`

## rgb_to_hex v1

### `rgb_to_hex()`
  Convert RGB values to a hex color string.
  Parameters: r, g, b

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `d7178aac91346eeed4fd5fd099c1c020...`

## roman_to_int v1

### `roman_to_int()`
  Converts a Roman numeral string to an integer.
  Parameters: s

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `d47790a55435326d14b818a09159d9f2...`

## rot13 v1

### `rot13()`
  Encode a string using ROT13 encoding.
  Parameters: text

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `f72dbba68ffab9e3bdbc93e0b8698f5a...`

## slugify v1

### `slugify()`
  Convert a string to a URL-safe slug: lowercase, replace any run of non-alphanumeric characters with a single hyphen, strip leading and trailing hyphens.
  Parameters: s

  Model: qwen2.5-coder:7b
  Attempt: 2
  Hash: `90f68afc0f16cfb440075885a94b0353...`

## stack_queue v1

### `stack_queue()`
  One-line docstring.

### `__init__()`
  Parameters: self

### `push()`
  Add an item to the top of the stack.
  Parameters: self, item

### `pop()`
  Remove the item from the top of the stack and return it.
  Parameters: self

### `peek()`
  Return the item at the top of the stack without removing it.
  Parameters: self

### `is_empty()`
  Check if the stack is empty.
  Parameters: self

### `__init__()`
  Parameters: self

### `enqueue()`
  Add an item to the end of the queue.
  Parameters: self, item

### `dequeue()`
  Remove the item from the front of the queue and return it.
  Parameters: self

### `front()`
  Return the item at the front of the queue without removing it.
  Parameters: self

### `is_empty()`
  Check if the queue is empty.
  Parameters: self

  Model: qwen2.5-coder:7b
  Attempt: 4
  Hash: `0f7379f02ea1436763fd30f8ebc64ca9...`

## string_compress v1

### `string_compress()`
  Compresses a string by replacing consecutive characters with the character followed by the count.
  Parameters: s

  Model: qwen2.5-coder:7b
  Attempt: 2
  Hash: `d0cc65a68f8cf3f49b315067a3250e9d...`

## sum_even_numbers v1

### `sum_even_numbers()`
  Sum all even numbers in a list of numbers.
  Parameters: numbers

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `21e9c6e53445dc555728f91190184f22...`

## title_case v1

### `title_case()`
  Converts a string to title case.
  Parameters: s

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `6014f2e72bee5d9bf9c62a4799b55b9a...`

## truncate v1

### `truncate()`
  Truncate text to a max length, adding an ellipsis if cut.
  Parameters: text, max_length

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `6320049d8c26d1d75ab6919e039aa0fd...`

## validate_email v1

### `validate_email()`
  Validate an email address format without using regex.
  Parameters: email

  Model: qwen2.5-coder:7b
  Attempt: 2
  Hash: `8e522d64580a09a0533f51ea45d541e5...`

## word_frequency v1

### `word_frequency()`
  Count the frequency of each lowercase word in a string, ignoring punctuation.
  Parameters: text

  Model: qwen2.5-coder:7b
  Attempt: 1
  Hash: `40c06832233e786f755ce3dc3c62edf7...`
