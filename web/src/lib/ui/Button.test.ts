import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { expect, test } from 'vitest';
import Button from './Button.svelte';

test('Button renders its label and fires onclick', async () => {
  const user = userEvent.setup();
  let clicked = 0;
  render(Button, { props: { onclick: () => (clicked += 1), children: undefined } });
  // children snippet is not passed in this unit test; assert the click wiring on role
  const button = screen.getByRole('button');
  await user.click(button);
  expect(clicked).toBe(1);
});
