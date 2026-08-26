import { getVocabulary } from '../api/resources';
import type { VocabularyItem } from '../api/types';

export const vocabulary = $state<{ categories: VocabularyItem[] }>({ categories: [] });

export async function loadVocabulary(): Promise<void> {
  try {
    vocabulary.categories = (await getVocabulary()).categories;
  } catch {
    // Degrades to a dropdown offering only "all". Match badges carry their own
    // label from the API, so a failure here never puts English on screen.
    vocabulary.categories = [];
  }
}
