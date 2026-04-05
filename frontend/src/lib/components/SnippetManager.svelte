<script lang="ts">
	import { workspaceStore } from '$lib/stores/workspaceStore';
	import { goto } from '$app/navigation';

	function replaySnippet(query: string) {
		const params = new URLSearchParams();
		params.set('sql', query);
		goto(`/database?${params.toString()}`);
	}

	async function deleteSnippet(id: string) {
		if (confirm('Permanently delete this snippet?')) {
			await workspaceStore.deleteSnippet(id);
		}
	}
</script>

<div class="flex flex-col h-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
	<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 flex items-center justify-between">
		<div>
			<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest">Logic Snippets</h3>
			<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Reusable SQL blocks for your workspace</p>
		</div>
		<div class="flex items-center gap-2">
			<span class="px-3 py-1 rounded-full bg-violet-500/10 text-violet-500 text-[10px] font-black uppercase tracking-widest border border-violet-500/20">
				{$workspaceStore.snippets.length} Saved
			</span>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-4">
		{#each $workspaceStore.snippets as snip (snip.id)}
			<div class="group flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden hover:border-violet-500/40 transition-all shadow-sm hover:shadow-xl">
				<div class="flex items-center justify-between p-4 bg-slate-50/50 dark:bg-slate-950/20 border-b border-slate-200 dark:border-slate-800">
					<div>
						<h4 class="text-xs font-black text-slate-800 dark:text-white uppercase tracking-widest italic">{snip.name}</h4>
						<div class="flex flex-wrap gap-1 mt-2">
							{#each snip.tags as tag}
								<span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 text-[9px] font-black uppercase tracking-widest">#{tag}</span>
							{/each}
						</div>
					</div>
					<div class="flex items-center gap-2">
						<button 
							onclick={() => deleteSnippet(snip.id)}
							class="w-8 h-8 rounded-xl bg-rose-500/10 text-rose-500 flex items-center justify-center hover:bg-rose-500 hover:text-white transition-all shadow-lg shadow-rose-500/10"
							title="Delete snippet"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
						</button>
						<button 
							onclick={() => replaySnippet(snip.query)}
							class="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-violet-500/20 active:scale-95 flex items-center gap-2"
						>
							<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
							Inject Logic
						</button>
					</div>
				</div>
				<div class="p-4 bg-slate-950">
					<pre class="text-[11px] font-mono font-medium text-slate-300 whitespace-pre-wrap overflow-x-auto selection:bg-violet-500/30 selection:text-white">{snip.query}</pre>
				</div>
			</div>
		{:else}
			<div class="flex flex-col items-center justify-center h-full text-slate-500 gap-4 opacity-50 py-20">
				<div class="text-6xl">🏢</div>
				<p class="text-xs font-black uppercase tracking-[0.3em]">No Logic Saved</p>
				<p class="text-[10px] font-bold uppercase tracking-widest text-center">Save complex queries as snippets to automate your workflow</p>
			</div>
		{/each}
	</div>
</div>
