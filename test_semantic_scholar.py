"""
Semantic Scholar API 테스트 스크립트
실제 검색을 수행하여 5개 논문 출력
"""
import json
from app.utils.logger import LoggerSetup, log_execution_time
from app.services.semantic_scholar import SemanticScholarService

logger = LoggerSetup.setup(
    log_file="semantic_scholar_test.log",
    level="DEBUG",
    console_level="INFO"
)

@log_execution_time
def test_search_papers():
    """논문 검색 테스트"""
    print("=" * 80)
    print("🔍 Semantic Scholar API 논문 검색 테스트")
    print("=" * 80)

    # 서비스 초기화
    print("\n[1단계] SemanticScholarService 초기화...")
    service = SemanticScholarService()  # API Key 없이 무료 사용
    print("✅ 초기화 완료\n")

    # 검색 파라미터
    keyword = "transformer recommendation system"
    year_from = 2020
    year_to = 2025
    limit = 5  # 5개 논문

    print(f"[2단계] 논문 검색 중...")
    print(f"  - 키워드: {keyword}")
    print(f"  - 연도: {year_from} - {year_to}")
    print(f"  - 개수: {limit}개")
    print()

    try:
        # 논문 검색
        papers = service.search_papers(
            keyword=keyword,
            year_from=year_from,
            year_to=year_to,
            limit=limit
        )

        print(f"✅ 검색 완료: {len(papers)}개 논문 발견\n")
        print("=" * 80)
        print("📄 검색 결과 (Citation 순)")
        print("=" * 80)

        # 결과 출력
        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}] {paper['title']}")
            print(f"    저자: {', '.join(paper['authors'][:3])}{' 외' if len(paper['authors']) > 3 else ''}")
            print(f"    연도: {paper['year']}")
            print(f"    컨퍼런스/저널: {paper['venue']}")
            print(f"    인용수: {paper['citations']}")
            print(f"    URL: {paper['url']}")
            if paper.get('doi'):
                print(f"    DOI: {paper['doi']}")
            if paper.get('pdf_url'):
                print(f"    PDF: {paper['pdf_url']}")
            if paper.get('abstract'):
                abstract_preview = paper['abstract'][:150] + "..." if len(paper['abstract']) > 150 else paper['abstract']
                print(f"    초록: {abstract_preview}")

        print("\n" + "=" * 80)

        # JSON 저장
        output_file = "test_papers_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'query': keyword,
                'year_range': f"{year_from}-{year_to}",
                'total_results': len(papers),
                'papers': papers
            }, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 결과가 {output_file}에 저장되었습니다.")
        print("\n테스트 성공! 🎉")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_papers()

