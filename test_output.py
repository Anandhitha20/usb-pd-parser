import json

# Read first 3 lines and check the content
with open('usb_pd_spec.jsonl', 'r', encoding='utf-8') as f:
    for i in range(3):
        line = f.readline().strip()
        if line:
            data = json.loads(line)
            print(f"Section {i+1}:")
            print(f"  ID: {data['section_id']}")
            print(f"  Title: {data['title'][:80]}...")
            print(f"  Page: {data['page']}")
            print()
