<script lang="ts">
	import { workspaceStore, type Snippet } from '$lib/stores/workspaceStore';
	import { fade, slide } from 'svelte/transition';
	import { flip } from 'svelte/animate';
	import { goto } from '$app/navigation';

	let searchQuery = $state('');
	
	// Group snippets: Favorites first, then by last used
	let sortedSnippets = $derived([...$workspaceStore.snippets].sort((a, b) => {
		if (a.is_favorite && !b.is_favorite) return -1;
		if (!a.is_favorite && b.is_favorite) return 1;
		return new Date(b.last_used).getTime() - new Date(a.last_used).getTime();
	}).filter(s => s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
				   s.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))));

	let favorites = $derived(sortedSnippets.filter(s => s.is_favorite));
	let regular = $derived(sortedSnippets.filter(s => !s.is_favorite));

	async function useSnippet(snippet: Snippet) {
		await workspaceStore.trackSnippetUsage(snippet.id);
		const params = new URLSearchParams();
		params.set('sql', snippet.query);
		goto(`/database?${params.toString()}`);
	}

	function toggleFav(id: string) {
		workspaceStore.toggleFavorite(id);
	}
</script>

<div class="flex flex-col h-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
	<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 flex flex-col gap-6">
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest">Logic Glossary</h3>
				<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1 italic tracking-widest leading-none">Persistent Snippet Registry</p>
			</div>
			<div class="flex items-center gap-2">
				<span class="px-3 py-1 rounded-full bg-amber-500/10 text-amber-500 text-[10px] font-black uppercase tracking-widest border border-amber-500/20 shadow-sm">
					{favorites.length} Pinned
				</span>
			</div>
		</div>

		<div class="relative">
			<input 
				type="text" 
				placeholder="Search by name or tags..." 
				bind:value={searchQuery}
				class="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2 text-[10px] font-bold focus:ring-4 focus:ring-indigo-500/10 transition-all outline-none"
			/>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-10">
		{#if favorites.length > 0}
			<div class="space-y-4">
				<div class="flex items-center gap-3">
					<span class="text-[9px] font-black text-amber-500 uppercase tracking-[0.3em] italic">Pinned Assets</span>
					<div class="h-px bg-amber-100 dark:bg-amber-900/30 flex-1"></div>
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					{#each favorites as snippet (snippet.id)}
						<div animate:flip={{duration: 400}} transition:fade>
							{@render SnippetCard({ snippet })}
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if regular.length > 0}
			<div class="space-y-4">
				<div class="flex items-center gap-3">
					<span class="text-[9px] font-black text-slate-400 uppercase tracking-[0.3em] italic">Library</span>
					<div class="h-px bg-slate-100 dark:bg-slate-800 flex-1"></div>
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					{#each regular as snippet (snippet.id)}
						<div animate:flip={{duration: 400}} transition:fade>
							{@render SnippetCard({ snippet })}
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if sortedSnippets.length === 0}
			<div class="flex flex-col items-center justify-center py-20 opacity-30 gap-6">
				<div class="text-8xl">🏢</div>
				<div class="text-center">
					<p class="text-sm font-black uppercase tracking-[0.4em] mb-2 text-indigo-500">Empty Registry</p>
					<p class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Save complex queries as snippets to automate your workflow</p>
				</div>
			</div>
		{/if}
	</div>
</div>

{#snippet SnippetCard({ snippet }: { snippet: Snippet })}
	<div class="group bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-[2.5rem] p-6 hover:border-indigo-500/50 transition-all hover:shadow-2xl relative flex flex-col h-full min-h-[220px] overflow-hidden">
		<div class="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-indigo-500 to-transparent opacity-30 group-hover:opacity-100 transition-opacity"></div>
		
		<div class="flex items-start justify-between gap-4 mb-6">
			<div class="flex-1 min-w-0">
				<div class="flex items-center gap-2 mb-2">
					<h4 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-tighter truncate italic leading-none">{snippet.name}</h4>
					<button 
						onclick={() => toggleFav(snippet.id)}
						class="text-xs transition-transform active:scale-150 {snippet.is_favorite ? 'text-amber-500 animate-in zoom-in' : 'text-slate-300 hover:text-amber-400 opacity-0 group-hover:opacity-100'}"
					>
						{snippet.is_favorite ? '★' : '☆'}
					</button>
				</div>
				<div class="flex flex-wrap gap-1.5">
					{#each snippet.tags as tag}
						<span class="px-2.5 py-0.5 rounded-lg bg-indigo-500/5 dark:bg-indigo-500/10 text-indigo-500 text-[8px] font-black uppercase tracking-widest border border-indigo-500/10">
							#{tag}
						</span>
					{/each}
				</div>
			</div>
			<button 
				onclick={() => useSnippet(snippet)}
				class="w-12 h-12 rounded-2xl bg-indigo-600 hover:bg-emerald-500 text-white flex items-center justify-center shadow-xl shadow-indigo-500/20 transition-all active:scale-90 flex-shrink-0 group-hover:rotate-12"
				title="Inject Snippet into Explorer"
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
			</button>
		</div>
		
		<div class="flex-1 bg-slate-950 rounded-2xl p-4 border border-slate-800/50 mb-6 overflow-hidden relative group/code shadow-inner">
			<div class="absolute top-2 right-3">
				<span class="text-[8px] font-black text-slate-700 uppercase tracking-widest leading-none italic pointer-events-none">Deterministic Logic</span>
			</div>
			<pre class="text-[10px] font-mono text-slate-400 line-clamp-4 leading-relaxed whitespace-pre-wrap">{snippet.query}</pre>
		</div>

		<div class="mt-auto flex items-center justify-between border-t border-slate-50 dark:border-slate-800 pt-4">
			<div class="flex items-center gap-4">
				<div class="flex flex-col">
					<span class="text-[8px] font-black text-slate-400 uppercase tracking-tighter">Last Engagement</span>
					<span class="text-[9px] font-bold text-slate-600 dark:text-slate-400 uppercase tracking-widest italic">{new Date(snippet.last_used).toLocaleDateString()}</span>
				</div>
			</div>
			<button 
				onclick={() => workspaceStore.deleteSnippet(snippet.id)}
				class="text-[9px] font-black text-rose-500 uppercase tracking-widest opacity-0 group-hover:opacity-100 hover:text-rose-400 transition-all flex items-center gap-2"
			>
				<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
				Purge Logic
			</button>
		</div>
	</div>
{/snippet}
