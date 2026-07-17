export const route = $state({ path: window.location.pathname });

export function navigate(to: string): void {
  const path = to.split('?')[0];
  const current = window.location.pathname + window.location.search;
  if (to !== current) {
    window.history.pushState({}, '', to);
  }
  route.path = path;
}

window.addEventListener('popstate', () => {
  route.path = window.location.pathname;
});
