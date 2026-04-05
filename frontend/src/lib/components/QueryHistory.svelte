<script lang="ts">
	import { workspaceStore, type HistoryEntry } from '$lib/stores/workspaceStore';
	import { goto } from '$app/navigation';
	import { flip } from 'svelte/animate';
	import { fade } from 'svelte/transition';

	let activeFilter = $state<'all' | 'slow' | 'failed'>('all');
	let searchQuery = $state('');

	// Compute filtered history
	let filteredHistory = $derived($workspaceStore.history.filter(h => {
		if (activeFilter === 'slow') return h.performance_tier === 'SLOW';
		if (activeFilter === 'failed') return !h.success;
		if (searchQuery) return h.query.toLowerCase().includes(searchQuery.toLowerCase());
		return true;
	}));

	// Compute grouped history (grouped by table name)
	let groupedHistory = $derived(filteredHistory.reduce((acc, entry) => {
		const key = entry.table_name || 'Global / Uncategorized';
		if (!acc[key]) acc[key] = [];
		acc[key].push(entry);
		return acc;
	}, {} as Record<string, HistoryEntry[]>));

	// Compute frequency
	let queryFrequency = $derived($workspaceStore.history.reduce((acc, entry) => {
		acc[entry.query] = (acc[entry.query] || 0) + 1;
		return acc;
	}, {} as Record<string, number>));

	function replayQuery(query: string) {
		const params = new URLSearchParams();
		params.set('sql', query);
		goto(`/database?${params.toString()}`);
	}

	function traceQuery(query: string) {
		const params = new URLSearchParams();
		params.set('sql', query);
		params.set('trace', 'true');
		goto(`/database?${params.toString()}`);
	}

	function getStatusColor(performance: string | undefined, success: boolean) {
		if (!success) return 'text-rose-500 bg-rose-500/10';
		if (performance === 'SLOW') return 'text-rose-500 bg-rose-500/10';
		if (performance === 'MEDIUM') return 'text-amber-500 bg-amber-500/10';
		return 'text-emerald-500 bg-emerald-500/10';
	}

	function getPerformanceIcon(performance: string | undefined, success: boolean) {
		if (!success) return '🔴';
		if (performance === 'SLOW') return '🔴';
		if (performance === 'MEDIUM') return '🟡';
		return '🟢';
	}
</script>

<div class="flex flex-col h-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
	<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 flex flex-col gap-6">
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest">Execution Registry</h3>
				<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1 italic tracking-widest leading-none">Intelligent Audit Engine</p>
			</div>
			<div class="flex items-center gap-2">
				<span class="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest border border-indigo-500/20 shadow-sm">
					{filteredHistory.length} Total
				</span>
			</div>
		</div>

		<div class="flex items-center gap-4">
			<div class="flex bg-slate-100 dark:bg-slate-950 p-1 rounded-xl border border-slate-200 dark:border-slate-800 shadow-inner">
				{#each ['all', 'slow', 'failed'] as f}
					<button 
						onclick={() => activeFilter = f as any}
						class="px-4 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all {activeFilter === f ? 'bg-white dark:bg-slate-800 text-indigo-500 shadow-sm' : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-300'}"
					>
						{f}
					</button>
				{/each}
			</div>
			<div class="flex-1 relative">
				<input 
					type="text" 
					placeholder="Search queries..." 
					bind:value={searchQuery}
					class="w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2 text-[10px] font-bold focus:ring-4 focus:ring-indigo-500/10 transition-all outline-none"
				/>
			</div>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-10">
		{#each Object.entries(groupedHistory) as [tableName, entries] (tableName)}
			<div class="space-y-4" transition:fade>
				<div class="flex items-center gap-3">
					<span class="text-[9px] font-black text-slate-400 uppercase tracking-[0.3em] italic">{tableName}</span>
					<div class="h-px bg-slate-100 dark:bg-slate-800 flex-1"></div>
					<span class="text-[9px] font-bold text-slate-500">{entries.length} queries</span>
				</div>

				<div class="grid grid-cols-1 gap-4">
					{#each entries as entry (entry.id)}
						<div 
							class="group flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden hover:border-indigo-500/40 transition-all shadow-sm hover:shadow-xl relative"
						>
							{#if queryFrequency[entry.query] > 1}
								<div class="absolute -right-1 -top-1 px-2 py-1 bg-violet-500 text-white rounded-bl-xl text-[8px] font-black uppercase tracking-widest z-10 shadow-lg shadow-violet-500/20">
									Frequent ({queryFrequency[entry.query]})
								</div>
							{/if}

							<div class="flex items-center justify-between p-4 bg-slate-50/50 dark:bg-slate-950/20 border-b border-slate-200 dark:border-slate-800">
								<div class="flex items-center gap-3">
									<span class="text-sm" title={entry.performance_tier}>{getPerformanceIcon(entry.performance_tier, entry.success)}</span>
									<span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono italic">{entry.timestamp}</span>
								</div>
								<div class="flex items-center gap-4">
									<div class="flex flex-col items-end">
										<span class="text-[9px] font-black text-slate-400 uppercase tracking-tighter mb-0.5">Complexity</span>
										<span class="text-[10px] font-black text-indigo-500 italic">{entry.explain_summary || 'N/A'}</span>
									</div>
									<div class="flex flex-col items-end">
										<span class="text-[9px] font-black text-slate-400 uppercase tracking-tighter mb-0.5">Latency</span>
										<span class="text-[10px] font-black text-indigo-500">{entry.duration_ms}ms</span>
									</div>
									<button 
										onclick={() => traceQuery(entry.query)}
										class="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-[9px] font-black uppercase tracking-widest transition-all shadow-lg shadow-amber-500/20 active:scale-95 flex items-center gap-2"
										title="Trace Impact Analysis"
									>
										<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
										Impact Trace
									</button>
									<button 
										onclick={() => replayQuery(entry.query)}
										class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-emerald-500 text-white text-[9px] font-black uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20 active:scale-95 flex items-center gap-2"
									>
										<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
										Replay
									</button>
								</div>
							</div>
							<div class="p-4 relative bg-slate-950">
								<pre class="text-[11px] font-mono font-medium text-slate-300 whitespace-pre-wrap overflow-x-auto selection:bg-indigo-500/30 selection:text-white leading-relaxed">{entry.query}</pre>
								
								{#if entry.optimization_hints && entry.optimization_hints.length > 0}
									<div class="mt-4 p-4 bg-amber-500/5 border border-amber-500/10 rounded-2xl animate-in slide-in-from-top-2 duration-300">
										<div class="flex items-center gap-2 mb-3">
											<span class="text-xs">💡</span>
											<span class="text-[9px] font-black text-amber-500 uppercase tracking-[0.2em] italic">Optimization Hints</span>
										</div>
										<ul class="space-y-2">
											{#each entry.optimization_hints as hint}
												<li class="text-[10px] font-bold text-amber-600/90 dark:text-amber-400/80 leading-relaxed border-l-2 border-amber-500/20 pl-3">
													{hint}
												</li>
											{/each}
										</ul>
									</div>
								{/if}

								{#if !entry.success && entry.error}
									<div class="mt-3 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl">
										<p class="text-[9px] font-black text-rose-500 uppercase tracking-widest mb-1">Runtime Exception</p>
										<p class="text-[10px] font-bold text-rose-400/80 font-mono italic leading-relaxed">{entry.error}</p>
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<div class="flex flex-col items-center justify-center h-full text-slate-500 gap-6 opacity-40 py-20 animate-in fade-in zoom-in-95 duration-700">
				<div class="text-8xl filter saturate-0 group-hover:saturate-100 transition-all">🔍</div>
				<div class="text-center">
					<p class="text-sm font-black uppercase tracking-[0.4em] mb-2 text-indigo-500">Registry Empty</p>
					<p class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Execute queries in the explorer to populate history</p>
				</div>
				<button 
					onclick={() => goto('/database')}
					class="px-6 py-2 rounded-full border border-slate-200 dark:border-slate-800 text-[10px] font-black uppercase tracking-widest hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
				>
					Open SQL Explorer
				</button>
			</div>
		{/each}
	</div>
</div>
