export const route = $state({ path: window.location.pathname });

export function navigate(to: string): void {
  if (to !== window.location.pathname) {
    window.history.pushState({}, '', to);
  }
  route.path = to;
}

window.addEventListener('popstate', () => {
  route.path = window.location.pathname;
});
