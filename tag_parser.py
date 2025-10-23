"""
Unified Tag Parser for PowerPoint Generator
============================================
Centralized tag parsing logic used by AI generator, previewer, and presentation builder
"""

import re


def normalize_tags(text):
    """
    Convert ALL tag formats to the standard closed-tag format: [tag]content[/tag]
    
    Handles:
    1. Open-only tags: [emphasis] word → [emphasis]word...[/emphasis]
    2. Tags with spaces: [emphasis] content [/emphasis] → [emphasis]content[/emphasis]
    3. Already-closed tags: [emphasis]word[/emphasis] → unchanged
    4. Step tags: [step] content → content (removed entirely)
    
    This function matches the behavior of clean_ai_output() in ai_content_generator.py
    """
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Handle [step] tags - remove them entirely
    text = re.sub(r'\[step\]\s*', '', text, flags=re.IGNORECASE)
    
    # TWO-PASS TAG NORMALIZATION (matches ai_content_generator.py)
    
    # Pass 1: Remove extra spaces inside tags: [tag] content [/tag] → [tag]content[/tag]
    for tag in ['vocabulary', 'question', 'answer', 'emphasis']:
        text = re.sub(rf'\[{tag}\]\s+', rf'[{tag}]', text, flags=re.IGNORECASE)
        text = re.sub(rf'\s+\[/{tag}\]', rf'[/{tag}]', text, flags=re.IGNORECASE)
    
    # Pass 2: Close unclosed tags
    # Capture everything until end of string or next tag/marker
    for tag in ['vocabulary', 'question', 'answer', 'emphasis']:
        # Match [tag] followed by content, but not already closed
        # Capture until: end of string, newline, or another opening tag
        pattern = rf'\[{tag}\]([^\[\]]+?)(?=$|\n|\[(?:vocabulary|question|answer|emphasis|step|/{tag}))'
        
        def replace_func(match):
            content = match.group(1).strip()
            # Check if already has closing tag
            if not content.endswith(f'[/{tag}]'):
                return f'[{tag}]{content}[/{tag}]'
            return match.group(0)
        
        text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
    
    return text


def parse_inline_tags(text):
    """
    Parse text with inline tags and return list of (content, style) tuples.
    
    Args:
        text: String that may contain [tag]content[/tag] markers
        
    Returns:
        List of tuples: [(content, style_name), ...]
        where style_name is one of: 'vocabulary', 'question', 'answer', 'emphasis', or None
        
    Example:
        "I [emphasis]really[/emphasis] like this" 
        Ã¢â€ â€™ [("I ", None), ("really", "emphasis"), (" like this", None)]
    """
    # First normalize all tags to closed format
    text = normalize_tags(text)
    
    # Pattern to match [tag]content[/tag]
    pattern = r'\[(vocabulary|question|answer|emphasis)\](.*?)\[/\1\]'
    
    segments = []
    last_idx = 0
    
    for match in re.finditer(pattern, text, re.IGNORECASE):
        # Add any text before the tag
        if match.start() > last_idx:
            segments.append((text[last_idx:match.start()], None))
        
        # Add the tagged content with its style
        tag_name = match.group(1).lower()
        content = match.group(2)
        segments.append((content, tag_name))
        
        last_idx = match.end()
    
    # Add any remaining text after the last tag
    if last_idx < len(text):
        segments.append((text[last_idx:], None))
    
    # If no segments were created, return the whole text with no style
    if not segments:
        return [(text, None)]
    
    return segments


def strip_all_tags(text):
    """
    Remove all tag markers from text, leaving only the content.
    
    Args:
        text: String that may contain tags
        
    Returns:
        Clean text with all tags removed
        
    Example:
        "I [emphasis]really[/emphasis] like this" Ã¢â€ â€™ "I really like this"
    """
    text = normalize_tags(text)
    
    # Remove all closed tags
    text = re.sub(
        r'\[(vocabulary|question|answer|emphasis)\](.*?)\[/\1\]',
        r'\2',
        text,
        flags=re.IGNORECASE
    )
    
    # Remove any remaining open tags (shouldn't exist after normalization, but just in case)
    text = re.sub(
        r'\[(vocabulary|question|answer|emphasis|step)\]',
        '',
        text,
        flags=re.IGNORECASE
    )
    
    # Remove any remaining close tags
    text = re.sub(
        r'\[/(vocabulary|question|answer|emphasis)\]',
        '',
        text,
        flags=re.IGNORECASE
    )
    
    return text.strip()


def has_inline_tags(text):
    """
    Check if text contains any inline style tags.
    
    Returns:
        Boolean indicating presence of tags
    """
    text = normalize_tags(text)
    return bool(re.search(
        r'\[(vocabulary|question|answer|emphasis)\].*?\[/\1\]',
        text,
        re.IGNORECASE
    ))


def validate_tags(text):
    """
    Validate that all tags are properly closed.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for unclosed tags (after normalization, there shouldn't be any open tags without close tags)
    open_tags = re.findall(r'\[(vocabulary|question|answer|emphasis)\](?![^\[]*\[/\1\])', text, re.IGNORECASE)
    if open_tags:
        errors.append(f"Unclosed tags found: {', '.join(set(open_tags))}")
    
    # Check for close tags without open tags
    close_tags = re.findall(r'\[/(vocabulary|question|answer|emphasis)\]', text, re.IGNORECASE)
    open_tags_all = re.findall(r'\[(vocabulary|question|answer|emphasis)\]', text, re.IGNORECASE)
    
    if len(close_tags) > len(open_tags_all):
        errors.append("More closing tags than opening tags")
    
    # Check for mismatched tags like [emphasis]...[/vocabulary]
    for match in re.finditer(r'\[(vocabulary|question|answer|emphasis)\](.*?)\[/(\w+)\]', text, re.IGNORECASE):
        open_tag = match.group(1).lower()
        close_tag = match.group(3).lower()
        if open_tag != close_tag:
            errors.append(f"Mismatched tags: [{open_tag}]...[/{close_tag}]")
    
    return len(errors) == 0, errors


# Test function for debugging
def test_tag_parser():
    """Test cases for tag parser"""
    test_cases = [
        # (input, expected_segments)
        ("I [emphasis]worked[/emphasis] yesterday", [("I ", None), ("worked", "emphasis"), (" yesterday", None)]),
        ("I [emphasis] worked yesterday", [("I ", None), ("worked", "emphasis"), (" yesterday", None)]),  # Now only styles one word
        ("[vocabulary]resilient[/vocabulary]", [("resilient", "vocabulary")]),
        ("[vocabulary] resilient", [("resilient", "vocabulary")]),
        ("No tags here", [("No tags here", None)]),
        ("[step] First point", [("First point", None)]),
        ("[emphasis] word [emphasis]", [("word", "emphasis")]),
        ("Multiple [emphasis]bold[/emphasis] and [vocabulary]term[/vocabulary] tags", 
         [("Multiple ", None), ("bold", "emphasis"), (" and ", None), ("term", "vocabulary"), (" tags", None)]),
    ]
    
    print("Testing Tag Parser")
    print("=" * 60)
    
    for input_text, expected in test_cases:
        result = parse_inline_tags(input_text)
        passed = result == expected
        status = "Ã¢Å“â€¦ PASS" if passed else "Ã¢ÂÅ’ FAIL"
        
        print(f"\n{status}")
        print(f"Input:    {repr(input_text)}")
        print(f"Expected: {expected}")
        print(f"Got:      {result}")
        
        # Also test normalization
        normalized = normalize_tags(input_text)
        print(f"Normalized: {repr(normalized)}")
    
    print("\n" + "=" * 60)
    print("Tag validation tests:")
    
    validation_tests = [
        ("I [emphasis]worked[/emphasis]", True),
        ("I [emphasis]worked", False),  # Unclosed
        ("I worked[/emphasis]", False),  # No opening
        ("[emphasis]one[/emphasis] and [vocabulary]two[/vocabulary]", True),
    ]
    
    for text, should_be_valid in validation_tests:
        is_valid, errors = validate_tags(text)
        passed = is_valid == should_be_valid
        status = "Ã¢Å“â€¦ PASS" if passed else "Ã¢ÂÅ’ FAIL"
        print(f"{status} {repr(text)}: valid={is_valid}, errors={errors}")


if __name__ == "__main__":
    test_tag_parser()