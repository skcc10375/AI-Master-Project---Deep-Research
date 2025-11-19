import asyncio
import base64
import time
import traceback
from io import BytesIO
from typing import List, Dict, Any
from openai import AsyncOpenAI
import fitz  # PyMuPDF
import json 
from pathlib import Path

# OpenAI 설정
VLM_URL = "https://api.openai.com/v1"
MODEL_NAME = "gpt-5-chat-latest"
API_KEY = "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"

MAX_CONCURRENT_TASKS = 3  # 동시에 처리할 페이지 수

class VLMParser:
    def __init__(self):
        self.client = None
        self.sem = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    async def _ensure_client(self):
        if self.client is None:
            self.client = AsyncOpenAI(api_key=API_KEY, base_url=VLM_URL, timeout=120)
        return self.client

    async def render_page_to_b64(self, doc: fitz.Document, page_idx: int, dpi: int = 150) -> str:
        """fitz PDF → JPEG base64 변환 (비동기 스레드 오프로딩)"""
        def _render():
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(dpi=dpi)
            return base64.b64encode(pix.tobytes("jpeg")).decode("utf-8")

        return await asyncio.to_thread(_render)  # CPU 연산을 별도 스레드로

    async def parse_single_page(self, doc: fitz.Document, page_idx: int, system_prompt: str) -> dict:
        """한 페이지를 이미지로 변환 후 VLM 호출"""
        async with self.sem:  # 동시에 n개까지만 실행
            client = await self._ensure_client()
            page_no = page_idx + 1

            print(f"[시작] 페이지 {page_no} 처리 중...")

            try:
                # PDF → 이미지 변환 (스레드로 비동기화)
                img_b64 = await self.render_page_to_b64(doc, page_idx, dpi=200)

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                            {"type": "text", "text": system_prompt},
                        ],
                    }
                ]

                start = time.perf_counter()
                res = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        seed=42,
                        timeout=100,
                    ),
                    timeout=180,
                )
                ans = res.choices[0].message.content or ""
                elapsed = round(time.perf_counter() - start, 2)
                print(f"[완료] 페이지 {page_no} (소요 {elapsed}s)")
                return {"page": page_no, "elapsed": elapsed, "content": ans}

            except asyncio.TimeoutError:
                print(f"[타임아웃] 페이지 {page_no}")
                return {"page": page_no, "content": "[타임아웃 발생]"}

            except Exception as e:
                print(f"[에러] 페이지 {page_no}: {e}")
                traceback.print_exc()
                return {"page": page_no, "content": f"[예외] {type(e).__name__}: {e}"}

    async def parse_pdf(self, pdf_path: str, system_prompt: str, output_jsonl: str):
        """PDF 병렬 파싱 + JSONL append + resume 지원"""
        pdf_path = Path(pdf_path)
        output_jsonl = Path(output_jsonl)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

        client = await self._ensure_client()
        with fitz.open(pdf_path) as doc, open(output_jsonl, "a", encoding="utf-8") as f:
            total_pages = len(doc)
            print(f"\n🚀 PDF 파싱 시작: {pdf_path.name} (총 {total_pages}페이지, 병렬 {MAX_CONCURRENT_TASKS}개)\n")

            tasks = []
            for idx in range(total_pages):
                tasks.append(self.parse_single_page(doc, idx, system_prompt))

            buffer = {}
            for coro in asyncio.as_completed(tasks):
                result = await coro
                buffer[result["page"]] = result  # 페이지번호 기준으로 보관

            # 모든 페이지 완료 후, 순서대로 저장
            with open(output_jsonl, "w", encoding="utf-8") as f:
                for page in sorted(buffer.keys()):
                    f.write(json.dumps(buffer[page], ensure_ascii=False) + "\n")


        await client.close()
        print(f"\n 모든 페이지 병렬 파싱 완료! 결과 저장: {output_jsonl}\n")


async def main():
    PDF_PATH = "../data/2024-04-22_우리은행_비정형 데이터 자산화 시스템 2단계 구축_Ⅳ.기술부문.pdf"
    OUTPUT_PATH = "./output/2024-04-22_우리은행_비정형 데이터 자산화 시스템 2단계 구축_Ⅳ.기술부문.json" 
    PROMPT = """
    You are an expert in analyzing and reconstructing proposal or presentation documents 
    that contain both text and visual structures (such as tables, diagrams, charts, or architecture figures).
    Your task is to parse the given image page into a structured and detailed representation of its content,
    preserving all textual information and clearly explaining any visual or spatial elements.
    Respond only in Korean and strictly follow the guidelines below:

    - Ensure that no content is omitted or altered.
    - For diagrams, describe the components, relationships, and directional flows explicitly.  
    - For tables, preserve the original formatting. 
    - For charts or graphics, describe what they represent and how they relate to the surrounding text.  
    - Ignore decorative elements such as logos or purely stylistic graphics.
    - At the end of your output, add a short "요약" section that concisely explains the overall meaning and purpose of this image.
    """

    parser = VLMParser()
    await parser.parse_pdf(PDF_PATH, PROMPT, OUTPUT_PATH)


if __name__ == "__main__":
    asyncio.run(main())
