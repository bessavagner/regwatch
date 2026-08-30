import { render, screen, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';
import CommandPalette from './CommandPalette.svelte';
import { TRIAGE_SHORTCUTS, type Command } from '../commands';
import * as router from '../router/router.svelte';

const ROUTES: Command[] = [
  { kind: 'route', label: 'triagem', path: '/feed' },
  { kind: 'route', label: 'buscas', path: '/watches' },
];
const COMMANDS: Command[] = [...ROUTES, ...TRIAGE_SHORTCUTS];

async function open(commands: Command[] = COMMANDS) {
  const user = userEvent.setup();
  render(CommandPalette, { commands });
  await user.keyboard('{Control>}k{/Control}');
  return user;
}

test('ctrl+k opens the palette and lists the routes', async () => {
  await open();
  await waitFor(() => expect(screen.getByRole('option', { name: /triagem/i })).toBeInTheDocument());
  expect(screen.getByRole('option', { name: /buscas/i })).toBeInTheDocument();
});

test('the triage shortcuts are discoverable, with their keys', async () => {
  await open();
  await waitFor(() => expect(screen.getByText(/marcar como relevante/i)).toBeInTheDocument());
  expect(screen.getByText(/arquivar/i)).toBeInTheDocument();
  // The key itself, not just the description — otherwise it is not discoverable.
  expect(screen.getByText('R')).toBeInTheDocument();
  expect(screen.getByText('J')).toBeInTheDocument();
});

test('enter navigates to the selected route', async () => {
  const navigate = vi.spyOn(router, 'navigate').mockImplementation(() => {});
  const user = await open();
  await waitFor(() => expect(screen.getByRole('option', { name: /triagem/i })).toBeInTheDocument());
  await user.keyboard('{Enter}');
  expect(navigate).toHaveBeenCalledWith('/feed');
});

test('a shortcut is never navigated to, only read', async () => {
  const navigate = vi.spyOn(router, 'navigate').mockImplementation(() => {});
  const user = await open();
  // "relevante" matches only a shortcut, so there is no route left to choose.
  await user.keyboard('relevante');
  await waitFor(() => expect(screen.getByText(/marcar como relevante/i)).toBeInTheDocument());
  await user.keyboard('{Enter}');
  expect(navigate).not.toHaveBeenCalled();
});

test('the query filters routes and shortcuts alike', async () => {
  const user = await open();
  await user.keyboard('busca');
  await waitFor(() => expect(screen.getByRole('option', { name: /buscas/i })).toBeInTheDocument());
  expect(screen.queryByRole('option', { name: /triagem/i })).not.toBeInTheDocument();
  expect(screen.queryByText(/marcar como relevante/i)).not.toBeInTheDocument();
});
