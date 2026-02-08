import json
import textwrap
from dataclasses import dataclass

from simagent.llm import LLMClient
from simagent.rag import RAGIndex
from simagent.repo_reader import RepoReader
from simagent.tools import list_files, read_file, search, write_file


SYSTEM_PROMPT = """
You are SimAgent, a local software engineering agent.
You can call tools by outputting JSON in one of these forms:
{"tool": "list_files", "subdir": ""}
{"tool": "read_file", "path": ""}
{"tool": "write_file", "path": "", "content": ""}
{"tool": "search", "pattern": ""}
If you are done, output: {"final": "..."}
Only output JSON. Use tools to read files before editing.
""".strip()


@dataclass
class AgentConfig:
    repo_path: str
    index_path: str | None
    max_turns: int = 8


class Agent:
    def __init__(self, repo_path: str, index_path: str | None = None, max_turns: int = 8):
        self.config = AgentConfig(repo_path=repo_path, index_path=index_path, max_turns=max_turns)
        self.llm = LLMClient()
        self.index = RAGIndex(repo_path=repo_path, index_path=index_path)
        self._load_or_build_index()

    def _load_or_build_index(self) -> None:
        if self.index.load():
            return
        reader = RepoReader(self.config.repo_path)
        self.index.build(reader)
        self.index.save()

    def run_repl(self) -> None:
        print("SimAgent ready. Type 'exit' to quit.")
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                return
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Bye!")
                return
            self.handle_query(user_input)

    def handle_query(self, query: str) -> None:
        if not self.llm.is_configured():
            print("LLM_BASE_URL is not set. Please configure and retry.")
            return
        snippets = "\n\n".join(self.index.iter_snippets(query))
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._wrap_user_prompt(query, snippets),
            },
        ]
        for turn in range(self.config.max_turns):
            response = self.llm.chat(messages)
            content = response.content.strip()
            tool_result = self._handle_model_output(content)
            if tool_result is None:
                return
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "tool", "content": tool_result})
        print("Reached max turns without final response.")

    def _wrap_user_prompt(self, query: str, snippets: str) -> str:
        if snippets:
            return textwrap.dedent(
                f"""
                User request: {query}

                Relevant code snippets:
                {snippets}
                """
            ).strip()
        return f"User request: {query}"

    def _handle_model_output(self, content: str) -> str | None:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            print("Model response was not JSON. Response:")
            print(content)
            return None
        if "final" in payload:
            print(payload["final"])
            return None
        tool = payload.get("tool")
        if tool == "list_files":
            subdir = payload.get("subdir")
            result = list_files(self.config.repo_path, subdir=subdir)
        elif tool == "read_file":
            path = payload.get("path")
            if not path:
                result = "Missing path"
            else:
                result = read_file(self.config.repo_path, path)
        elif tool == "write_file":
            path = payload.get("path")
            content_to_write = payload.get("content", "")
            if not path:
                result = "Missing path"
            else:
                result = write_file(self.config.repo_path, path, content_to_write)
        elif tool == "search":
            pattern = payload.get("pattern", "")
            result = search(self.config.repo_path, pattern)
        else:
            print(f"Unknown tool: {tool}")
            return None
        if isinstance(result, str):
            return result
        output = f"ok={result.ok}\n{result.output}"
        return output
