import os
import sys


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

# Now we can import modules
from src.preprocess.chunker import chunk_law_text

text = """
CHƯƠNG I NHỮNG QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh Bộ luật lao động quy định tiêu chuẩn lao động; quyền, nghĩa vụ,
trách nhiệm của người lao động, người sử dụng lao động, tổ chức đại diện tập thể lao động,
tổ chức đại diện người sử dụng lao động trong quan hệ lao động và các quan hệ khác liên quan
trực tiếp đến quan hệ lao động; quản lý nhà nước về lao động.
Điều 2. Đối tượng áp dụng
1. Người lao động Việt Nam, người học nghề, tập nghề và người lao động khác được quy định tại Bộ luật này.
2. Người sử dụng lao động.
3. Người lao động nước ngoài làm việc tại Việt Nam.
"""


def test_chunk_law_text():
    assert chunk_law_text(text) == [
        {
            "chapter": "CHƯƠNG I NHỮNG QUY ĐỊNH CHUNG",
            "section": None,
            "subsection": None,
            "article": None,
            "clause": None,
            "point": None,
            "content": [],
        },
        {
            "chapter": "CHƯƠNG I NHỮNG QUY ĐỊNH CHUNG",
            "section": None,
            "subsection": None,
            "article": "Điều 1. Phạm vi điều chỉnh Bộ luật lao động quy định tiêu chuẩn lao động; quyền, nghĩa vụ,",
            "clause": None,
            "point": None,
            "content": [
                "trách nhiệm của người lao động, người sử dụng lao động, tổ chức đại diện tập thể lao động,",
                "tổ chức đại diện người sử dụng lao động trong quan hệ lao động và các quan hệ khác liên quan",
                "trực tiếp đến quan hệ lao động; quản lý nhà nước về lao động.",
            ],
        },
        {
            "chapter": "CHƯƠNG I NHỮNG QUY ĐỊNH CHUNG",
            "section": None,
            "subsection": None,
            "article": "Điều 2. Đối tượng áp dụng",
            "clause": None,
            "point": None,
            "content": [],
        },
        {
            "chapter": "CHƯƠNG I NHỮNG QUY ĐỊNH CHUNG",
            "section": None,
            "subsection": None,
            "article": "Điều 2. Đối tượng áp dụng",
            "clause": "1. Người lao động Việt Nam, người học nghề, tập nghề và người lao động khác được quy định tại Bộ luật này.",
            "point": None,
            "content": [],
        },
        {
            "chapter": "CHƯƠNG I NHỮNG QUY ĐỊNH CHUNG",
            "section": None,
            "subsection": None,
            "article": "Điều 2. Đối tượng áp dụng",
            "clause": "2. Người sử dụng lao động.",
            "point": None,
            "content": [],
        },
        {
            "chapter": "CHƯƠNG I NHỮNG QUY ĐỊNH CHUNG",
            "section": None,
            "subsection": None,
            "article": "Điều 2. Đối tượng áp dụng",
            "clause": "3. Người lao động nước ngoài làm việc tại Việt Nam.",
            "point": None,
            "content": [],
        },
    ]
