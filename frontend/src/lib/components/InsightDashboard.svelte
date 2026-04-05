<script lang="ts">
	import { workspaceStore } from '$lib/stores/workspaceStore';
	import { onMount } from 'svelte';
	import { fade, slide } from 'svelte/transition';

	onMount(() => {
		workspaceStore.fetchInsights();
	});

	function formatDuration(ms: number) {
		if (ms < 1) return '< 1ms';
		return `${ms.toFixed(1)}ms`;
	}
</script>

<div class="h-full overflow-y-auto p-8 space-y-12 custom-scrollbar animate-in fade-in slide-in-from-bottom-4 duration-700">
	<header class="space-y-2">
		<h2 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">Architectural <span class="text-indigo-500">Intelligence</span></h2>
		<p class="text-xs font-bold text-slate-500 uppercase tracking-widest leading-none">Aggregated performance patterns and structural volatility insights</p>
	</header>

	{#if $workspaceStore.insights}
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<!-- Performance Hotspots -->
			<section class="space-y-6">
				<div class="flex items-center gap-3">
					<span class="text-xl">🔥</span>
					<h3 class="text-xs font-black text-slate-400 uppercase tracking-[0.3em] font-sans">Performance Hotspots</h3>
					<div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
				</div>

				<div class="space-y-4">
					{#each $workspaceStore.insights.slowest_queries as entry}
						<div class="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-[2rem] hover:shadow-2xl hover:border-rose-500/30 transition-all group overflow-hidden relative">
							<div class="absolute top-0 right-0 p-3">
								<span class="px-2 py-1 rounded-lg bg-rose-500/10 text-rose-500 text-[9px] font-black uppercase tracking-tighter">Slowest Peak</span>
							</div>
							<div class="flex items-start justify-between mb-3 pr-20">
								<code class="text-[11px] font-mono font-medium text-slate-600 dark:text-slate-400 line-clamp-2">{entry.query}</code>
							</div>
							<div class="flex items-center gap-4 border-t border-slate-100 dark:border-slate-800 pt-3">
								<div class="flex flex-col">
									<span class="text-[9px] font-black text-slate-400 uppercase tracking-tighter">Avg Latency</span>
									<span class="text-xs font-black text-rose-500">{formatDuration(entry.duration_ms)}</span>
								</div>
								<div class="flex flex-col border-l border-slate-100 dark:border-slate-800 pl-4">
									<span class="text-[9px] font-black text-slate-400 uppercase tracking-tighter">Table Context</span>
									<span class="text-xs font-black text-slate-700 dark:text-slate-300 uppercase tracking-tighter">{entry.table_name || 'Global'}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</section>

			<!-- Impact & Frequency -->
			<div class="space-y-12">
				<!-- High Volatility Tables -->
				<section class="space-y-6">
					<div class="flex items-center gap-3">
						<span class="text-xl">📊</span>
						<h3 class="text-xs font-black text-slate-400 uppercase tracking-[0.3em] font-sans">Structural Volatility</h3>
						<div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
					</div>

					<div class="grid grid-cols-1 gap-4">
						{#each $workspaceStore.insights.impacted_tables as table}
							<div class="flex items-center justify-between p-5 bg-indigo-500/5 border border-indigo-500/10 rounded-2xl group hover:bg-indigo-500/10 transition-all">
								<div class="flex flex-col">
									<span class="text-sm font-black text-slate-800 dark:text-white uppercase tracking-tighter italic">{table.table}</span>
									<span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{table.activity} mutations in last 100 runs</span>
								</div>
								<div class="text-right">
									<span class="block text-xs font-black text-indigo-500">{table.rows.toLocaleString()}</span>
									<span class="text-[9px] font-black text-slate-400 uppercase tracking-tighter">Rows Affected</span>
								</div>
							</div>
						{/each}
					</div>
				</section>

				<!-- Execution Frequency -->
				<section class="space-y-6">
					<div class="flex items-center gap-3">
						<span class="text-xl">🔄</span>
						<h3 class="text-xs font-black text-slate-400 uppercase tracking-[0.3em] font-sans">Execution Frequency</h3>
						<div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
					</div>

					<div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-[2.5rem] overflow-hidden shadow-xl">
						<div class="divide-y divide-slate-100 dark:divide-slate-800">
							{#each $workspaceStore.insights.frequent_queries as freq}
								<div class="p-5 flex items-center justify-between group hover:bg-slate-50 dark:hover:bg-slate-950 transition-colors">
									<div class="flex-1 mr-6">
										<code class="text-[10px] font-mono text-slate-500 truncate block border-l-2 border-indigo-500/20 pl-3 leading-relaxed">{freq.query}</code>
									</div>
									<div class="px-4 py-2 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-600/20">
										<span class="text-[11px] font-black text-white uppercase tracking-widest">{freq.count}x</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</section>
			</div>
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center h-96 opacity-30 gap-6">
			<div class="text-[100px] filter saturate-0 group-hover:saturate-100 transition-all">📈</div>
			<div class="text-center">
				<p class="text-sm font-black uppercase tracking-[0.5em] text-indigo-500">Processing Activity</p>
				<p class="text-[10px] font-bold uppercase tracking-widest leading-relaxed mt-2">Execute more queries to initialize the architectural insight engine</p>
			</div>
		</div>
	{/if}
</div>
