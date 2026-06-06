import sys
import os
sys.path.append(os.path.abspath("src"))

from contentforge.creative_manager.prompt_interpreter import PromptInterpreter

def test_parse(raw_text):
    interpreter = PromptInterpreter()
    
    parsed = interpreter._extract_json_object(raw_text)
    if not parsed:
        parsed_arr = interpreter._extract_json_array(raw_text)
        if parsed_arr:
            parsed = {"days": parsed_arr}
        else:
            return None

    days_raw = parsed.get("days", [])
    
    if not isinstance(days_raw, list) or not days_raw:
        for key in ["content_series", "series", "plan", "posts", "schedule", "weekly_plan", "items"]:
            val = parsed.get(key)
            if isinstance(val, list) and val:
                days_raw = val
                break

    # NEW FALLBACK: Check if parsed dict is a day itself
    if (not isinstance(days_raw, list) or not days_raw) and isinstance(parsed, dict):
        # If the top level contains day-like fields, wrap it
        day_keys = ["hook", "caption", "cta", "key_points", "talking_points"]
        if "title" in parsed and any(k in parsed for k in day_keys):
            days_raw = [parsed]

    # Fallback 2: Search for list of dicts
    if not isinstance(days_raw, list) or not days_raw:
        for val in parsed.values():
            if isinstance(val, list) and val and all(isinstance(x, dict) for x in val):
                days_raw = val
                break

    print(f"Parsed days count: {len(days_raw) if isinstance(days_raw, list) else 'Not a list'}")
    if isinstance(days_raw, list) and days_raw:
        print(f"Day 1 keys: {list(days_raw[0].keys())}")

def main():
    # Test 1: Single day JSON directly at root
    single_day_json = """
    {
      "day_number": 1,
      "title": "Google releases Gemini 1.5",
      "hook": "New model alert!",
      "key_points": ["Point 1", "Point 2"],
      "slide_outline": [
        {"slide_number": 1, "slide_title": "Cover"}
      ],
      "caption": "Check this out!",
      "cta": "Follow for more"
    }
    """
    print("Testing single day JSON directly at root:")
    test_parse(single_day_json)

if __name__ == "__main__":
    main()
