import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from tqdm import tqdm
import re
import json
import time
from urllib.parse import quote

class IconDownloader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 设置输出目录
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloaded_icons')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载域名映射
        self.domain_mappings = self.load_domain_mappings()

    def load_domain_mappings(self):
        """加载域名映射，优先使用外部文件"""
        # 首先尝试从程序目录加载
        exe_dir = os.path.dirname(os.path.abspath(__file__))
        external_json = os.path.join(exe_dir, 'domain_mappings.json')
        
        if os.path.exists(external_json):
            try:
                with open(external_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load external domain_mappings.json: {e}")
        
        # 如果外部文件不存在或加载失败，使用打包的资源
        try:
            import sys
            if getattr(sys, 'frozen', False):
                # 如果是打包后的程序
                base_path = sys._MEIPASS
            else:
                # 如果是开发环境
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            internal_json = os.path.join(base_path, 'domain_mappings.json')
            with open(internal_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error: Failed to load internal domain_mappings.json: {e}")
            return {}  # 返回空字典作为后备

    def create_default_mappings(self):
        """创建默认的域名映射文件"""
        default_mappings = {
            "微信": "weixin.qq.com",
            "支付宝": "alipay.com",
            "淘宝": "taobao.com",
            "京东": "jd.com",
            "抖音": "douyin.com",
            "快手": "kuaishou.com",
            "bilibili": "bilibili.com",
            "哔哩哔哩": "bilibili.com",
            "网易云音乐": "music.163.com",
            "QQ音乐": "y.qq.com",
            "喜马拉雅": "ximalaya.com",
            "知乎": "zhihu.com",
            "微博": "weibo.com",
            "百度": "baidu.com",
            "阿里巴巴": "alibaba.com",
            "腾讯": "qq.com",
            "美团": "meituan.com",
            "拼多多": "pinduoduo.com",
            "饿了么": "ele.me",
            "滴滴": "didichuxing.com",
            "谷歌": "google.com",
            "Google": "google.com",
            "google": "google.com"
        }
        
        # 保存到主映射文件
        with open(self.mappings_file, 'w', encoding='utf-8') as f:
            json.dump(default_mappings, f, ensure_ascii=False, indent=4)
            print("已创建默认映射文件")

    def add_domain_mapping(self, name, domain):
        """添加新的域名映射"""
        try:
            with open(self.mappings_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
        except FileNotFoundError:
            mappings = {}
            
        # 添加新映射
        mappings[name] = domain
        
        # 保存更新后的映射
        with open(self.mappings_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=4)
            
        # 更新内存中的映射
        self.brand_domains[name] = domain
        print(f"已添加映射: {name} -> {domain}")

    def get_all_categories(self):
        """获取所有可用的类别"""
        categories = []
        for filename in os.listdir(self.mappings_dir):
            if filename.endswith('.json'):
                categories.append(filename[:-5])
        return categories

    def translate_to_english(self, text):
        """将中文翻译为英文"""
        try:
            # 使用百度翻译API
            url = f"https://fanyi.baidu.com/sug"
            data = {
                "kw": text
            }
            response = requests.post(url, data=data, headers=self.headers, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('data') and len(result['data']) > 0:
                    return result['data'][0]['v'].split(';')[0].strip().lower()
            
            # 备用：使用有道翻译API
            url = f"http://fanyi.youdao.com/translate?&doctype=json&type=AUTO&i={quote(text)}"
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('translateResult') and len(result['translateResult']) > 0:
                    return result['translateResult'][0][0]['tgt'].lower()
            
            return text
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text

    def search_domain(self, name):
        """通过搜索引擎查找品牌官网"""
        try:
            # 首先检查已加载的域名映射
            print(f"正在检查域名映射... 当前已加载 {len(self.brand_domains)} 个映射")
            
            # 转换为小写进行匹配
            name_lower = name.lower()
            for key, value in self.brand_domains.items():
                if key.lower() == name_lower:
                    print(f"在映射中找到域名: {value}")
                    return value
            
            print(f"在映射中未找到域名: {name}")
            print(f"已加载的映射: {self.brand_domains}")
            
            # 常见中国网站的直接映射
            common_cn_sites = {
                "支付宝": "alipay.com",
                "百度": "baidu.com",
                "淘宝": "taobao.com",
                "京东": "jd.com",
                "微信": "weixin.qq.com",
                "微博": "weibo.com",
                "知乎": "zhihu.com",
                "抖音": "douyin.com",
                "哔哩哔哩": "bilibili.com",
                "网易": "163.com",
                "阿里巴巴": "alibaba.com",
                "腾讯": "qq.com",
                "谷歌": "google.com",
                "google": "google.com"
            }
            
            # 检查是否是常见网站（不区分大小写）
            for key, value in common_cn_sites.items():
                if key.lower() == name_lower:
                    return value
            
            # 如果是中文，先尝试翻译
            if re.search(r'[\u4e00-\u9fff]', name):
                english_name = self.translate_to_english(name)
            else:
                english_name = name
                
            # 构建多个搜索查询
            search_queries = [
                f"{name} 官网",
                f"{name} official website",
                f"{english_name} official website",
                f"{name} site:.com OR site:.cn",
                f"{english_name} site:.com OR site:.cn"
            ]
            
            all_results = []
            for query in search_queries:
                # 使用Bing搜索
                search_url = f"https://www.bing.com/search?q={quote(query)}"
                response = requests.get(search_url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找搜索结果中的链接
                    for cite in soup.find_all('cite'):
                        url = cite.get_text()
                        if url and self.is_valid_url(url):
                            try:
                                domain = self.extract_domain(url)
                                if domain and self.is_valid_domain(domain, name, english_name):
                                    all_results.append((domain, self.calculate_domain_score(domain, name, english_name)))
                            except:
                                continue
                    
                    # 如果没有找到结果，尝试其他链接
                    if not all_results:
                        for link in soup.find_all('a'):
                            href = link.get('href', '')
                            if href and self.is_valid_url(href):
                                try:
                                    domain = self.extract_domain(href)
                                    if domain and self.is_valid_domain(domain, name, english_name):
                                        all_results.append((domain, self.calculate_domain_score(domain, name, english_name)))
                                except:
                                    continue
                
                time.sleep(1)  # 添加延时避免请求过快
            
            # 选择得分最高的域名
            if all_results:
                all_results.sort(key=lambda x: x[1], reverse=True)
                return all_results[0][0]
            
            return None
        except Exception as e:
            print(f"Error searching domain for {name}: {str(e)}")
            return None

    def is_valid_url(self, url):
        """验证URL是否有效"""
        excluded_patterns = [
            'bing.com', 'google.com', 'baidu.com/s?', 
            'advertisement', 'click', 'redirect',
            'search?', 'microsoft.com', '.gov', 
            'wikipedia.org', 'zhihu.com/question'
        ]
        return not any(pattern in url.lower() for pattern in excluded_patterns)

    def extract_domain(self, url):
        """从URL中提取域名"""
        url = url.lower().strip()
        url = url.replace('https://', '').replace('http://', '').replace('www.', '')
        return url.split('/')[0]

    def is_valid_domain(self, domain, name, english_name):
        """验证域名是否有效"""
        domain_lower = domain.lower()
        name_lower = name.lower()
        english_name_lower = english_name.lower()
        
        # 排除无效域名
        excluded_domains = [
            'bing.com', 'google.com', 'baidu.com/s', 
            'advertisement', 'ad.', '.gov', 'search',
            'wikipedia.org', 'zhihu.com/question'
        ]
        if any(x in domain_lower for x in excluded_domains):
            return False
            
        # 检查域名是否包含品牌名称（原名或英文名）
        name_parts = set(re.split(r'[\s\-_]', name_lower) + re.split(r'[\s\-_]', english_name_lower))
        domain_parts = set(re.split(r'[\s\-_\.]', domain_lower))
        
        # 允许的顶级域名
        valid_tlds = ('.com', '.cn', '.net', '.org', '.com.cn')
        return bool(name_parts & domain_parts) and any(domain_lower.endswith(tld) for tld in valid_tlds)

    def calculate_domain_score(self, domain, name, english_name):
        """计算域名匹配得分"""
        score = 0
        domain_lower = domain.lower()
        name_lower = name.lower()
        english_name_lower = english_name.lower()
        
        # 域名完全匹配得分最高
        if domain_lower in [f"{name_lower}.com", f"{name_lower}.cn", f"{english_name_lower}.com", f"{english_name_lower}.cn"]:
            score += 10
        
        # 域名包含完整名称
        if name_lower in domain_lower or english_name_lower in domain_lower:
            score += 5
            
        # 域名包含名称的一部分
        name_parts = set(re.split(r'[\s\-_]', name_lower) + re.split(r'[\s\-_]', english_name_lower))
        domain_parts = set(re.split(r'[\s\-_\.]', domain_lower))
        matching_parts = name_parts & domain_parts
        score += len(matching_parts) * 2
        
        # 域名长度越短越可能是官网
        score += 10.0 / len(domain)
        
        # 优先选择常见顶级域名
        if domain_lower.endswith('.com.cn'):
            score += 4
        elif domain_lower.endswith('.com'):
            score += 3
        elif domain_lower.endswith('.cn'):
            score += 2
        elif domain_lower.endswith('.net'):
            score += 1
            
        return score

    def get_domain_from_name(self, name):
        """从品牌名称获取域名"""
        name = name.strip()
        
        # 如果输入的是域名格式，直接返回
        if '.' in name:
            if not name.startswith(('http://', 'https://')):
                name = name.replace('https://', '').replace('http://', '')
            return name.split('/')[0]
        
        # 通过搜索引擎查找域名
        domain = self.search_domain(name)
        return domain

    def download_google_favicon(self, domain, size=256):
        """从Google Favicon服务下载图标"""
        try:
            url = f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                filename = f"{self.clean_filename(domain)}_google_{size}.png"
                filepath = os.path.join(self.output_dir, filename)
                
                # 保存原始图片
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # 调整图片大小
                img = Image.open(filepath)
                if img.size != (size, size):
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    img.save(filepath, "PNG")
                
                return filepath
            return None
        except Exception as e:
            print(f"Error downloading Google favicon for {domain}: {str(e)}")
            return None

    def download_direct_favicon(self, domain):
        """直接从网站下载favicon，尝试获取最大尺寸"""
        try:
            # 常见的图标路径
            common_icon_paths = [
                "/favicon.ico",
                "/favicon.png",
                "/apple-touch-icon.png",
                "/apple-touch-icon-precomposed.png",
                "/apple-touch-icon-120x120.png",
                "/apple-touch-icon-152x152.png",
                "/apple-touch-icon-180x180.png",
                "/icon.png",
                "/logo.png",
                "/touch-icon-iphone.png"
            ]
            
            urls_to_try = [
                f"https://{domain}",
                f"https://www.{domain}",
                f"http://{domain}",
                f"http://www.{domain}"
            ]
            
            # 首先尝试直接访问常见的图标路径
            for base_url in [f"https://{domain}", f"https://www.{domain}"]:
                for path in common_icon_paths:
                    try:
                        icon_url = base_url + path
                        print(f"尝试下载图标: {icon_url}")
                        response = requests.get(icon_url, headers=self.headers, timeout=5)
                        if response.status_code == 200:
                            try:
                                img = Image.open(BytesIO(response.content))
                                if max(img.size) >= 32:  # 确保图标足够大
                                    filename = f"{self.clean_filename(domain)}_direct_{max(img.size)}.png"
                                    filepath = os.path.join(self.output_dir, filename)
                                    img.save(filepath, "PNG")
                                    print(f"成功从 {icon_url} 下载图标")
                                    return filepath
                            except:
                                continue
                    except:
                        continue
            
            # 如果直接访问失败，尝试从HTML中查找图标链接
            response = None
            for url in urls_to_try:
                try:
                    print(f"尝试访问网站: {url}")
                    response = requests.get(url, headers=self.headers, timeout=5)
                    if response.status_code == 200:
                        break
                except Exception as e:
                    print(f"访问 {url} 失败: {str(e)}")
                    continue
                    
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找所有可能的图标链接
                icon_links = []
                for link in soup.find_all('link'):
                    rel = link.get('rel', [])
                    if isinstance(rel, str):
                        rel = [rel]
                    if any(r.lower() in ['icon', 'shortcut icon', 'apple-touch-icon', 'apple-touch-icon-precomposed', 'fluid-icon', 'mask-icon'] for r in rel):
                        href = link.get('href')
                        if href:
                            # 尝试从href中提取尺寸信息
                            size_match = re.search(r'(\d+)x(\d+)', href)
                            if size_match:
                                size = int(size_match.group(1))
                            else:
                                size = 0
                            icon_links.append((href, size))

                # 按尺寸排序图标链接
                icon_links.sort(key=lambda x: x[1], reverse=True)
                
                best_icon = None
                best_size = 0
                
                for link, size in icon_links:
                    try:
                        if link.startswith('//'):
                            link = f"https:{link}"
                        elif link.startswith('/'):
                            link = f"https://{domain}{link}"
                        elif not link.startswith(('http://', 'https://')):
                            link = f"https://{domain}/{link}"

                        print(f"尝试下载图标: {link}")
                        icon_response = requests.get(link, headers=self.headers, timeout=5)
                        if icon_response.status_code == 200:
                            img = Image.open(BytesIO(icon_response.content))
                            actual_size = max(img.size)
                            if actual_size > best_size and actual_size >= 32:  # 确保图标足够大
                                best_size = actual_size
                                best_icon = (link, icon_response.content, actual_size)
                                print(f"找到更大的图标: {link} ({actual_size}x{actual_size})")
                    except Exception as e:
                        print(f"下载图标 {link} 失败: {str(e)}")
                        continue

                if best_icon:
                    filename = f"{self.clean_filename(domain)}_direct_{best_icon[2]}.png"
                    filepath = os.path.join(self.output_dir, filename)
                    
                    try:
                        # 保存并调整图片大小
                        img = Image.open(BytesIO(best_icon[1]))
                        target_size = max(img.size)  # 使用最大的边长作为目标尺寸
                        if img.size != (target_size, target_size):
                            img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                        img.save(filepath, "PNG")
                        print(f"成功保存图标: {filepath}")
                        return filepath
                    except Exception as e:
                        print(f"保存图标失败: {str(e)}")
                        return None

            return None
        except Exception as e:
            print(f"Error downloading direct favicon for {domain}: {str(e)}")
            return None

    def download_icon_from_services(self, domain, size=256):
        """从多个图标服务下载图标"""
        services = [
            {
                'name': 'Google Favicon',
                'url': f"https://www.google.com/s2/favicons?domain={domain}&sz={size}",
                'type': 'direct'
            },
            {
                'name': 'DuckDuckGo',
                'url': f"https://icons.duckduckgo.com/ip3/{domain}.ico",
                'type': 'direct'
            },
            {
                'name': 'Yandex',
                'url': f"https://favicon.yandex.net/favicon/{domain}",
                'type': 'direct'
            },
            {
                'name': 'ico.kucat.cn',
                'url': f"https://ico.kucat.cn/get.php?url={domain}",
                'type': 'direct'
            }
        ]
        
        results = []
        for service in services:
            try:
                print(f"尝试从 {service['name']} 下载图标...")
                response = requests.get(service['url'], headers=self.headers, timeout=10)
                if response.status_code == 200:
                    try:
                        img = Image.open(BytesIO(response.content))
                        
                        # 确保图标不是空的且尺寸合适
                        if max(img.size) >= 16:  # 确保图标不是空的
                            # 获取原始尺寸
                            original_size = max(img.size)
                            
                            # 如果原始尺寸大于目标尺寸，保持原始尺寸
                            target_size = max(size, original_size)
                            
                            # 转换为RGBA模式以保持透明度
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')
                            
                            # 调整图片大小（如果需要）
                            if img.size != (target_size, target_size):
                                img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                            
                            # 在文件名中使用实际尺寸
                            filename = f"{self.clean_filename(domain)}_{service['name']}_{target_size}.png"
                            filepath = os.path.join(self.output_dir, filename)
                            
                            # 保存图片
                            img.save(filepath, "PNG")
                            
                            print(f"从 {service['name']} 成功下载图标，实际尺寸: {target_size}x{target_size}")
                            results.append({
                                'service': service['name'],
                                'filepath': filepath,
                                'size': target_size
                            })
                    except Exception as e:
                        print(f"处理 {service['name']} 图标时出错: {str(e)}")
            except Exception as e:
                print(f"从 {service['name']} 下载失败: {str(e)}")
                continue
        
        return results

    def download_icons(self, names_or_domains):
        """下载多个名称或域名的图标"""
        results = []
        for name in tqdm(names_or_domains, desc="Downloading icons"):
            domain = self.get_domain_from_name(name)
            if not domain:
                results.append({
                    'name': name,
                    'domain': None,
                    'error': '未找到对应的域名',
                    'icons': []
                })
                continue

            # 添加延时避免请求过快
            time.sleep(1)
            
            # 从各个服务下载图标
            service_results = self.download_icon_from_services(domain)
            
            # 尝试直接从网站下载
            direct_result = self.download_direct_favicon(domain)
            if direct_result:
                service_results.append({
                    'service': '直接下载',
                    'filepath': direct_result,
                    'size': 0  # 这里可以读取实际文件获取尺寸
                })
            
            results.append({
                'name': name,
                'domain': domain,
                'icons': service_results
            })
        return results

    def clean_filename(self, filename):
        """清理文件名，移除非法字符"""
        return re.sub(r'[<>:"/\\|?*]', '', filename)

def main():
    downloader = IconDownloader()
    print("欢迎使用图标下载器！")
    print("请输入要下载图标的名称或域名（多个名称或域名用逗号分隔）")
    print("支持的品牌包括：微信、支付宝、淘宝、京东、抖音、bilibili等")
    
    user_input = input("请输入名称或域名: ")
    names_or_domains = [name.strip() for name in user_input.split(',')]
    
    results = downloader.download_icons(names_or_domains)
    
    print("\n下载结果:")
    for result in results:
        print(f"\n名称或域名: {result['name']}")
        if result['domain']:
            print(f"域名: {result['domain']}")
            if result['icons']:
                print("下载的图标:")
                for icon in result['icons']:
                    print(f"- 从 {icon['service']} 下载的图标已保存至: {icon['filepath']}")
            else:
                print("未能下载到任何图标")
        else:
            print(f"错误: {result['error']}")

if __name__ == "__main__":
    main() 