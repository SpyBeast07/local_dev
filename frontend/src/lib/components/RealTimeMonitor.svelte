<script lang="ts">
	import { workspaceStore } from '$lib/stores/workspaceStore';
	import { onMount, onDestroy } from 'svelte';
	import { fade, slide, scale } from 'svelte/transition';

	let interval: any;

	onMount(() => {
		workspaceStore.fetchActiveQueries();
		interval = setInterval(() => {
			workspaceStore.fetchActiveQueries();
		}, 3000); // 3s refresh for real-time feel
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});

	function getDurationColor(seconds: number) {
		if (seconds > 10) return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
		if (seconds > 3) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
		return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
	}
</script>

<div class="h-full flex flex-col overflow-hidden animate-in fade-in slide-in-from-right-4 duration-500">
	<div class="p-6 border-b border-white/5 bg-white/40 dark:bg-slate-900/40 flex items-center justify-between">
		<div class="flex items-center gap-4">
			<div class="relative">
				<div class="w-3 h-3 rounded-full bg-emerald-500 animate-ping absolute inset-0 opacity-50"></div>
				<div class="w-3 h-3 rounded-full bg-emerald-500 relative"></div>
			</div>
			<div>
				<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest">Active Awareness</h3>
				<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1 italic leading-none">Live database activity monitoring (3s interval)</p>
			</div>
		</div>
		<div class="flex items-center gap-2">
			<span class="px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-[10px] font-black uppercase tracking-widest text-slate-500">
				{$workspaceStore.activeQueries.length} Sessions Active
			</span>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
		{#each $workspaceStore.activeQueries as query (query.pid)}
			<div 
				in:slide={{ duration: 300 }}
				class="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-[2.5rem] shadow-xl hover:shadow-2xl transition-all relative overflow-hidden group"
			>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-[9px] font-black text-slate-500 uppercase tracking-widest">PID: {query.pid}</span>
						<span class="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-500 text-[9px] font-black uppercase tracking-widest italic">{query.state}</span>
					</div>
					<div class="flex items-center gap-2 px-3 py-1.5 rounded-xl border {getDurationColor(query.duration_s)} transition-colors">
						<span class="text-[10px] font-black uppercase tracking-tighter">Live Time: {query.duration_s}s</span>
					</div>
				</div>

				<div class="bg-slate-50 dark:bg-slate-950 p-4 rounded-2xl border border-slate-100 dark:border-slate-800 mb-4 group-hover:border-indigo-500/20 transition-colors">
					<code class="text-[11px] font-mono font-medium text-slate-600 dark:text-slate-400 leading-relaxed block break-words whitespace-pre-wrap">{query.query}</code>
				</div>

				<div class="flex items-center gap-4">
					<div class="flex items-center gap-2">
						<span class="text-[9px] font-black text-slate-400 uppercase tracking-widest italic leading-none">Wait Event:</span>
						<span class="text-[10px] font-bold text-slate-500 uppercase tracking-tighter truncate max-w-[200px]">{query.wait_event}</span>
					</div>
				</div>
			</div>
		{:else}
			<div class="h-full flex flex-col items-center justify-center opacity-20 py-20 text-center space-y-6">
				<div class="text-[140px] filter saturate-0 origin-center hover:scale-110 transition-transform">🛰️</div>
				<p class="text-sm font-black uppercase tracking-[0.5em] text-emerald-500">System Quiescent</p>
				<p class="text-[10px] font-bold uppercase tracking-widest italic">No active transactions detected beyond background maintenance</p>
			</div>
		{/each}
	</div>
</div>
