import sys
import os
from datetime import date
from decimal import Decimal

# Add the project root to sys.path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.database import engine, Base, SessionLocal, Book

def init_books():
    print("Creating books table...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if books already exist to avoid duplicates if run multiple times
        count = db.query(Book).count()
        if count > 0:
            print(f"Books table already has {count} records. Skipping seeding.")
            return

        print("Seeding 20 books...")
        sample_books = [
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald", category="Classic", price=Decimal("299.00"), published_date=date(1925, 4, 10)),
            Book(title="1984", author="George Orwell", category="Dystopian", price=Decimal("350.00"), published_date=date(1949, 6, 8)),
            Book(title="To Kill a Mockingbird", author="Harper Lee", category="Fiction", price=Decimal("320.00"), published_date=date(1960, 7, 11)),
            Book(title="จิตวิทยาสายดาร์ก", author="Dr. Hiro", category="Psychology", price=Decimal("250.00"), published_date=date(2021, 1, 1)),
            Book(title="Harry Potter and the Sorcerer's Stone", author="J.K. Rowling", category="Fantasy", price=Decimal("450.00"), published_date=date(1997, 6, 26)),
            Book(title="The Hobbit", author="J.R.R. Tolkien", category="Fantasy", price=Decimal("380.00"), published_date=date(1937, 9, 21)),
            Book(title="ถอดรหัสลับสมองมั่งคั่ง", author="T. Harv Eker", category="Finance", price=Decimal("280.00"), published_date=date(2005, 2, 15)),
            Book(title="Atomic Habits", author="James Clear", category="Self-help", price=Decimal("395.00"), published_date=date(2018, 10, 16)),
            Book(title="คิดแบบยิบซอ", author="Shunmyo Masuno", category="Self-help", price=Decimal("220.00"), published_date=date(2019, 5, 20)),
            Book(title="The Catcher in the Rye", author="J.D. Salinger", category="Fiction", price=Decimal("290.00"), published_date=date(1951, 7, 16)),
            Book(title="Sapiens: A Brief History of Humankind", author="Yuval Noah Harari", category="History", price=Decimal("590.00"), published_date=date(2011, 1, 1)),
            Book(title="Principia", author="Isaac Newton", category="Science", price=Decimal("950.00"), published_date=date(1687, 7, 5)),
            Book(title="พ่อรวยสอนลูก", author="Robert Kiyosaki", category="Finance", price=Decimal("250.00"), published_date=date(1997, 1, 1)),
            Book(title="The Alchemist", author="Paulo Coelho", category="Philosophy", price=Decimal("310.00"), published_date=date(1988, 1, 1)),
            Book(title="Deep Work", author="Cal Newport", category="Business", price=Decimal("420.00"), published_date=date(2016, 1, 5)),
            Book(title="Clean Code", author="Robert C. Martin", category="Programming", price=Decimal("1200.00"), published_date=date(2008, 8, 1)),
            Book(title="The Pragmatic Programmer", author="Andrew Hunt", category="Programming", price=Decimal("1100.00"), published_date=date(1999, 10, 30)),
            Book(title="สตาร์ทอัพสร้างได้", author="Eric Ries", category="Business", price=Decimal("350.00"), published_date=date(2011, 9, 13)),
            Book(title="Brave New World", author="Aldous Huxley", category="Dystopian", price=Decimal("330.00"), published_date=date(1932, 1, 1)),
            Book(title="The Art of War", author="Sun Tzu", category="Strategy", price=Decimal("199.00"), published_date=date(2000, 1, 1)),
        ]
        
        db.add_all(sample_books)
        db.commit()
        print("Successfully seeded 20 books.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding books: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_books()
