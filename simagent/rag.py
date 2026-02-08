import json
import math
import os
import re
from dataclasses import dataclass
from typing import Iterable

from simagent.repo_reader import DocumentChunk, RepoReader


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass
class RAGDocument:
    path: str
    start_line: int
    end_line: int
    content: str
    term_freq: dict[str, int]


class RAGIndex:
    def __init__(self, repo_path: str, index_path: str | None = None):
        self.repo_path = os.path.abspath(repo_path)
        self.index_path = index_path or os.path.join(self.repo_path, ".simagent", "index.json")
        self.documents: list[RAGDocument] = []
        self.doc_freq: dict[str, int] = {}
        self.total_docs = 0

    def build(self, reader: RepoReader) -> None:
        self.documents = []
        self.doc_freq = {}
        for chunk in reader.iter_chunks():
            term_freq = self._tokenize(chunk.content)
            if not term_freq:
                continue
            self.documents.append(
                RAGDocument(
                    path=chunk.path,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    content=chunk.content,
                    term_freq=term_freq,
                )
            )
            for term in term_freq:
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1
        self.total_docs = len(self.documents)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        payload = {
            "repo_path": self.repo_path,
            "doc_freq": self.doc_freq,
            "documents": [
                {
                    "path": doc.path,
                    "start_line": doc.start_line,
                    "end_line": doc.end_line,
                    "content": doc.content,
                    "term_freq": doc.term_freq,
                }
                for doc in self.documents
            ],
        }
        with open(self.index_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def load(self) -> bool:
        if not os.path.exists(self.index_path):
            return False
        with open(self.index_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if payload.get("repo_path") != self.repo_path:
            return False
        self.doc_freq = payload.get("doc_freq", {})
        self.documents = [
            RAGDocument(
                path=item["path"],
                start_line=item["start_line"],
                end_line=item["end_line"],
                content=item["content"],
                term_freq=item.get("term_freq", {}),
            )
            for item in payload.get("documents", [])
        ]
        self.total_docs = len(self.documents)
        return True

    def retrieve(self, query: str, top_k: int = 4) -> list[RAGDocument]:
        if not self.documents:
            return []
        query_terms = self._tokenize(query)
        if not query_terms:
            return []
        scores: list[tuple[float, RAGDocument]] = []
        for doc in self.documents:
            score = self._bm25_score(query_terms, doc.term_freq)
            if score > 0:
                scores.append((score, doc))
        scores.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scores[:top_k]]

    def iter_snippets(self, query: str, top_k: int = 4) -> Iterable[str]:
        for doc in self.retrieve(query, top_k=top_k):
            yield (
                f"File: {doc.path} (lines {doc.start_line}-{doc.end_line})\n"
                f"{doc.content.strip()}"
            )

    def _tokenize(self, text: str) -> dict[str, int]:
        tokens = TOKEN_RE.findall(text.lower())
        term_freq: dict[str, int] = {}
        for token in tokens:
            term_freq[token] = term_freq.get(token, 0) + 1
        return term_freq

    def _bm25_score(self, query_terms: dict[str, int], doc_terms: dict[str, int]) -> float:
        score = 0.0
        k1 = 1.5
        b = 0.75
        doc_len = sum(doc_terms.values()) or 1
        avg_doc_len = self._avg_doc_len()
        for term, qtf in query_terms.items():
            if term not in doc_terms:
                continue
            df = self.doc_freq.get(term, 0)
            idf = math.log(1 + (self.total_docs - df + 0.5) / (df + 0.5))
            tf = doc_terms[term]
            denom = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
            score += idf * ((tf * (k1 + 1)) / denom) * qtf
        return score

    def _avg_doc_len(self) -> float:
        if not self.documents:
            return 1.0
        total = sum(sum(doc.term_freq.values()) for doc in self.documents)
        return total / len(self.documents)
