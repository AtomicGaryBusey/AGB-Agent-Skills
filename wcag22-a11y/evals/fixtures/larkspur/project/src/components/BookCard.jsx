// BookCard: one catalog result (source for catalog.html; not built)
import React from 'react';

export default function BookCard({ book, onAdd }) {
  return (
    <li className="book-card">
      <img src={book.coverUrl} />
      <div>
        <h2>
          <a href={`/catalog?item=${book.slug}`}>{book.title}</a>
        </h2>
        <p>
          {book.author} &middot; {book.format} &middot; {book.availability}
        </p>
        <div className="btn add-btn" onClick={() => onAdd(book)}>
          Add to reading list
        </div>
      </div>
    </li>
  );
}
