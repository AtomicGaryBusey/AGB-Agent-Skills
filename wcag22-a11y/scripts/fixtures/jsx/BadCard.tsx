import React, { useState } from 'react';
import { useSortable } from '@dnd-kit/sortable';

type Props<T> = { items: T[]; onRemove: (id: string) => void };
const identity = <T,>(value: T) => value;

export function BadCard<T extends string>({ items, onRemove }: Props<T>) {
  const [open, setOpen] = useState<boolean>(false);
  const tooMany = items.length < 10 && items.length > 2;
  return (
    <section className="card">
      <img src="/avatar.png" />
      <span className="caret" onClick={() => setOpen(!open)}>Details</span>
      <a href="/profile"><UserIcon /></a>
      <button aria-label="Remove item">Delete</button>
      <input type="email" placeholder="Email" />
      <div role="switch" tabIndex={0} aria-label="Dark mode" onKeyDown={() => {}} onClick={() => {}} />
      <p style={{ color: '#999', backgroundColor: '#fff' }}>Muted text</p>
      <input type="password" onPaste={(e) => e.preventDefault()} autoComplete="current-password" aria-label="Password" />
      <select aria-label="Sort" onChange={(e) => router.push(e.target.value)}><option>A</option></select>
      {items.map((i) => <li key={i}>{i}</li>)}
      {/* a JSX comment */}
      <div className="toast">Saved</div>
    </section>
  );
}
