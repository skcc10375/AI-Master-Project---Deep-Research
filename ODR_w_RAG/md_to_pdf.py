import pypandoc
import os


def md_to_pdf(md_path):
    # XeLaTeX 경로를 PATH에 추가 (macOS에서 MacTeX 설치 시)
    tex_bin_path = "/Library/TeX/texbin"
    if os.path.exists(tex_bin_path) and tex_bin_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{tex_bin_path}:{os.environ.get('PATH', '')}"

    base_dir = "/Users/seohuipark/Documents/ai_master/ODR_w_RAG/"

    # ✅ LangGraph에서 받은 상대경로(reports/...)를 odr 기준으로 합침
    abs_md_path = md_path
    abs_pdf_path = abs_md_path.replace(".md", ".pdf")

    pypandoc.convert_text(
        open(abs_md_path, encoding="utf-8").read(),
        "pdf",
        format="md",
        outputfile=abs_pdf_path,
        extra_args=[
            "--standalone",
            "--pdf-engine=xelatex",
            "-V",
            "mainfont=Apple SD Gothic Neo",  # macOS 기본 한글 폰트
            "-V",
            "geometry:margin=1in",
            "--toc",
        ],
    )
    print(f"✅ 변환 완료: {abs_pdf_path}")


# 예시 실행
if __name__ == "__main__":
    md_to_pdf("studiooutput/hybrid.md")  # example.md → example.pdf
