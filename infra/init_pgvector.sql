CREATE EXTENSION IF NOT EXISTS vector;

-- ตารางสำหรับ Vector Store (Document RAG)
CREATE TABLE IF NOT EXISTS doc_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- สร้าง Index สำหรับการค้นหา Vector ให้เร็วขึ้น (HNSW)
CREATE INDEX ON doc_chunks USING hnsw (embedding vector_cosine_ops);

-- ตารางสำหรับ SQL RAG (Business Data)
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(100),
    segment VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2)
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    product_id INTEGER REFERENCES products(product_id),
    qty INTEGER NOT NULL,
    sale_date DATE NOT NULL
);

-- ข้อมูลจำลองสำหรับ SQL RAG
INSERT INTO customers (name, region, segment) VALUES
('บริษัท อัลฟ่า จำกัด', 'ภาคกลาง', 'Enterprise'),
('คุณสมชาย ใจดี', 'ภาคเหนือ', 'SME'),
('ร้านค้านายเอก', 'ภาคใต้', 'Retail');

INSERT INTO products (name, category, price) VALUES
('Laptop Pro 15', 'Electronics', 45000.00),
('Wireless Mouse', 'Accessories', 1200.00),
('Mechanical Keyboard', 'Accessories', 3500.00);

INSERT INTO sales (customer_id, product_id, qty, sale_date) VALUES
(1, 1, 10, '2024-01-15'),
(1, 2, 10, '2024-01-15'),
(2, 1, 1, '2024-02-10'),
(3, 3, 5, '2024-03-05');

-- ตารางสำหรับข้อมูลหนังสือ
CREATE TABLE IF NOT EXISTS books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2),
    published_date DATE
);

-- ข้อมูลจำลองสำหรับหนังสือ 20 เล่ม
INSERT INTO books (title, author, category, price, published_date) VALUES
('The Great Gatsby', 'F. Scott Fitzgerald', 'Classic', 350.00, '1925-04-10'),
('1984', 'George Orwell', 'Dystopian', 320.00, '1949-06-08'),
('To Kill a Mockingbird', 'Harper Lee', 'Fiction', 380.00, '1960-07-11'),
('The Catcher in the Rye', 'J.D. Salinger', 'Fiction', 300.00, '1951-07-16'),
('The Hobbit', 'J.R.R. Tolkien', 'Fantasy', 450.00, '1937-09-21'),
('Pride and Prejudice', 'Jane Austen', 'Romance', 280.00, '1813-01-28'),
('The Chronicles of Narnia', 'C.S. Lewis', 'Fantasy', 550.00, '1950-10-16'),
('Moby-Dick', 'Herman Melville', 'Adventure', 420.00, '1851-10-18'),
('War and Peace', 'Leo Tolstoy', 'Historical', 600.00, '1869-01-01'),
('The Odyssey', 'Homer', 'Epic', 250.00, '1000-01-01'),
('Brave New World', 'Aldous Huxley', 'Sci-Fi', 340.00, '1932-01-01'),
('The Alchemist', 'Paulo Coelho', 'Philosophy', 290.00, '1988-01-01'),
('Dune', 'Frank Herbert', 'Sci-Fi', 480.00, '1965-08-01'),
('Foundation', 'Isaac Asimov', 'Sci-Fi', 390.00, '1951-01-01'),
('Neuromancer', 'William Gibson', 'Cyberpunk', 410.00, '1984-07-01'),
('The Shining', 'Stephen King', 'Horror', 370.00, '1977-01-28'),
('Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', 'Fantasy', 490.00, '1997-06-26'),
('The Da Vinci Code', 'Dan Brown', 'Thriller', 360.00, '2003-03-18'),
('Gone Girl', 'Gillian Flynn', 'Thriller', 330.00, '2012-05-24'),
('Normal People', 'Sally Rooney', 'Fiction', 310.00, '2018-08-28');
