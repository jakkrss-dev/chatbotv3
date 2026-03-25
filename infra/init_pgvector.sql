CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Vector store table for document RAG.
CREATE TABLE IF NOT EXISTS doc_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Vector similarity index.
CREATE INDEX IF NOT EXISTS doc_chunks_embedding_hnsw_idx
ON doc_chunks USING hnsw (embedding vector_cosine_ops);

-- Structured data tables for SQL RAG.
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

CREATE TABLE IF NOT EXISTS books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2),
    published_date DATE
);

-- Seed data for SQL RAG.
INSERT INTO customers (customer_id, name, region, segment) VALUES
(1, 'Acme Corporation', 'Central', 'Enterprise'),
(2, 'Northwind Trading', 'North', 'SME'),
(3, 'Southern Retail', 'South', 'Retail')
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO products (product_id, name, category, price) VALUES
(1, 'Laptop Pro 15', 'Electronics', 45000.00),
(2, 'Wireless Mouse', 'Accessories', 1200.00),
(3, 'Mechanical Keyboard', 'Accessories', 3500.00)
ON CONFLICT (product_id) DO NOTHING;

INSERT INTO sales (sale_id, customer_id, product_id, qty, sale_date) VALUES
(1, 1, 1, 10, '2024-01-15'),
(2, 1, 2, 10, '2024-01-15'),
(3, 2, 1, 1, '2024-02-10'),
(4, 3, 3, 5, '2024-03-05')
ON CONFLICT (sale_id) DO NOTHING;

-- Seed book catalog.
INSERT INTO books (book_id, title, author, category, price, published_date) VALUES
(1, 'The Great Gatsby', 'F. Scott Fitzgerald', 'Classic', 350.00, '1925-04-10'),
(2, '1984', 'George Orwell', 'Dystopian', 320.00, '1949-06-08'),
(3, 'To Kill a Mockingbird', 'Harper Lee', 'Fiction', 380.00, '1960-07-11'),
(4, 'The Catcher in the Rye', 'J.D. Salinger', 'Fiction', 300.00, '1951-07-16'),
(5, 'The Hobbit', 'J.R.R. Tolkien', 'Fantasy', 450.00, '1937-09-21'),
(6, 'Pride and Prejudice', 'Jane Austen', 'Romance', 280.00, '1813-01-28'),
(7, 'The Chronicles of Narnia', 'C.S. Lewis', 'Fantasy', 550.00, '1950-10-16'),
(8, 'Moby-Dick', 'Herman Melville', 'Adventure', 420.00, '1851-10-18'),
(9, 'War and Peace', 'Leo Tolstoy', 'Historical', 600.00, '1869-01-01'),
(10, 'The Odyssey', 'Homer', 'Epic', 250.00, '1000-01-01'),
(11, 'Brave New World', 'Aldous Huxley', 'Sci-Fi', 340.00, '1932-01-01'),
(12, 'The Alchemist', 'Paulo Coelho', 'Philosophy', 290.00, '1988-01-01'),
(13, 'Dune', 'Frank Herbert', 'Sci-Fi', 480.00, '1965-08-01'),
(14, 'Foundation', 'Isaac Asimov', 'Sci-Fi', 390.00, '1951-01-01'),
(15, 'Neuromancer', 'William Gibson', 'Cyberpunk', 410.00, '1984-07-01'),
(16, 'The Shining', 'Stephen King', 'Horror', 370.00, '1977-01-28'),
(17, 'Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', 'Fantasy', 490.00, '1997-06-26'),
(18, 'The Da Vinci Code', 'Dan Brown', 'Thriller', 360.00, '2003-03-18'),
(19, 'Gone Girl', 'Gillian Flynn', 'Thriller', 330.00, '2012-05-24'),
(20, 'Normal People', 'Sally Rooney', 'Fiction', 310.00, '2018-08-28')
ON CONFLICT (book_id) DO NOTHING;
