# -*- coding: utf-8 -*-
"""知识库使用示例

演示如何使用知识库服务添加和搜索转写文本。
"""

from __future__ import annotations

import json
from knowledge_base_service import knowledge_base


def main():
    """主函数，演示知识库功能"""
    print("开始知识库功能演示...")

    # 示例转写文本（句子段格式）
    sample_transcripts = [
        {
            # 不再包含 video_id；metadata 只包含 transcript_id
            "segments": [
                {"index": 0, "sentence": "人工智能正在改变我们的生活方式。", "start_time": 0.0, "end_time": 3.5},
                {"index": 1, "sentence": "从智能手机到自动驾驶汽车，AI技术已经渗透到我们日常生活的方方面面。", "start_time": 3.5, "end_time": 8.2},
                {"index": 2, "sentence": "机器学习算法可以帮助我们预测天气、推荐电影，甚至诊断疾病。", "start_time": 8.2, "end_time": 12.8},
                {"index": 3, "sentence": "随着技术的不断进步，AI将在更多领域发挥重要作用。", "start_time": 12.8, "end_time": 16.1}
            ],
            "metadata": {"transcript_id": 1}
        },
        {
            # 不再包含 video_id；metadata 只包含 transcript_id
            "segments": [
                {"index": 0, "sentence": "深度学习是机器学习的一个子集，使用神经网络来模拟人脑的工作方式。", "start_time": 0.0, "end_time": 5.1},
                {"index": 1, "sentence": "卷积神经网络在图像识别领域取得了巨大成功。", "start_time": 5.1, "end_time": 9.3},
                {"index": 2, "sentence": "而循环神经网络在自然语言处理中发挥着重要作用。", "start_time": 9.3, "end_time": 13.7},
                {"index": 3, "sentence": "生成对抗网络可以用于图像生成和风格迁移。", "start_time": 13.7, "end_time": 18.2}
            ],
            "metadata": {"transcript_id": 2}
        }
    ]

    # 添加转写句子段到知识库（会自动组装成块）
    print("正在添加示例转写句子段到知识库...")
    for transcript in sample_transcripts:
        try:
            knowledge_base.add_transcript(
                video_id=None,
                segments=transcript["segments"],
                metadata=transcript["metadata"]
            )
            print(f"✓ 已添加转写: transcript_id={transcript['metadata']['transcript_id']} ({len(transcript['segments'])}个句子段，将组装成块)")
        except Exception as e:
            print(f"✗ 添加失败 transcript_id={transcript['metadata'].get('transcript_id', 'unknown')}: {str(e)}")

    # 搜索示例
    print("\n正在执行搜索示例...")
    search_queries = [
        "人工智能如何改变生活",
        "神经网络在图像识别中的应用",
        "自然语言处理的发展"
    ]

    for query in search_queries:
        print(f"\n搜索查询: '{query}'")
        try:
            results = knowledge_base.search_similar(query=query, n_results=2)
            for i, result in enumerate(results, 1):
                print(f"{i}. doc_id: {result.get('doc_id', 'N/A')} 相似度: {result['distance']:.4f}")
                print(f"   文本块: {result['text'][:150]}...")
                print(f"   元数据: transcript_id={result['metadata'].get('transcript_id')}, chunk_index={result['metadata'].get('chunk_index')}, segment_indices={json.loads(result['metadata'].get('segment_indices', '[]'))}")
                # 如果需要更详细的句子信息，可以调用 /knowledge/doc/{doc_id} 接口去获取
        except Exception as e:
            print(f"搜索失败: {str(e)}")

    # 范围搜索示例：只在 transcript_id=1 中搜索
    print("\n正在执行范围搜索示例（只在 transcript_id=1 中）...")
    range_query = "人工智能如何改变生活"
    try:
        results = knowledge_base.search_similar(query=range_query, n_results=2, transcript_ids=[1])
        print(f"范围搜索查询: '{range_query}' (transcript_ids=[1])")
        for i, result in enumerate(results, 1):
            print(f"{i}. doc_id: {result.get('doc_id', 'N/A')} 相似度: {result['distance']:.4f}")
            print(f"   文本块: {result['text'][:150]}...")
            print(f"   元数据: transcript_id={result['metadata'].get('transcript_id')}, chunk_index={result['metadata'].get('chunk_index')}, segment_indices={json.loads(result['metadata'].get('segment_indices', '[]'))}")
    except Exception as e:
        print(f"范围搜索失败: {str(e)}")

    # 获取所有视频ID
    print("\n获取所有转写ID（transcript_id）...")
    try:
        transcript_ids = knowledge_base.get_transcript_ids()
        print(f"知识库中的转写数量: {len(transcript_ids)}")
        print(f"transcript_id 列表: {transcript_ids}")
    except Exception as e:
        print(f"获取视频ID失败: {str(e)}")

    # 删除测试
    print("\n正在测试删除功能...")
    if transcript_ids:
        test_transcript_id = transcript_ids[0]  # 删除第一个转写
        print(f"测试删除 transcript_id={test_transcript_id} 的所有向量...")

        # 执行条件删除
        try:
            knowledge_base.collection.delete(where={"transcript_id": test_transcript_id})
            print(f"✓ 条件删除成功: transcript_id={test_transcript_id}")
        except Exception as e:
            print(f"✗ 条件删除失败: {str(e)}")

        # 验证删除结果
        try:
            remaining_ids = knowledge_base.get_transcript_ids()
            print(f"删除后剩余转写数量: {len(remaining_ids)}")
            print(f"剩余 transcript_id 列表: {remaining_ids}")
            if test_transcript_id not in remaining_ids:
                print("✓ 删除验证成功")
            else:
                print("⚠ 删除可能失败")
        except Exception as e:
            print(f"验证失败: {str(e)}")

    print("\n知识库演示完成！")


if __name__ == "__main__":
    main()
