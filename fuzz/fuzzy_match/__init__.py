"""
Visual Novel Title Fuzzy Matching Package
使用Sentence-BERT和Faiss实现的高效视觉小说标题模糊匹配系统
"""

from .matcher import TitleMatcher

__all__ = ['TitleMatcher']
