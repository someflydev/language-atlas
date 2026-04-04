import os
import sqlite3
from typing import List, Dict, Any, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, MarkdownViewer, Input, ListItem, ListView, Label, Static
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.binding import Binding

from app.core.data_loader import DataLoader

class SearchResultItem(ListItem):
    def __init__(self, title: str, category: str, language_name: str, snippet: str):
        super().__init__()
        self.title = title
        self.category = category
        self.language_name = language_name
        self.snippet = snippet

    def compose(self) -> ComposeResult:
        from rich.text import Text
        yield Label(f"[{self.category.upper()}] {self.title}")
        yield Static(Text.from_markup(self.snippet), classes="search_snippet")

class NexusItem(ListItem):
    def __init__(self, language_name: str, score: int, direction: str):
        super().__init__()
        self.language_name = language_name
        self.score = score
        self.direction = direction

    def compose(self) -> ComposeResult:
        icon = "←" if self.direction == "from" else "→"
        yield Label(f"{icon} {self.language_name} (Score: {self.score})")

class LivingAtlasApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    #main_container {
        height: 1fr;
    }

    #left_pane {
        width: 20%;
        border-right: tall $primary;
    }

    #center_pane {
        width: 60%;
    }

    #right_pane {
        width: 20%;
        border-left: tall $primary;
    }

    .pane_title {
        background: $primary;
        color: $text;
        text-align: center;
        text-style: bold;
        padding: 0 1;
    }

    #search_input {
        margin: 0 1;
    }

    #search_results {
        height: auto;
        max-height: 10;
        border: solid $accent;
        display: none;
    }

    #search_results.visible {
        display: block;
    }

    .search_snippet {
        font-size: 80%;
        color: $text-muted;
        margin-left: 2;
    }

    #nexus_list {
        height: 1fr;
    }

    #odyssey_tree {
        display: none;
    }

    #odyssey_tree.visible {
        display: block;
    }

    #chronology_tree.hidden {
        display: none;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("f", "focus_search", "Search"),
        Binding("o", "toggle_odyssey", "Toggle Odyssey Mode"),
        Binding("escape", "hide_search", "Clear Search", show=False),
    ]

    selected_language = reactive(None)
    search_query = reactive("")
    odyssey_mode = reactive(False)

    def __init__(self, initial_language: Optional[str] = None):
        super().__init__()
        self.loader = DataLoader()
        self.initial_language = initial_language
        # Force SQLite for FTS5 features
        os.environ['USE_SQLITE'] = '1'
        self.loader.use_sqlite = True

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search the Atlas (FTS5)...", id="search_input")
        yield ListView(id="search_results")
        with Horizontal(id="main_container"):
            with Vertical(id="left_pane"):
                yield Label("CHRONOLOGY", id="pane_label", classes="pane_title")
                yield Tree("Languages", id="chronology_tree")
                yield Tree("Odysseys", id="odyssey_tree")
            with Vertical(id="center_pane"):
                yield Label("READER", classes="pane_title")
                yield MarkdownViewer(id="reader")
            with Vertical(id="right_pane"):
                yield Label("NEXUS", classes="pane_title")
                yield ListView(id="nexus_list")
        yield Footer()

    def on_mount(self) -> None:
        self.populate_tree()
        self.populate_odyssey_tree()
        if self.initial_language:
            self.selected_language = self.initial_language
            self.select_in_tree(self.initial_language)
        self.query_one("#search_input").focus()

    def populate_tree(self) -> None:
        tree = self.query_one("#chronology_tree")
        tree.root.expand()
        
        langs = self.loader.get_all_languages()
        # Group by generation
        gens = {}
        for l in langs:
            g = l.get('generation', 'unknown').capitalize()
            if g not in gens:
                gens[g] = []
            gens[g].append(l)

        for gen_name in sorted(gens.keys()):
            gen_node = tree.root.add(gen_name, expand=True)
            for lang in sorted(gens[gen_name], key=lambda x: x.get('year', 0)):
                gen_node.add_leaf(lang['name'], data=lang)

    def populate_odyssey_tree(self) -> None:
        tree = self.query_one("#odyssey_tree")
        tree.root.expand()
        
        paths = self.loader.get_learning_paths()
        for p in paths:
            path_node = tree.root.add(p['title'], expand=False, data=p)
            for step in p['steps']:
                path_node.add_leaf(f"{step['milestone']}: {step['language']}", data=step)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.node.data:
            if 'language' in event.node.data:
                self.selected_language = event.node.data['language']
                # Update reader with challenge info if it's a step
                if 'challenge' in event.node.data:
                    self.update_with_challenge(event.node.data)
            elif 'name' in event.node.data:
                self.selected_language = event.node.data['name']

    def update_with_challenge(self, step_data: Dict[str, Any]) -> None:
        lang_data = self.loader.get_combined_language_data(step_data['language'])
        if lang_data:
            md = f"# Odyssey Step: {step_data['milestone']}\n\n"
            md += f"## Challenge\n> {step_data['challenge']}\n\n"
            md += "---\n\n"
            md += self.generate_markdown(lang_data)
            self.query_one("#reader").document.update(md)
            self.update_nexus(step_data['language'])

    def watch_odyssey_mode(self, val: bool) -> None:
        label = self.query_one("#pane_label")
        c_tree = self.query_one("#chronology_tree")
        o_tree = self.query_one("#odyssey_tree")
        
        if val:
            label.update("ODYSSEYS")
            c_tree.add_class("hidden")
            o_tree.add_class("visible")
        else:
            label.update("CHRONOLOGY")
            c_tree.remove_class("hidden")
            o_tree.remove_class("visible")

    def action_toggle_odyssey(self) -> None:
        self.odyssey_mode = not self.odyssey_mode

    def watch_selected_language(self, old_val: str, new_val: str) -> None:
        if new_val:
            self.update_panes(new_val)

    def update_panes(self, language_name: str) -> None:
        # Update Reader
        lang_data = self.loader.get_combined_language_data(language_name)
        if lang_data:
            md = self.generate_markdown(lang_data)
            # If there was a search query, we could highlight it, but MarkdownViewer
            # doesn't support easy highlighting of text nodes.
            # We'll just set the content for now.
            self.query_one("#reader").document.update(md)

        # Update Nexus
        self.update_nexus(language_name)

    def generate_markdown(self, lang: Dict[str, Any]) -> str:
        md = f"# {lang.get('display_name') or lang['name']} ({lang.get('year', 'N/A')})\n\n"
        md += f"- **Creators:** {', '.join(lang.get('creators', []))}\n"
        md += f"- **Paradigms:** {', '.join(lang.get('paradigms', []))}\n"
        md += f"- **Cluster:** {lang.get('cluster', 'N/A')}\n"
        md += f"- **Generation:** {lang.get('generation', 'N/A')}\n\n"
        
        md += "## Philosophy\n"
        md += f"{lang.get('philosophy', 'N/A')}\n\n"
        
        md += "## Mental Model\n"
        md += f"{lang.get('mental_model', 'N/A')}\n\n"
        
        md += "## Key Innovations\n"
        for i in lang.get('key_innovations', []):
            md += f"- {i}\n"
        
        if 'historical_context' in lang:
            md += "\n## Historical Context\n"
            md += lang['historical_context']
            
        return md

    def update_nexus(self, language_name: str) -> None:
        nexus_list = self.query_one("#nexus_list")
        nexus_list.clear()

        conn = self.loader._get_connection()
        # Find ID of selected language
        cursor = conn.execute("SELECT id FROM languages WHERE name = ?", (language_name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        lang_id = row['id']

        # Influenced By
        cursor = conn.execute("""
            SELECT l.name, l.influence_score
            FROM languages l
            JOIN influences i ON l.id = i.source_id
            WHERE i.target_id = ?
        """, (lang_id,))
        for r in cursor.fetchall():
            nexus_list.append(NexusItem(r['name'], r['influence_score'], "from"))

        # Influenced
        cursor = conn.execute("""
            SELECT l.name, l.influence_score
            FROM languages l
            JOIN influences i ON l.id = i.target_id
            WHERE i.source_id = ?
        """, (lang_id,))
        for r in cursor.fetchall():
            nexus_list.append(NexusItem(r['name'], r['influence_score'], "to"))

        conn.close()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, NexusItem):
            self.selected_language = event.item.language_name
            # Also try to select it in the tree for consistency
            self.select_in_tree(event.item.language_name)
        elif isinstance(event.item, SearchResultItem):
            self.selected_language = event.item.language_name
            self.select_in_tree(event.item.language_name)
            self.action_hide_search()

    def select_in_tree(self, language_name: str) -> None:
        tree = self.query_one("#chronology_tree")
        # Recursively find the node
        def find_node(node):
            if node.data and node.data.get('name') == language_name:
                return node
            for child in node.children:
                res = find_node(child)
                if res: return res
            return None
        
        target_node = find_node(tree.root)
        if target_node:
            tree.select_node(target_node)
            tree.scroll_to_node(target_node)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_input":
            self.perform_search(event.value)

    def perform_search(self, query: str) -> None:
        results_list = self.query_one("#search_results")
        if not query or len(query) < 2:
            results_list.clear()
            results_list.remove_class("visible")
            return

        conn = self.loader._get_connection()
        # Search using v_global_search FTS5
        # v_global_search is a union of fts_languages and fts_profiles
        # But we need to match it. Actually v_global_search is NOT an FTS table,
        # it just selects from them. FTS tables are fts_languages and fts_profiles.
        
        # We'll use a modified version of Loader.search logic but targeting v_global_search if possible,
        # or just join them.
        
        sql = """
            SELECT category, title, snippet, l.name as language_name
            FROM (
                SELECT 'language' as category, language_id, name as title, snippet(fts_languages, -1, '[b]', '[/b]', '...', 10) as snippet, bm25(fts_languages) as score
                FROM fts_languages WHERE fts_languages MATCH ?
                UNION ALL
                SELECT 'profile' as category, language_id, language_name || ' (' || section_name || ')' as title, snippet(fts_profiles, -1, '[b]', '[/b]', '...', 10) as snippet, bm25(fts_profiles) as score
                FROM fts_profiles WHERE fts_profiles MATCH ?
            ) s
            JOIN languages l ON s.language_id = l.id
            ORDER BY score
            LIMIT 10
        """
        
        try:
            cursor = conn.execute(sql, (query, query))
            rows = cursor.fetchall()
            results_list.clear()
            if rows:
                results_list.add_class("visible")
                for row in rows:
                    results_list.append(SearchResultItem(row['title'], row['category'], row['language_name'], row['snippet']))
            else:
                results_list.remove_class("visible")
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()

    def action_focus_search(self) -> None:
        self.query_one("#search_input").focus()

    def action_hide_search(self) -> None:
        self.query_one("#search_input").value = ""
        results_list = self.query_one("#search_results")
        results_list.clear()
        results_list.remove_class("visible")
        self.query_one("#chronology_tree").focus()

if __name__ == "__main__":
    import sys
    initial_lang = sys.argv[1] if len(sys.argv) > 1 else None
    app = LivingAtlasApp(initial_language=initial_lang)
    app.run()
