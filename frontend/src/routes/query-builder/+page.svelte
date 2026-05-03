<script lang="ts">
	import VisualQueryBuilder from '$lib/components/VisualQueryBuilder.svelte';
	import { goto } from '$app/navigation';
    import { onMount } from 'svelte';

	function handleSendToEditor(sql: string) {
		// Bridge back to Relations page with the query
		goto(`/relations?query=${encodeURIComponent(sql)}`);
	}
</script>

<svelte:head>
	<title>Visual Query Builder | DevBeast</title>
	<meta name="description" content="Design complex SQL JOIN queries visually with interactive table modeling." />
</svelte:head>

<div class="flex-1 flex flex-col min-h-0">
	<header class="flex flex-col gap-3 shrink-0 mb-6">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-4">
				<a
					href="/"
					class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all shadow-sm"
					aria-label="Back to dashboard"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2.5"
							d="M15 19l-7-7 7-7"
						/></svg
					>
				</a>
				<h1
					class="text-4xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none"
				>
					Visual Query Builder<span class="text-indigo-500 uppercase italic">.</span>
				</h1>
			</div>
		</div>
		<p
			class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-[10px] ml-14"
		>
			Interactive Join Modeling & Query Construction
		</p>
	</header>

	<div class="flex-1 flex gap-6 min-h-0 relative">
		<VisualQueryBuilder 
			onCancel={() => goto('/relations')}
			onSendToEditor={handleSendToEditor}
		/>
	</div>
</div>
