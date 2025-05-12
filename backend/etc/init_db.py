"""
Database initialization script
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import Base and models
from backend.models import Base, init_models, get_db
from backend.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def drop_all_tables(engine):
    """Drop all tables in the database"""
    with engine.connect() as conn:
        # Disable foreign key checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        # Get all table names
        result = conn.execute(text("SHOW TABLES;"))
        tables = [row[0] for row in result]
        
        # Drop all tables
        for table in tables:
            logger.info(f"Dropping table: {table}")
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`;"))
        
        # Re-enable foreign key checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        conn.commit()

def init_db():
    """Initialize the database with default data"""
    try:
        # Connect to the database
        engine = create_engine(settings.DATABASE_URL)
        
        # Initialize models to ensure all tables are registered
        models = init_models()
        
        # Drop all existing tables
        logger.info("Dropping existing tables...")
        drop_all_tables(engine)
        
        # Create tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Get a database session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if data already exists
            from backend.models import Country
            country_count = db.query(Country).count()
            
            if country_count > 0:
                logger.info("Database already initialized.")
                return
            
            # Insert default countries
            logger.info("Inserting default countries...")
            countries = [
                Country(name="Australia", code="AU", enabled=True),
                Country(name="Canada", code="CA", enabled=True),
                Country(name="France", code="FR", enabled=True)
            ]
            db.add_all(countries)
            db.commit()
            
            # Refresh to get IDs
            for country in countries:
                db.refresh(country)
            
            # Insert default topics
            logger.info("Inserting default topics...")
            from backend.models import Topic
            topics = [
                Topic(name="visa", code="visa", enabled=True),
                Topic(name="insurance", code="insurance", enabled=True),
                Topic(name="immigration", code="immigration", enabled=True)
            ]
            db.add_all(topics)
            db.commit()
            
            # Refresh to get IDs
            for topic in topics:
                db.refresh(topic)
            
            # Insert default sources
            logger.info("Inserting default sources...")
            from backend.models import Source
            sources = [
                Source(name="Government Website", url="", source_type="GOVERNMENT"),
                Source(name="Embassy", url="", source_type="EMBASSY"),
                Source(name="Immigration Department", url="", source_type="GOVERNMENT")
            ]
            db.add_all(sources)
            db.commit()
            
            # Insert required items for countries
            logger.info("Inserting required items for countries...")
            
            # Australia
            from backend.models import RequiredItem
            au_items = [
                RequiredItem(country_id=countries[0].id, item="6개월 이상 유효한 여권"),
                RequiredItem(country_id=countries[0].id, item="ETA(전자비자) 또는 워킹홀리데이/학생비자 승인서"),
                RequiredItem(country_id=countries[0].id, item="왕복 항공권 및 예약증명서"),
                RequiredItem(country_id=countries[0].id, item="해외여행자 보험 가입 확인서"),
                RequiredItem(country_id=countries[0].id, item="현지 숙소 예약 내역"),
                RequiredItem(country_id=countries[0].id, item="비상연락처(영사관 등)")
            ]
            db.add_all(au_items)
            
            # Canada
            ca_items = [
                RequiredItem(country_id=countries[1].id, item="여권(잔여기간 확인)"),
                RequiredItem(country_id=countries[1].id, item="eTA(전자여행 허가) 또는 비자"),
                RequiredItem(country_id=countries[1].id, item="입국 심사/질문 대비 서류(방문 목적 등)"),
                RequiredItem(country_id=countries[1].id, item="여행자 보험 가입서류"),
                RequiredItem(country_id=countries[1].id, item="왕복 항공권"),
                RequiredItem(country_id=countries[1].id, item="체류지 주소/연락처")
            ]
            db.add_all(ca_items)
            
            # France
            fr_items = [
                RequiredItem(country_id=countries[2].id, item="여권(잔여기간 6개월)"),
                RequiredItem(country_id=countries[2].id, item="유럽여행자 보험(Schengen)"),
                RequiredItem(country_id=countries[2].id, item="프랑스 비자(필요 시)"),
                RequiredItem(country_id=countries[2].id, item="왕복 항공권 또는 출국 증빙"),
                RequiredItem(country_id=countries[2].id, item="프랑스 내 숙소 예약확인서"),
                RequiredItem(country_id=countries[2].id, item="재정 증명 관련 서류")
            ]
            db.add_all(fr_items)
            
            # Commit all required items
            db.commit()
            
            # Insert FAQs
            logger.info("Inserting FAQs...")
            
            # Australia visa FAQs
            from backend.models import FAQ
            au_visa_faqs = [
                FAQ(
                    question="호주 워킹홀리데이 비자 신청 방법은?",
                    answer="호주 워킹홀리데이 비자는 호주 이민성 웹사이트에서 온라인으로 신청 가능합니다. 신청 시 여권, 재정증명, 영문 이력서가 필요합니다.",
                    country_id=countries[0].id,
                    topic_id=topics[0].id
                ),
                FAQ(
                    question="호주 학생비자 준비 서류가 뭐에요?",
                    answer="호주 학생비자 신청 시 필요 서류: 여권, 입학허가서(CoE), 재정증명서, 영어능력증명(IELTS 등), GTE(Genuine Temporary Entrant) 신고서 등이 필요합니다.",
                    country_id=countries[0].id,
                    topic_id=topics[0].id
                ),
                FAQ(
                    question="비자 승인 대략 기간은 얼마나 걸리나요?",
                    answer="호주 비자 종류에 따라 처리 기간이 다릅니다. 일반적으로 워킹홀리데이 비자는 2주-2개월, 학생비자는 4-6주, 관광비자는 1-4주 정도 소요됩니다.",
                    country_id=countries[0].id,
                    topic_id=topics[0].id
                ),
                FAQ(
                    question="비자 신청 수수료가 있나요?",
                    answer="호주 비자 신청 시 수수료가 부과됩니다. 워킹홀리데이 비자는 약 AUD 510, 학생비자는 약 AUD 630, 관광비자는 약 AUD 145 정도입니다 (2024년 기준).",
                    country_id=countries[0].id,
                    topic_id=topics[0].id
                )
            ]
            db.add_all(au_visa_faqs)
            
            # France insurance FAQs
            fr_insurance_faqs = [
                FAQ(
                    question="프랑스에서 필수 보험 종류는?",
                    answer="프랑스 방문/체류 시 여행자 보험은 필수입니다. 솅겐 비자 신청 시에는 최소 보장금액 30,000€ 이상의 의료보험이 필요합니다.",
                    country_id=countries[2].id,
                    topic_id=topics[1].id
                ),
                FAQ(
                    question="여행자 보험 가입 조건을 알려주세요.",
                    answer="프랑스 여행자 보험은 의료비, 응급 후송, 배상 책임을 포함해야 합니다. 솅겐 지역 전체를 보장하며 체류 기간 전체를 커버하는 보험이어야 합니다.",
                    country_id=countries[2].id,
                    topic_id=topics[1].id
                ),
                FAQ(
                    question="보험 청구 절차는 어떻게 되나요?",
                    answer="보험 청구 시 병원 영수증, 의사 진단서, 처방전 등 원본을 보관해야 합니다. 대부분의 보험사는 온라인 청구 시스템을 갖추고 있으며, 현지에서 긴급 상황 시 보험사 긴급 연락처로 먼저 연락하는 것이 좋습니다.",
                    country_id=countries[2].id,
                    topic_id=topics[1].id
                )
            ]
            db.add_all(fr_insurance_faqs)
            
            # Canada immigration FAQs
            ca_immigration_faqs = [
                FAQ(
                    question="캐나다 영주권 신청 방법은?",
                    answer="캐나다 영주권은 Express Entry, 주정부 이민 프로그램(PNP), 가족 초청 등 여러 경로가 있습니다. Express Entry는 학력, 경력, 언어능력 등을 점수화하여 선발하는 시스템입니다.",
                    country_id=countries[1].id,
                    topic_id=topics[2].id
                ),
                FAQ(
                    question="캐나다 Express Entry 자격 요건은?",
                    answer="Express Entry는 연방 기술 이민(FSW), 캐나다 경험 이민(CEC), 연방 기술 직종(FST) 프로그램이 있습니다. 공통적으로 언어능력(영어/프랑스어), 학력, 직무경력, 적응능력 등이 평가됩니다.",
                    country_id=countries[1].id,
                    topic_id=topics[2].id
                ),
                FAQ(
                    question="영주권 신청 후 처리 기간은?",
                    answer="캐나다 영주권 처리 기간은 신청 경로에 따라 다릅니다. Express Entry는 6-8개월, 주정부 이민(PNP)은 15-19개월, 가족 초청은 12-24개월 정도 소요됩니다.",
                    country_id=countries[1].id,
                    topic_id=topics[2].id
                )
            ]
            db.add_all(ca_immigration_faqs)
            
            # Commit all FAQs
            db.commit()
            
            logger.info("Database initialization completed successfully.")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error during database initialization: {e}")
            raise
        finally:
            db.close()
            
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting database initialization...")
    init_db()