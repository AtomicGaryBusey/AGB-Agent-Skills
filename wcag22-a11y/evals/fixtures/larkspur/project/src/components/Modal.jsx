// Modal: event reservation dialog (source for events.html; not built)
import React, { useEffect, useRef } from 'react';

export default function Modal({ open, title, onClose, children }) {
  const firstFieldRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const first = firstFieldRef.current && firstFieldRef.current.querySelector('input');
    if (first) first.focus();

    function onKeyDown(e) {
      if (e.key === 'Tab') {
        e.preventDefault();
        if (first) first.focus();
      }
      if (e.key === 'Escape') {
        e.preventDefault();
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open]);

  if (!open) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <span className="close" onClick={onClose}>&times;</span>
        <h2 id="modal-title">{title}</h2>
        <div ref={firstFieldRef}>{children}</div>
      </div>
    </div>
  );
}
