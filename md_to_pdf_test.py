import pypandoc
import os

def md_to_pdf(md_path):
    
    base_dir = "/Users/a11434/workspace/AI-Master-Project---Deep-Research/odr"
    
    # ✅ LangGraph에서 받은 상대경로(reports/...)를 odr 기준으로 합침
    abs_md_path = os.path.join(base_dir, md_path)
    abs_pdf_path = abs_md_path.replace(".md", ".pdf")
    
    pypandoc.convert_text(
        open(abs_md_path, encoding="utf-8").read(),
        "pdf",
        format="md",
        outputfile=abs_pdf_path,
        extra_args=[
            "--standalone",
            "--pdf-engine=xelatex",
            "-V", "mainfont=Apple SD Gothic Neo",  # macOS 기본 한글 폰트
            "-V", "geometry:margin=1in",
            "--toc"
        ]
    )
    print(f"✅ 변환 완료: {abs_pdf_path}")

# 예시 실행
if __name__ == "__main__":
    md_to_pdf("reports/open_deep_research_20251112_205843.md")  # example.md → example.pdf