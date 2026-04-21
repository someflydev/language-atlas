import os
import sqlite3
from typing import List, Dict, Any, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, MarkdownViewer, Input, ListItem, ListView, Label, Static
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.binding import Binding

from app.core.data_loader import DataLoader
from app.core.terminal_ui import (
    build_downstream_lineage_entries,
    build_upstream_lineage_sections,
    format_lineage_entry,
    get_display_name,
    get_entity_type_label,
)

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
    def __init__(
        self,
        language_name: str,
        direction: str,
        display_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        influence_type: Optional[str] = None,
    ):
        super().__init__()
        self.language_name = language_name
        self.direction = direction
        self.display_name = display_name or language_name
        self.entity_type = entity_type
        self.influence_type = influence_type

    def compose(self) -> ComposeResult:
        icon = "←" if self.direction == "from" else "→"
        meta = [get_entity_type_label(self.entity_type)]
        if self.influence_type:
            meta.append(self.influence_type)
        yield Label(f"{icon} {self.display_name} [{' | '.join(meta)}]")


class NexusSectionItem(ListItem):
    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.title}[/bold]")


class NexusMessageItem(ListItem):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Label(self.message)

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
        Binding("m", "cycle_browse_mode", "Cycle Browse Mode"),
        Binding("escape", "hide_search", "Clear Search", show=False),
    ]

    selected_language = reactive[str | None](None)
    search_query = reactive[str]("")
    odyssey_mode = reactive[bool](False)
    browse_mode = reactive[str]("language")

    def __init__(self, initial_language: Optional[str] = None) -> None:
        super().__init__()
        self.loader = DataLoader()
        self.initial_language = initial_language
        # Force SQLite for FTS5 features
        os.environ['USE_SQLITE'] = '1'
        self.loader.use_sqlite = True

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(
            placeholder="Search languages, foundations, and artifacts...",
            id="search_input",
        )
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
        self.query_one("#pane_label", Label).update(self._chronology_label())
        if self.initial_language:
            self.selected_language = self.initial_language
            self.select_in_tree(self.initial_language)
        self.query_one("#search_input", Input).focus()

    def populate_tree(self) -> None:
        tree = self.query_one("#chronology_tree", Tree[dict[str, Any]])
        tree.clear()
        tree.root.expand()

        entities = self.get_browse_entities()
        # Group by generation
        gens: dict[str, list[dict[str, Any]]] = {}
        for l in entities:
            g = l.get('generation', 'unknown').capitalize()
            if g not in gens:
                gens[g] = []
            gens[g].append(l)

        root_label = {
            "language": "Languages",
            "foundation": "Foundations",
            "artifact": "Artifacts",
            "all": "All Language-like Entities",
        }[self.browse_mode]
        tree.root.label = root_label

        for gen_name in sorted(gens.keys()):
            gen_node = tree.root.add(gen_name, expand=True)
            for lang in sorted(gens[gen_name], key=lambda x: (x.get('year') or 0, x.get('name') or "")):
                label = get_display_name(lang)
                if self.browse_mode == "all":
                    label = f"{label} [{get_entity_type_label(lang.get('entity_type'))}]"
                gen_node.add_leaf(label, data=lang)

    def get_browse_entities(self) -> List[Dict[str, Any]]:
        return self.get_browse_entities_for_mode(self.browse_mode)

    def get_browse_entities_for_mode(self, mode: str) -> List[Dict[str, Any]]:
        selected_type = None if mode == "all" else mode
        return self.loader.get_all_languages(entity_type=selected_type)

    def populate_odyssey_tree(self) -> None:
        tree = self.query_one("#odyssey_tree", Tree[dict[str, Any]])
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
            # Pull challenge from lang_data instead of step_data
            challenge = lang_data.get('challenge', 'No specific challenge listed.')
            md += f"## Challenge\n> {challenge}\n\n"
            md += "---\n\n"
            md += self.generate_markdown(lang_data)
            self.query_one("#reader", MarkdownViewer).document.update(md)
            self.update_nexus(step_data['language'])

    def watch_odyssey_mode(self, val: bool) -> None:
        if not self.is_mounted:
            return
        label = self.query_one("#pane_label", Label)
        c_tree = self.query_one("#chronology_tree", Tree[dict[str, Any]])
        o_tree = self.query_one("#odyssey_tree", Tree[dict[str, Any]])
        
        if val:
            label.update("ODYSSEYS")
            c_tree.add_class("hidden")
            o_tree.add_class("visible")
        else:
            label.update(self._chronology_label())
            c_tree.remove_class("hidden")
            o_tree.remove_class("visible")

    def action_toggle_odyssey(self) -> None:
        self.odyssey_mode = not self.odyssey_mode

    def _chronology_label(self) -> str:
        labels = {
            "language": "CHRONOLOGY [LANGUAGES]",
            "foundation": "CHRONOLOGY [FOUNDATIONS]",
            "artifact": "CHRONOLOGY [ARTIFACTS]",
            "all": "CHRONOLOGY [ALL]",
        }
        return labels[self.browse_mode]

    def action_cycle_browse_mode(self) -> None:
        modes = ["language", "foundation", "artifact", "all"]
        current_index = modes.index(self.browse_mode)
        self.browse_mode = modes[(current_index + 1) % len(modes)]

    def watch_browse_mode(self, _: str, __: str) -> None:
        if not self.is_mounted:
            return
        if not self.odyssey_mode:
            self.query_one("#pane_label", Label).update(self._chronology_label())
        self.populate_tree()
        if self.selected_language:
            self.select_in_tree(self.selected_language)

    def watch_selected_language(self, old_val: str | None, new_val: str | None) -> None:
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
            self.query_one("#reader", MarkdownViewer).document.update(md)

        # Update Nexus
        self.update_nexus(language_name)

    def generate_markdown(self, lang: Dict[str, Any]) -> str:
        entity_label = get_entity_type_label(lang.get('entity_type'))
        md = f"# {lang.get('display_name') or lang['name']} ({lang.get('year', 'N/A')})\n\n"
        md += f"- **Entity Type:** {entity_label}\n"
        md += f"- **Creators:** {', '.join(lang.get('creators', [])) or 'Unknown'}\n"
        md += f"- **Paradigms:** {', '.join(lang.get('paradigms', [])) or 'Unspecified'}\n"
        md += f"- **Cluster:** {lang.get('cluster', 'N/A')}\n"
        md += f"- **Generation:** {lang.get('generation', 'N/A')}\n\n"

        upstream_sections = build_upstream_lineage_sections(lang)
        downstream_entries = build_downstream_lineage_entries(lang)
        if upstream_sections or downstream_entries:
            md += "## Upstream Lineage\n"
            if upstream_sections:
                for section in upstream_sections:
                    md += f"\n### {section['label']}\n"
                    for item in section.get("items", []):
                        md += f"- {format_lineage_entry(item)}\n"
            else:
                md += "\nNo upstream lineage recorded.\n"

            md += "\n### Downstream Influences\n"
            if downstream_entries:
                for item in downstream_entries:
                    md += f"- {format_lineage_entry(item)}\n"
            else:
                md += "- None recorded.\n"
            md += "\n"

        overview = lang.get("overview")
        if overview:
            md += "## Overview\n"
            md += f"{overview}\n\n"

        md += "## Philosophy\n"
        md += f"{lang.get('philosophy', 'N/A')}\n\n"

        md += "## Mental Model\n"
        md += f"{lang.get('mental_model', 'N/A')}\n\n"

        innovations = lang.get('key_innovations', [])
        if innovations:
            md += "## Key Innovations\n"
            for i in innovations:
                md += f"- {i}\n"
            md += "\n"

        if 'historical_context' in lang:
            md += "## Historical Context\n"
            md += f"{lang['historical_context']}\n"
            
        return md

    def update_nexus(self, language_name: str) -> None:
        nexus_list = self.query_one("#nexus_list", ListView)
        nexus_list.clear()
        nexus_sections = self.get_nexus_sections(language_name)
        if not nexus_sections:
            nexus_list.append(NexusMessageItem("No lineage recorded."))
            return

        for section in nexus_sections:
            nexus_list.append(NexusSectionItem(section["label"]))
            items = section.get("items", [])
            if items:
                for item in items:
                    nexus_list.append(
                        NexusItem(
                            item["name"],
                            section["direction"],
                            display_name=get_display_name(item),
                            entity_type=item.get("entity_type"),
                            influence_type=item.get("type"),
                        )
                    )
            else:
                nexus_list.append(NexusMessageItem(section["empty_message"]))

    def get_nexus_sections(self, language_name: str) -> List[Dict[str, Any]]:
        influences = self.loader.get_influences(language_name)
        if not influences:
            return []

        upstream_sections = build_upstream_lineage_sections(influences)
        downstream_entries = build_downstream_lineage_entries(influences)
        sections: List[Dict[str, Any]] = []

        if upstream_sections:
            for section in upstream_sections:
                sections.append(
                    {
                        "label": section["label"],
                        "direction": "from",
                        "items": section.get("items", []),
                        "empty_message": "No upstream influences recorded.",
                    }
                )

        sections.append(
            {
                "label": "Downstream Influences",
                "direction": "to",
                "items": downstream_entries,
                "empty_message": "No downstream influences recorded.",
            }
        )
        return sections

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, NexusItem):
            self.selected_language = event.item.language_name
            self._switch_browse_mode_for_entity(event.item.entity_type)
            # Also try to select it in the tree for consistency
            self.select_in_tree(event.item.language_name)
        elif isinstance(event.item, SearchResultItem):
            self.selected_language = event.item.language_name
            self._switch_browse_mode_for_entity(event.item.category)
            self.select_in_tree(event.item.language_name)
            self.action_hide_search()

    def _switch_browse_mode_for_entity(self, entity_type: Optional[str]) -> None:
        normalized = (entity_type or "language").lower()
        if normalized in {"language", "foundation", "artifact"} and self.browse_mode != normalized:
            self.browse_mode = normalized

    def select_in_tree(self, language_name: str) -> None:
        tree = self.query_one("#chronology_tree", Tree[dict[str, Any]])
        # Recursively find the node
        def find_node(node: Any) -> Any:
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
        results_list = self.query_one("#search_results", ListView)
        if not query or len(query) < 2:
            results_list.clear()
            results_list.remove_class("visible")
            return

        conn = self.loader._get_connection()
        # Search using search_index FTS5
        sql = """
            SELECT entity_type as category, title, snippet(search_index, -1, '[b]', '[/b]', '...', 10) as snippet, entity_id as language_name
            FROM search_index 
            WHERE search_index MATCH ?
              AND entity_type IN ('language', 'foundation', 'artifact')
            ORDER BY bm25(search_index)
            LIMIT 10
        """
        
        try:
            cursor = conn.execute(sql, (query,))
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
        self.query_one("#search_input", Input).focus()

    def action_hide_search(self) -> None:
        self.query_one("#search_input", Input).value = ""
        results_list = self.query_one("#search_results", ListView)
        results_list.clear()
        results_list.remove_class("visible")
        self.query_one("#chronology_tree", Tree[dict[str, Any]]).focus()

if __name__ == "__main__":
    import sys
    initial_lang = sys.argv[1] if len(sys.argv) > 1 else None
    app = LivingAtlasApp(initial_language=initial_lang)
    app.run()
