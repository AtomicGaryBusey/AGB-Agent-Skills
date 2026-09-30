// SearchBar: catalog search form (source for catalog.html; not built)
import React, { useState } from 'react';

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    onSearch(query);
  }

  return (
    <form className="search-row" role="search" onSubmit={handleSubmit}>
      <input
        type="search"
        id="q"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button type="submit" className="icon-btn">
        <img src="/images/icon-search.svg" alt="" />
      </button>
    </form>
  );
}
