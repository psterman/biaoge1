import os
import json

def merge_json_files():
    # 获取所有JSON文件
    json_dir = "domain_mappings"
    merged_mappings = {}
    
    # 遍历目录中的所有JSON文件
    for filename in os.listdir(json_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(json_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 合并映射
                    merged_mappings.update(data)
            except Exception as e:
                print(f"Error reading {filename}: {str(e)}")
    
    # 按键排序
    sorted_mappings = dict(sorted(merged_mappings.items()))
    
    # 保存合并后的文件
    with open("domain_mappings.json", 'w', encoding='utf-8') as f:
        json.dump(sorted_mappings, f, ensure_ascii=False, indent=4)
    
    print(f"合并完成！共有 {len(sorted_mappings)} 个域名映射")

if __name__ == "__main__":
    merge_json_files() 