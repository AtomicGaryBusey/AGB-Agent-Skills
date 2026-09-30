import React, { useState } from 'react';

type Props<T> = { items: T[]; label: string };
const identity = <T,>(value: T) => value;

export function GoodCard<T extends string>({ items, label }: Props<T>) {
  const [open, setOpen] = useState<boolean>(false);
  const n = items.length < 3 ? 1 : 2;
  return (
    <section className="card" aria-labelledby="card-title">
      <h2 id="card-title">{label}</h2>
      <img src="/avatar.png" alt="" />
      <button type="button" aria-expanded={open} onClick={() => setOpen(!open)}>
        Details
      </button>
      <a href="/profile" aria-label="Profile"><UserIcon aria-hidden="true" /></a>
      <button aria-label="Delete item">Delete</button>
      <label htmlFor="em">Email</label>
      <input id="em" type="email" autoComplete="email" />
      <Field label="Name"><input name="name" autoComplete="name" /></Field>
      <div role="switch" aria-checked={open} tabIndex={0} aria-label="Dark mode" onKeyDown={() => {}} onClick={() => {}} />
      <p style={{ color: '#222', backgroundColor: '#fff' }}>Readable</p>
      <ul>{items.map((i) => <li key={i}>{i}</li>)}</ul>
      <div role="status" aria-live="polite" className="toast">{open ? 'Open' : ''}</div>
      <img {...imgProps} />
      <button {...buttonProps} />
      {open && <p>{`Showing ${n} items`}</p>}
    </section>
  );
}
