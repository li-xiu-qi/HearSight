# -*- coding: utf-8 -*-
"""知识库服务模块

使用 ChromaDB 实现多视频知识库，支持向量检索。
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, TypedDict

import chromadb
from openai import OpenAI

# 添加项目根目录到路径，确保导入backend模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.config import settings


class DocDetails(TypedDict):
    doc_id: str
    transcript_id: str
    chunk_index: int
    chunk_text: str
    sentences: List[Dict[str, Any]]


class KnowledgeBaseService:
    """知识库服务类"""

    def __init__(self):
        """初始化知识库服务"""
        # 将向量数据库放到app_datas目录
        app_datas_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "app_datas"
        chroma_path = app_datas_dir / "chroma_db"
        chroma_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(chroma_path))
        self.collection = self.client.get_or_create_collection(name="video_transcripts")
        self.openai_client = OpenAI(
            api_key=settings.embedding_provider_api_key,
            base_url=settings.embedding_provider_base_url,
        )

    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量嵌入"""
        response = self.openai_client.embeddings.create(
            input=text,
            model=settings.embedding_model
        )
        return response.data[0].embedding

    def add_transcript(self, video_id: str, segments: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """添加视频转写句子段到知识库

        将句子段组装成块，每个块约2000字符，作为一个向量文档。

        Args:
            video_id: 视频唯一标识（可选，已废弃，优先使用metadata中的transcript_id）
            segments: 句子段列表，每个包含sentence等信息
            metadata: 元数据，必须包含transcript_id
        """
        if metadata is None:
            metadata = {}

        chunks = self._group_segments_into_chunks(segments, chunk_size=2000)

        for i, chunk in enumerate(chunks):
            chunk_text = " ".join([seg["sentence"] for seg in chunk])
            embedding = self._get_embedding(chunk_text)

            transcript_id = metadata.get("transcript_id") if metadata else None
            if transcript_id:
                doc_id = f"{transcript_id}_chunk_{i}"
            else:
                doc_id = f"{video_id}_chunk_{i}"

            chunk_metadata = {
                "transcript_id": transcript_id,
                "chunk_index": i,
                "segment_indices": json.dumps([seg.get("index") for seg in chunk]),
            }

            try:
                self.collection.upsert(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[chunk_text],
                    metadatas=[chunk_metadata],
                )
            except Exception:
                self.collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[chunk_text],
                    metadatas=[chunk_metadata],
                )

    def _get_metadata_by_id(self, doc_id: str) -> Dict[str, Any] | None:
        """通过 doc_id 从 Chroma 中获取 metadata"""
        try:
            res = self.collection.get(ids=[doc_id], include=["metadatas", "documents"])
            if res and res.get("metadatas") and len(res.get("metadatas")) > 0:
                md = res.get("metadatas")[0]
                doc = res.get("documents")[0] if res.get("documents") else None
                return {"metadata": md, "document": doc}
        except Exception:
            return None
        return None

    def search_similar(self, query: str, n_results: int = 5, transcript_ids: List[int] = None) -> List[Dict[str, Any]]:
        """搜索相似内容

        Args:
            query: 查询文本
            n_results: 返回结果数量
            transcript_ids: 可选，限制搜索范围到指定 transcript_id 列表

        Returns:
            相似文档列表，包含文本、元数据和相似度
        """
        query_embedding = self._get_embedding(query)
        where_clause = {"transcript_id": {"$in": transcript_ids}} if transcript_ids else None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        search_results = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            # 从metadata生成doc_id
            doc_id = f"{metadata['transcript_id']}_chunk_{metadata['chunk_index']}" if metadata.get('transcript_id') and metadata.get('chunk_index') is not None else None
            search_results.append({
                "doc_id": doc_id,
                "text": doc,
                "metadata": metadata,
                "distance": results["distances"][0][i]
            })

        return search_results

    def get_doc_details(self, doc_id: str, db_url: str) -> DocDetails | None:
        """获取文档（块）详细信息，通过 transcript 表重建句子信息并返回（内部方法）"""
        try:
            # 获取 Chroma 中的 metadata（包含 transcript_id 和 chunk_index）
            md_res = self._get_metadata_by_id(doc_id)
            if not md_res or not md_res.get("metadata"):
                return None

            metadata = md_res.get("metadata")
            transcript_id = metadata.get("transcript_id")
            chunk_index = metadata.get("chunk_index")

            if not transcript_id:
                return None

            # 从数据库中获取转写记录
            from backend.db.transcript_crud import get_transcript_by_id
            tr = get_transcript_by_id(db_url, int(transcript_id))
            if not tr:
                return None

            segments = tr.get("segments", [])

            # 如果 metadata 中包含 segment_indices，优先使用它们以避免和 chunk 算法依赖
            segment_indices = metadata.get("segment_indices") if metadata else None
            if segment_indices:
                try:
                    segment_indices = json.loads(segment_indices)
                    chosen_chunk = [s for s in segments if s.get("index") in segment_indices]
                except Exception:
                    return None
            else:
                # 使用 knowledge_base 的 chunk 算法重建 chunks，并定位 chunk
                chunks = self._group_segments_into_chunks(segments, chunk_size=2000)
                try:
                    chosen_chunk = chunks[int(chunk_index)]
                except Exception:
                    return None

            chunk_text = " ".join([s["sentence"] for s in chosen_chunk])

            # 返回整段信息
            return {
                "doc_id": doc_id,
                "transcript_id": transcript_id,
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "sentences": [
                    {
                        "index": s.get("index"),
                        "sentence": s.get("sentence"),
                        "start_time": s.get("start_time"),
                        "end_time": s.get("end_time"),
                        "spk_id": s.get("spk_id"),
                    }
                    for s in chosen_chunk
                ],
            }
        except Exception:
            return None

    def _group_segments_into_chunks(self, segments: List[Dict[str, Any]], chunk_size: int = 2000) -> List[List[Dict[str, Any]]]:
        """将句子段组装成块，每个块约chunk_size字符

        贪心算法：按顺序累积句子，直到超过chunk_size则切分，确保块内句子连续。
        """
        chunks = []
        current_chunk = []
        current_length = 0

        for segment in segments:
            sentence = segment.get("sentence", "")
            sentence_length = len(sentence)

            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_length = 0

            current_chunk.append(segment)
            current_length += sentence_length

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def get_transcript_ids(self) -> List[int]:
        """获取所有 transcript_id（用于标识转写记录）"""
        results = self.collection.get(include=["metadatas"])
        transcript_ids = set()
        for metadata in results.get("metadatas", []):
            tid = metadata.get("transcript_id") if metadata else None
            if tid:
                try:
                    transcript_ids.add(int(tid))
                except Exception:
                    transcript_ids.add(tid)
        return list(transcript_ids)


# 全局实例
knowledge_base = KnowledgeBaseService()