<script lang="ts">
	import { workspaceStore } from '$lib/stores/workspaceStore';
	import { goto } from '$app/navigation';

	function replayQuery(query: string) {
		// Use URL search params to pass query to the database page
		const params = new URLSearchParams();
		params.set('sql', query);
		goto(`/database?${params.toString()}`);
	}

	function getStatusColor(success: boolean) {
		return success ? 'text-emerald-500 bg-emerald-500/10' : 'text-rose-500 bg-rose-500/10';
	}
</script>

<div class="flex flex-col h-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
	<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 flex items-center justify-between">
		<div>
			<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest">Execution Registry</h3>
			<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Audit log of your last 100 queries</p>
		</div>
		<div class="flex items-center gap-2">
			<span class="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest border border-indigo-500/20">
				{$workspaceStore.history.length} Entries
			</span>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-4">
		{#each $workspaceStore.history as entry (entry.id)}
			<div class="group flex flex-col bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden hover:border-indigo-500/40 transition-all shadow-sm hover:shadow-xl">
				<div class="flex items-center justify-between p-4 bg-slate-50/50 dark:bg-slate-950/20 border-b border-slate-200 dark:border-slate-800">
					<div class="flex items-center gap-3">
						<span class="px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest {getStatusColor(entry.success)}">
							{entry.success ? 'Success' : 'Failed'}
						</span>
						<span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{entry.timestamp}</span>
					</div>
					<div class="flex items-center gap-4">
						<div class="flex flex-col items-end">
							<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Time</span>
							<span class="text-[11px] font-black text-indigo-500">{entry.duration_ms}ms</span>
						</div>
						<div class="w-px h-6 bg-slate-200 dark:bg-slate-800"></div>
						<button 
							onclick={() => replayQuery(entry.query)}
							class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
						>
							Replay
						</button>
					</div>
				</div>
				<div class="p-4 relative bg-slate-950">
					<pre class="text-[11px] font-mono font-medium text-slate-300 whitespace-pre-wrap overflow-x-auto selection:bg-indigo-500/30 selection:text-white">{entry.query}</pre>
					{#if !entry.success && entry.error}
						<div class="mt-3 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl">
							<p class="text-[10px] font-black text-rose-500 uppercase tracking-widest mb-1">Runtime Exception</p>
							<p class="text-[10px] font-bold text-rose-400 font-mono italic leading-relaxed">{entry.error}</p>
						</div>
					{/if}
				</div>
			</div>
		{:else}
			<div class="flex flex-col items-center justify-center h-full text-slate-500 gap-4 opacity-50 py-20">
				<div class="text-6xl">🕳️</div>
				<p class="text-xs font-black uppercase tracking-[0.3em]">Registry Empty</p>
				<p class="text-[10px] font-bold uppercase tracking-widest">Execute queries in the explorer to populate history</p>
			</div>
		{/each}
	</div>
</div>
