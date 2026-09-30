// Carousel: "What's new" rotating panel (source for index.html; not built)
import React, { useEffect, useState } from 'react';

export default function Carousel({ slides, intervalMs = 4000 }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % slides.length);
    }, intervalMs);
    return () => clearInterval(id);
  }, [slides.length, intervalMs]);

  return (
    <div className="carousel">
      <div
        className="carousel-track"
        style={{ transform: `translateX(${-100 * index}%)` }}
      >
        {slides.map((s) => (
          <div className="slide" key={s.id}>
            <h3>{s.heading}</h3>
            <p>{s.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
