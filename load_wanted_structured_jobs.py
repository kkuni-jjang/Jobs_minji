import json

# 파일 경로
file_path = r"data/wanted_structured_jobs_20250709_010849.json"

# JSON 파일 불러오기
def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_tech_stack_null(data):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == 'tech_stack' and isinstance(v, str) and v.lower() == 'null':
                data[k] = None
            else:
                convert_tech_stack_null(v)
    elif isinstance(data, list):
        for item in data:
            convert_tech_stack_null(item)

if __name__ == "__main__":
    data = load_json(file_path)
    convert_tech_stack_null(data)
    print(data) 

print('hello')
