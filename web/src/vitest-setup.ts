import '@testing-library/jest-dom/vitest';

// jsdom ships <dialog> but not showModal()/close(), so a component that opens
// one throws under test while working fine in every real browser. Stub the two
// methods onto the prototype, keeping the `open` attribute honest so
// jsdom's UA stylesheet still hides a closed dialog from the queries.
if (typeof HTMLDialogElement !== 'undefined' && !HTMLDialogElement.prototype.showModal) {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.open = true;
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.open = false;
    this.dispatchEvent(new Event('close'));
  };
}
