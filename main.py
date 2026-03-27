import flet as ft
from datetime import datetime
import json
import os

def main(page: ft.Page):
    page.title = "智能笔记"
    
    # --- 1. 绝对安全的路径逻辑 ---
    if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
        # 使用 Flet 专门为安卓提供的持久化目录
        data_dir = os.environ.get("FLET_APP_STORAGE_DATA", "/tmp")
        # 尝试使用 pwa_storage_path 作为备选
        if not os.path.exists(data_dir):
            data_dir = page.pwa_storage_path if page.pwa_storage_path else "."
        DB_FILE = os.path.join(data_dir, "my_app_data.json")
    else:
        DB_FILE = "my_app_data.json"

    # --- 2. 稳健的数据加载 ---
    def load_data():
        default_data = {
            "categories": ["默认分类", "工作", "灵感"], 
            "logs_data": {"默认分类": [], "工作": [], "灵感": []}
        }
        try:
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    # 确保数据格式完整
                    if "categories" in content and "logs_data" in content:
                        return content
        except Exception as e:
            print(f"读取数据失败: {e}")
        return default_data

    def save_data():
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump({"categories": categories, "logs_data": logs_data}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # 如果保存失败，弹出提示而不是闪退
            page.snack_bar = ft.SnackBar(ft.Text(f"保存失败: {e}"))
            page.snack_bar.open = True
            page.update()

    # 初始化变量（确保顺序正确）
    data = load_data()
    categories = data.get("categories", ["默认分类"])
    logs_data = data.get("logs_data", {categories[0]: []})
    
    current_category = ft.Ref[str]()
    current_category.current = categories[0]

    # UI 控件定义
    log_list = ft.ListView(expand=True, spacing=10)
    title_text = ft.Text(f"目录：{current_category.current}", size=22, weight="bold")
    
    # 详情、搜索等对话框逻辑保持原样，但一定要放在 page.overlay 中
    # (由于篇幅限制，此处省略你原有的详细 UI 代码，但请确保在你的文件里保留它们)
    
    # --- 3. 界面刷新逻辑 ---
    def refresh_ui():
        title_text.value = f"目录：{current_category.current}"
        log_list.controls.clear()
        items = logs_data.get(current_category.current, [])
        for index, item in enumerate(items):
            # 这里调用你原有的 create_item_card
            log_list.controls.append(create_item_card(item, index, current_category.current))
        page.update()

    # 简化的项目卡片创建（用于排查白屏）
    def create_item_card(item, index, cat_name):
        return ft.Card(
            content=ft.ListTile(
                title=ft.Text(item['content']),
                subtitle=ft.Text(f"{item['created_at']}"),
                on_click=lambda _: open_detail(item)
            )
        )
    
    # 详情弹窗逻辑（必须有，否则 open_detail 会报错）
    detail_content_text = ft.Text(size=18, selectable=True)
    detail_time_text = ft.Text(size=12)
    detail_dialog = ft.AlertDialog(
        title=ft.Text("内容详情"),
        content=ft.Column([detail_time_text, detail_content_text], tight=True),
        actions=[ft.TextButton("关闭", on_click=lambda _: setattr(detail_dialog, "open", False) or page.update())]
    )
    
    def open_detail(item):
        detail_content_text.value = item['content']
        detail_time_text.value = f"时间: {item['created_at']}"
        detail_dialog.open = True
        page.update()

    # 页面组装
    page.overlay.append(detail_dialog)
    
    new_in = ft.TextField(label="输入内容...", expand=True)
    def add_click(e):
        if not new_in.value: return
        if current_category.current not in logs_data:
            logs_data[current_category.current] = []
        logs_data[current_category.current].insert(0, {
            "content": new_in.value,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        new_in.value = ""
        save_data()
        refresh_ui()

    page.add(
        title_text, 
        ft.Row([new_in, ft.FloatingActionButton(icon=ft.icons.ADD, on_click=add_click)]), 
        ft.Divider(),
        log_list
    )
    refresh_ui()

# 最后启动
ft.app(target=main)
