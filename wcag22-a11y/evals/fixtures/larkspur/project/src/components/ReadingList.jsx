// ReadingList: user's ordered reading list (source for catalog.html; not built)
import React, { useState } from 'react';

export default function ReadingList({ initialItems }) {
  const [items, setItems] = useState(initialItems);
  const [dragIndex, setDragIndex] = useState(null);

  function handleDrop(targetIndex) {
    if (dragIndex === null || dragIndex === targetIndex) return;
    const next = items.slice();
    const [moved] = next.splice(dragIndex, 1);
    next.splice(targetIndex, 0, moved);
    setItems(next);
    setDragIndex(null);
  }

  return (
    <ol className="reading-list">
      {items.map((title, i) => (
        <li
          key={title}
          draggable="true"
          onDragStart={() => setDragIndex(i)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={() => handleDrop(i)}
        >
          {title}
        </li>
      ))}
    </ol>
  );
}
