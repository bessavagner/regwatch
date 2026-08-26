import { afterEach, expect, test, vi } from 'vitest';
import * as resources from '../api/resources';
import { loadVocabulary, vocabulary } from './vocabulary.svelte';

afterEach(() => {
  vi.restoreAllMocks();
  vocabulary.categories = [];
});

test('loads the categories in the order the API sent them', async () => {
  vi.spyOn(resources, 'getVocabulary').mockResolvedValue({
    categories: [
      { value: 'tender', label: 'licitação' },
      { value: 'other', label: 'outro' },
    ],
  });
  await loadVocabulary();
  expect(vocabulary.categories.map((c) => c.value)).toEqual(['tender', 'other']);
  expect(vocabulary.categories[0].label).toBe('licitação');
});

test('a failed fetch leaves the list empty rather than throwing', async () => {
  vi.spyOn(resources, 'getVocabulary').mockRejectedValue(new Error('offline'));
  await expect(loadVocabulary()).resolves.toBeUndefined();
  expect(vocabulary.categories).toEqual([]);
});
