import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import WatchForm from './WatchForm.svelte';
import * as resources from '../api/resources';
import { ApiError } from '../api/client';
import { SECTIONS } from '../constants';
import type { Watch } from '../api/types';

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

  const mixedWatch: Watch = {
    id: 8, client: 1, exclude: [], section: '', active: true,
    groups: [{ terms: [{ text: 'sebrae', kind: 'entity' }, { text: 'contrato', kind: 'concept' }] }],
  } as never;

  it('keeps each term\'s original kind when the row selector is left untouched', async () => {
    const updateWatch = vi.spyOn(resources, 'updateWatch').mockResolvedValue({} as never);
    render(WatchForm, { clients, onsaved: () => {}, watch: mixedWatch });

    await fireEvent.change(screen.getByLabelText(/section/i), { target: { value: 'DO1' } });
    await fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(updateWatch).toHaveBeenCalledWith(8, expect.objectContaining({
      groups: [{ terms: [{ text: 'sebrae', kind: 'entity' }, { text: 'contrato', kind: 'concept' }] }],
    }));
  });

  it('applies the chosen kind to every term when the row selector is changed', async () => {
    const updateWatch = vi.spyOn(resources, 'updateWatch').mockResolvedValue({} as never);
    render(WatchForm, { clients, onsaved: () => {}, watch: mixedWatch });

    await fireEvent.change(screen.getByLabelText(/match kind for group 1/i), { target: { value: 'concept' } });
    await fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(updateWatch).toHaveBeenCalledWith(8, expect.objectContaining({
      groups: [{ terms: [{ text: 'sebrae', kind: 'concept' }, { text: 'contrato', kind: 'concept' }] }],
    }));
  });

  it('gives a newly typed alias the row\'s displayed kind while pre-existing aliases keep theirs', async () => {
    const updateWatch = vi.spyOn(resources, 'updateWatch').mockResolvedValue({} as never);
    render(WatchForm, { clients, onsaved: () => {}, watch: mixedWatch });

    await fireEvent.input(screen.getByLabelText(/aliases for group 1/i),
      { target: { value: 'sebrae, contrato, sebrae/mg' } });
    await fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(updateWatch).toHaveBeenCalledWith(8, expect.objectContaining({
      groups: [{
        terms: [
          { text: 'sebrae', kind: 'entity' },
          { text: 'contrato', kind: 'concept' },
          { text: 'sebrae/mg', kind: 'entity' },
        ],
      }],
    }));
  });

  it('assigns the row kind to every term on a brand-new watch (no prior kinds to preserve)', async () => {
    const createWatch = vi.spyOn(resources, 'createWatch').mockResolvedValue({} as never);
    render(WatchForm, { clients, onsaved: () => {} });

    await fireEvent.input(screen.getByLabelText(/aliases for group 1/i),
      { target: { value: 'sebrae, contrato' } });
    await fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(createWatch).toHaveBeenCalledWith(expect.objectContaining({
      groups: [{ terms: [{ text: 'sebrae', kind: 'entity' }, { text: 'contrato', kind: 'entity' }] }],
    }));
  });
});

describe('WatchForm', () => {
  it('section options match the real pipeline edition codes', () => {
    render(WatchForm, { clients, onsaved: () => {} });
    const values = screen.getAllByRole('option', { name: /seção/i }).map((o) => (o as HTMLOptionElement).value);
    expect(values).toEqual(SECTIONS.map((s) => s.value));
    expect(values).toEqual(['DO1', 'DO2', 'DO3', 'DO1E', 'DO2E', 'DO3E']);
  });

  it('defaults a new watch to "all sections" and posts it that way untouched', async () => {
    const created: Watch = {
      id: 9,
      client: 3,
      groups: [{ terms: [{ text: 'a', kind: 'entity' }] }],
      exclude: [],
      section: '',
      active: true,
    };
    vi.spyOn(resources, 'createWatch').mockResolvedValue(created);
    render(WatchForm, { clients, onsaved: () => {} });

    expect(screen.getByLabelText(/section/i)).toHaveValue('');
    await fireEvent.input(screen.getByLabelText(/aliases for group 1/i), { target: { value: 'a' } });
    await fireEvent.click(screen.getByRole('button', { name: /save/i }));

    expect(resources.createWatch).toHaveBeenCalledWith(expect.objectContaining({ section: '' }));
  });

  it('a 400 field error is shown', async () => {
    vi.spyOn(resources, 'createWatch').mockRejectedValue(
      new ApiError(400, 'request failed', { groups: ['must not be empty'] }),
    );
    render(WatchForm, { clients, onsaved: () => {} });
    await fireEvent.change(screen.getByLabelText(/client/i), { target: { value: '1' } });
    await fireEvent.click(screen.getByRole('button', { name: /save/i }));
    expect(await screen.findByText(/must not be empty/i)).toBeInTheDocument();
  });
});
