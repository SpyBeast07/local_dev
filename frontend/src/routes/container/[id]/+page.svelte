<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import axios from "axios";
	import { page } from "$app/state";

	let containerId = $derived(page.params.id ?? "");
	let logs = $state<string[]>([]);
	let loading = $state(true);
	let lastRefresh = $state<string>("");

	async function fetchLogs() {
		if (!containerId) return;
		try {
			const res = await axios.get(
				`http://127.0.0.1:8000/containers/${containerId}/logs`
			);
			logs = res.data.logs;
			lastRefresh = new Date().toLocaleTimeString();
		} catch (err) {
			console.error("Failed to fetch logs:", err);
		} finally {
			loading = false;
		}
	}

	let stats = $state<any>(null);
	async function fetchStats() {
		if (!containerId) return;
		try {
			const res = await axios.get(`http://127.0.0.1:8000/containers/${containerId}/stats`);
			stats = res.data;
		} catch (err) {
			console.error("Failed to fetch stats:", err);
		}
	}

	let intervalId: any;

	onMount(() => {
		fetchLogs();
		fetchStats();
		intervalId = setInterval(() => {
			fetchLogs();
			fetchStats();
		}, 3000);
	});

	onDestroy(() => {
		if (intervalId) clearInterval(intervalId);
	});
</script>

<div class="flex flex-col gap-8 flex-1">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<a href="/containers" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-200 dark:hover:border-blue-800 transition-all shadow-sm" aria-label="Back to containers">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Live Logs<span class="text-blue-600 uppercase italic">.</span></h1>
		</div>
		<div class="flex items-center gap-6 ml-14">
			<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-[10px]">Container ID: <span class="text-slate-900 dark:text-slate-200 italic font-mono">{containerId.slice(0,12)}</span></p>
			
			{#if stats && !stats.error}
				<div class="flex items-center gap-6 border-l border-slate-200 dark:border-slate-800 pl-6">
					<div class="flex flex-col gap-0.5">
						<span class="text-[8px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest leading-none">CPU</span>
						<span class="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400 italic py-0.5">{stats.CPUPerc}</span>
					</div>
					<div class="flex flex-col gap-0.5">
						<span class="text-[8px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest leading-none">Memory</span>
						<span class="text-xs font-mono font-bold text-blue-600 dark:text-blue-400 italic py-0.5">{stats.MemUsage} <span class="text-[10px] text-blue-400/50">({stats.MemPerc})</span></span>
					</div>
					<div class="flex flex-col gap-0.5">
						<span class="text-[8px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest leading-none">Net IO</span>
						<span class="text-xs font-mono font-bold text-amber-600 dark:text-amber-400 italic py-0.5">{stats.NetIO}</span>
					</div>
				</div>
			{/if}

			{#if lastRefresh}
				<div class="flex items-center gap-2 ml-auto">
					<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
					<span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none">Live Sync: {lastRefresh}</span>
				</div>
			{/if}
		</div>
	</header>

	{#if loading}
		<div class="flex-1 flex items-center justify-center gap-4 text-blue-600 dark:text-blue-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Attaching to Stream...
		</div>
	{:else}
		<div class="flex-1 bg-slate-950 rounded-[2.5rem] p-8 shadow-2xl shadow-blue-900/20 border border-slate-800 overflow-hidden flex flex-col mx-2">
			<div class="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
				<div class="flex gap-2">
					<div class="w-3 h-3 rounded-full bg-rose-500/50"></div>
					<div class="w-3 h-3 rounded-full bg-amber-500/50"></div>
					<div class="w-3 h-3 rounded-full bg-emerald-500/50"></div>
				</div>
				<span class="text-[10px] font-mono font-black text-slate-500 uppercase tracking-[0.3em] leading-none">Container Terminal V1.0</span>
			</div>
			
			<div class="flex-1 overflow-y-auto font-mono text-sm space-y-1 custom-scrollbar pr-4">
				{#each logs as line, i}
					{#if line.trim()}
						<div class="flex gap-4 group">
							<span class="text-slate-700 select-none text-[10px] mt-0.5 min-w-[3ch] text-right font-mono">{i + 1}</span>
							<p class="text-slate-300 group-hover:text-emerald-400 transition-colors break-all whitespace-pre-wrap leading-relaxed">{line}</p>
						</div>
					{/if}
				{:else}
					<div class="h-full flex flex-col items-center justify-center gap-4 opacity-20 italic">
						<span class="text-4xl font-black uppercase tracking-tighter text-white leading-none">No Output</span>
						<p class="text-xs font-bold text-white uppercase tracking-widest leading-none">Awaiting system events...</p>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #1e293b;
		border-radius: 10px;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: #334155;
	}
</style>
