"""Basic pipeline unit test using mock objects.
"""
from ingest.binary_loader import BinaryLoader
from llm.client import LLMClient
from llm.refiner import Refiner

def test_refine_cycle(tmp_path):
    bl = BinaryLoader(tmp_path)
    meta = bl.ingest(__file__)  # ingest this test file as a placeholder
    llm = LLMClient()
    ref = Refiner(llm)
    fn = {'fn_id': '0x1', 'instrs': []}
    out = ref.refine(fn)
    assert 'code' in out