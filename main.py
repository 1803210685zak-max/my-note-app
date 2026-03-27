# _*_ coding : utf-8 _*_
# @Time : 2026/3/26 23:06
# @Author : 康
# @File : main
# @Project : python
# -*- coding : utf-8 -*-
import flet as ft
from datetime import datetime
import json
import os

def main(page: ft.Page):
    page.title = "智能笔记"
    
    # --- 终极路径修复方案 ---
    # 我们直接尝试使用 page.client_storage 这种更安全的沙盒路径
    if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
        # 在安卓上，获取一个绝对安全的私有目录
        # 如果 pwa_storage_path 不行，就降级使用当前目录，但在安卓通常需要这个：
        data_path = os.environ.get("FLET_APP_STORAGE_DATA", ".")
        DB_FILE = os.path.join(data_path, "my_app_data.json")
    else:
        DB_FILE = "my_app_data.json"

    # 添加一个简单的错误捕获，防止白屏
    def load_data():
        try:
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            # 如果读取失败，至少让 App 能跑起来
            print(f"Read error: {e}")
        return {"categories": ["默认分类", "工作"], "logs_data": {"默认分类": [], "工作": []}}
    # --- 1. 安卓路径适配逻辑 ---
    # 在手机上，直接使用相对路径可能无法写入，我们需要获取 App 的私有存储目录
    if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
        data_dir = page.client_storage.get("data_path")
        # 如果是第一次运行，我们设定一个文件名
        DB_FILE = os.path.join(page.pwa_storage_path if page.pwa_storage_path else ".", "my_app_data.json")
    else:
        # 电脑端保持原样
        DB_FILE = "my_app_data.json"

    # --- 2. 数据持久化 ---
    def load_data():
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"categories": ["默认分类", "工作", "灵感"], "logs_data": {"默认分类": [], "工作": [], "灵感": []}}

    def save_data():
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump({"categories": categories, "logs_data": logs_data}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存失败: {e}")

    data = load_data()
    categories = data["categories"]
    logs_data = data["logs_data"]
    current_category = ft.Ref[str]()
    current_category.current = categories[0]

    log_list = ft.ListView(expand=True, spacing=10)
    title_text = ft.Text(f"目录：{current_category.current}", size=22, weight="bold")

    # --- 3. 详情展示逻辑 ---
    detail_content_text = ft.Text(size=18, selectable=True)
    detail_time_text = ft.Text(size=12, color=ft.colors.GREY_700)

    def open_detail(item):
        detail_content_text.value = item['content']
        time_str = f"创建: {item['created_at']}"
        if item.get('updated_at'): time_str += f" | 修改: {item['updated_at']}"
        detail_time_text.value = time_str
        detail_dialog.open = True
        page.update()

    detail_dialog = ft.AlertDialog(
        title=ft.Text("内容详情"),
        content=ft.Container(
            content=ft.Column([detail_time_text, ft.Divider(), detail_content_text], scroll=ft.ScrollMode.AUTO,
                              tight=True), width=400),
        actions=[ft.TextButton("关闭", on_click=lambda _: setattr(detail_dialog, "open", False) or page.update())]
    )

    # --- 4. 界面渲染逻辑 ---
    def refresh_ui():
        title_text.value = f"目录：{current_category.current}"
        log_list.controls.clear()
        items = logs_data.get(current_category.current, [])
        for index, item in enumerate(items):
            log_list.controls.append(create_item_card(item, index, current_category.current))
        page.update()

    def create_item_card(item, index, cat_name):
        display_content = item['content'] if len(item['content']) < 35 else item['content'][:35] + "..."
        return ft.Card(
            content=ft.ListTile(
                title=ft.Text(display_content),
                subtitle=ft.Text(f"{item['created_at']}", size=10),
                on_click=lambda _: open_detail(item),
                trailing=ft.Row([
                    ft.IconButton(ft.icons.EDIT_NOTE, on_click=lambda _: open_edit_log_dialog(index, cat_name)),
                    ft.IconButton(ft.icons.DELETE_OUTLINE, icon_color="red",
                                  on_click=lambda _: open_delete_log_dialog(index, cat_name)),
                ], tight=True)
            )
        )

    # --- 5. 侧边栏目录管理 ---
    def refresh_drawer():
        my_drawer.controls.clear()
        my_drawer.controls.append(ft.Container(content=ft.Text("我的目录", size=20, weight="bold"), padding=20))
        my_drawer.controls.append(ft.Divider())

        for cat in categories:
            my_drawer.controls.append(ft.NavigationDrawerDestination(icon=ft.icons.FOLDER, label=cat))
            my_drawer.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.TextButton("改名", icon=ft.icons.EDIT,
                                      on_click=lambda e, c=cat: open_rename_category_dialog(c)),
                        ft.TextButton("删除", icon=ft.icons.DELETE_FOREVER, icon_color="red",
                                      on_click=lambda e, c=cat: check_delete_category(c)) if len(
                            categories) > 1 else ft.Container()
                    ]), padding=ft.padding.only(left=20, bottom=5)
                )
            )

        new_cat_input = ft.TextField(label="新目录名", height=45)

        def add_cat(e):
            if new_cat_input.value and new_cat_input.value not in categories:
                categories.append(new_cat_input.value)
                logs_data[new_cat_input.value] = []
                save_data();
                refresh_drawer();
                page.update()
            new_cat_input.value = ""

        my_drawer.controls.extend([
            ft.Divider(),
            ft.Container(content=ft.Column([new_cat_input, ft.ElevatedButton("创建", on_click=add_cat)]), padding=20)
        ])
        page.update()

    # 目录重命名
    ren_cat_field = ft.TextField(label="新名字")
    target_cat_ref = ft.Ref[str]()

    def do_ren_cat(e):
        old, new = target_cat_ref.current, ren_cat_field.value
        if new and new not in categories:
            categories[categories.index(old)] = new
            logs_data[new] = logs_data.pop(old)
            if current_category.current == old: current_category.current = new
            save_data();
            ren_cat_dialog.open = False;
            refresh_drawer();
            refresh_ui()

    ren_cat_dialog = ft.AlertDialog(title=ft.Text("改名"), content=ren_cat_field,
                                    actions=[ft.ElevatedButton("提交", on_click=do_ren_cat)])

    def open_rename_category_dialog(cat_name):
        target_cat_ref.current = cat_name
        ren_cat_field.value = cat_name
        ren_cat_dialog.open = True;
        page.update()

    # --- 6. 搜索功能 ---
    s_field = ft.TextField(label="搜索关键词...", autofocus=True)
    s_mode = ft.RadioGroup(content=ft.Row([ft.Radio(value="c", label="本目录"), ft.Radio(value="a", label="全局")]),
                           value="c")

    def run_s(e):
        kw = s_field.value.lower().strip()
        if not kw: return
        results = []
        scope = logs_data.items() if s_mode.value == "a" else [
            (current_category.current, logs_data[current_category.current])]
        for c, items in scope:
            for i, item in enumerate(items):
                if kw in item['content'].lower(): results.append({"item": item, "cat": c, "idx": i})
        log_list.controls.clear()
        title_text.value = f"结果: {len(results)}条";
        for r in results:
            card = create_item_card(r['item'], r['idx'], r['cat'])
            card.content.subtitle.value += f" | {r['cat']}"
            log_list.controls.append(card)
        s_dialog.open = False;
        page.update()

    s_dialog = ft.AlertDialog(title=ft.Text("搜索"), content=ft.Column([s_field, s_mode], tight=True),
                              actions=[ft.ElevatedButton("搜索", on_click=run_s)])

    # --- 7. 编辑/删除记录 ---
    e_log_field = ft.TextField(label="内容", multiline=True)
    op_ref = {"idx": 0, "cat": ""}

    def save_e(e):
        logs_data[op_ref["cat"]][op_ref["idx"]]['content'] = e_log_field.value
        logs_data[op_ref["cat"]][op_ref["idx"]]['updated_at'] = datetime.now().strftime("%H:%M")
        save_data();
        e_dialog.open = False;
        refresh_ui()

    e_dialog = ft.AlertDialog(title=ft.Text("编辑"), content=e_log_field,
                              actions=[ft.TextButton("保存", on_click=save_e)])

    def open_edit_log_dialog(idx, cat):
        op_ref["idx"], op_ref["cat"] = idx, cat
        e_log_field.value = logs_data[cat][idx]['content']
        e_dialog.open = True;
        page.update()

    def del_log(e):
        logs_data[op_ref["cat"]].pop(op_ref["idx"])
        save_data();
        d_dialog.open = False;
        refresh_ui()

    d_dialog = ft.AlertDialog(title=ft.Text("删除?"),
                              actions=[ft.ElevatedButton("确定", bgcolor="red", on_click=del_log)])

    def open_delete_log_dialog(idx, cat):
        op_ref["idx"], op_ref["cat"] = idx, cat
        d_dialog.open = True;
        page.update()

    # 目录删除
    cat_del_btn = ft.ElevatedButton("确定删除", bgcolor="red", color="white", on_click=lambda _: do_del_cat())
    cat_d_dialog = ft.AlertDialog(actions=[cat_del_btn])

    def check_delete_category(cat_name):
        target_cat_ref.current = cat_name
        n = len(logs_data[cat_name])
        cat_d_dialog.title = ft.Text("确认删除" if n == 0 else "无法删除")
        cat_d_dialog.content = ft.Text(f"确定删除 '{cat_name}'？" if n == 0 else f"请先清空 '{cat_name}'")
        cat_del_btn.visible = (n == 0)
        cat_d_dialog.open = True;
        page.update()

    def do_del_cat():
        name = target_cat_ref.current
        categories.remove(name);
        del logs_data[name]
        if current_category.current == name: current_category.current = categories[0]
        save_data();
        cat_d_dialog.open = False;
        refresh_drawer();
        refresh_ui()

    # --- 8. 页面组装 ---
    page.overlay.extend([detail_dialog, s_dialog, e_dialog, d_dialog, ren_cat_dialog, cat_d_dialog])
    my_drawer = ft.NavigationDrawer(on_change=lambda e: (
    setattr(current_category, "current", categories[int(e.data)]), setattr(my_drawer, "open", False), refresh_ui()))
    page.drawer = my_drawer
    refresh_drawer()

    page.appbar = ft.AppBar(
        leading=ft.IconButton(ft.icons.MENU, on_click=lambda _: page.show_drawer(my_drawer)),
        title=ft.Text("智能笔记"),
        actions=[ft.IconButton(ft.icons.SEARCH, on_click=lambda _: setattr(s_dialog, "open", True) or page.update()),
                 ft.IconButton(ft.icons.REFRESH, on_click=lambda _: refresh_ui())]
    )

    new_in = ft.TextField(label="输入内容...", expand=True)

    def add_click(e):
        if not new_in.value: return
        logs_data[current_category.current].insert(0, {"content": new_in.value,
                                                       "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                                       "updated_at": None})
        new_in.value = "";
        save_data();
        refresh_ui()

    page.add(title_text, ft.Row([new_in, ft.FloatingActionButton(icon=ft.icons.ADD, on_click=add_click)]), ft.Divider(),
             log_list)
    refresh_ui()


# 打包 APK 时，建议 target 使用 main
if __name__ == "__main__":
    ft.app(target=main)
