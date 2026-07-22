import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import WatchForm from './WatchForm.svelte';
import * as resources from '../api/resources';

const clients = [{ id: 1, name: 'Acme', is_house: false, email: '' }];

beforeEach(() => vi.restoreAllMocks());

describe('WatchForm groups', () => {
  it('submits one group per row with comma-separated aliases ORed inside', async () => {
    const createWatch = vi.spyOn(resources, 'createWatch').mockResolvedValue({} as never);
    render(WatchForm, { clients, onsaved: () => {} });

    await fireEvent.input(screen.getByLabelText(/aliases for group 1/i),
      { target: { value: 'sebrae, sebrae/mg' } });
    await fireEvent.click(screen.getByRole('button', { name: /add group/i }));
    await fireEvent.input(screen.getByLabelText(/aliases for group 2/i),
      { target: { value: 'contrato' } });
    await fireEvent.change(screen.getByLabelText(/match kind for group 2/i),
      { target: { value: 'concept' } });
    await fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(createWatch).toHaveBeenCalledWith(expect.objectContaining({
      groups: [
        { terms: [{ text: 'sebrae', kind: 'entity' }, { text: 'sebrae/mg', kind: 'entity' }] },
        { terms: [{ text: 'contrato', kind: 'concept' }] },
      ],
    }));
  });

  it('seeds rows from an existing watch', () => {
    render(WatchForm, {
      clients,
      onsaved: () => {},
      watch: {
        id: 7, client: 1, exclude: [], section: '', active: true,
        groups: [{ terms: [{ text: 'sebrae', kind: 'entity' }] }],
      } as never,
    });
    expect(screen.getByLabelText(/aliases for group 1/i)).toHaveValue('sebrae');
  });
});
