<script lang="ts">
  import Button from '../lib/ui/Button.svelte';
  import Input from '../lib/ui/Input.svelte';
  import Card from '../lib/ui/Card.svelte';
  import { auth } from '../lib/stores/auth.svelte';
  import { navigate } from '../lib/router/router.svelte';

  let username = $state('');
  let password = $state('');

  async function submit(e: SubmitEvent) {
    e.preventDefault();
    await auth.login(username, password);
    if (auth.status === 'authed') navigate('/feed');
  }
</script>

<main class="mx-auto mt-16 max-w-sm p-6">
  <Card>
    <h1 class="mb-4 text-lg font-semibold text-brand-600">RegWatch</h1>
    <form onsubmit={submit} class="space-y-3">
      <div>
        <label for="username" class="mb-1 block text-sm">Username</label>
        <Input id="username" bind:value={username} />
      </div>
      <div>
        <label for="password" class="mb-1 block text-sm">Password</label>
        <Input id="password" type="password" bind:value={password} />
      </div>
      {#if auth.error}
        <p role="alert" class="text-sm text-red-600">{auth.error}</p>
      {/if}
      <Button type="submit">Sign in</Button>
    </form>
  </Card>
</main>
