<script lang="ts">
  let {
    value = $bindable(''),
    type = 'text',
    placeholder = '',
    disabled = false,
    id,
  }: { value?: string; type?: string; placeholder?: string; disabled?: boolean; id?: string } = $props();
</script>

<input {id} {type} {placeholder} {disabled} bind:value class="field" />
