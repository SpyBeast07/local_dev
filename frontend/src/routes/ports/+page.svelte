<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";

	interface Port {
		process: string;
		pid: string;
		protocol: string;
		port: string;
		is_important: boolean;
	}

	let ports = $state<Port[]>([]);
	let importantPorts = $state<Port[]>([]);
	let otherPorts = $state<Port[]>([]);
	
	let loading = $state(true);
	let showOther = $state(false);

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/ports");
			ports = Array.isArray(res.data) ? res.data : [];
			importantPorts = ports.filter(p => p.is_important);
			otherPorts = ports.filter(p => !p.is_important);
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});
</script>

{#snippet portCard(p: Port)}
	<a 
		href={`http://localhost:${p.port}`}
		target="_blank"
		class="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border shadow-sm transition-all duration-500 group flex flex-col gap-6 relative overflow-hidden
			{p.is_important 
				? 'border-slate-200/60 dark:border-slate-800 hover:border-amber-300 dark:hover:border-amber-800 hover:bg-amber-50/10 dark:hover:bg-amber-900/10' 
				: 'border-slate-100 dark:border-slate-800/50 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/30'}"
	>
		<div class="absolute -right-4 -top-4 w-24 h-24 rounded-full blur-2xl transition-colors duration-500
			{p.is_important ? 'bg-amber-500/5 group-hover:bg-amber-500/10' : 'bg-slate-500/5 group-hover:bg-slate-500/10'}"></div>
		
		<div class="flex items-start justify-between">
			<div class="flex flex-col">
				<span class="text-3xl font-black tracking-tighter italic leading-none uppercase transition-colors duration-300
					{p.is_important ? 'text-slate-900 dark:text-white group-hover:text-amber-600 dark:group-hover:text-amber-400' : 'text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white'}">
					{p.port}
				</span>
				<span class="text-[10px] uppercase font-black text-slate-400 dark:text-slate-500 tracking-[0.2em] mt-2 italic leading-none">{p.protocol}</span>
			</div>
			<div class="w-10 h-10 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800 flex items-center justify-center text-slate-300 dark:text-slate-700 transition-all duration-300
				{p.is_important ? 'group-hover:bg-amber-500 group-hover:text-white group-hover:shadow-lg group-hover:shadow-amber-500/20' : 'group-hover:bg-slate-700 group-hover:text-white'}">
				<svg class="w-5 h-5 group-hover:scale-125 transition-transform duration-300 {p.is_important ? 'group-hover:rotate-12' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
			</div>
		</div>

		<div class="flex flex-col gap-3">
			<div class="flex items-center justify-between bg-slate-50 dark:bg-slate-950 px-4 py-2 rounded-xl border border-slate-100/50 dark:border-slate-800">
				<span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none">Process</span>
				<span class="text-[9px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest leading-none">PID {p.pid}</span>
			</div>
			<p class="text-lg font-black uppercase tracking-tight italic break-all leading-tight transition-colors duration-300
				{p.is_important ? 'text-slate-800 dark:text-slate-200 group-hover:text-amber-600 dark:group-hover:text-amber-400' : 'text-slate-600 dark:text-slate-400 group-hover:text-slate-800 dark:group-hover:text-slate-200'}">
				{p.process}
			</p>
		</div>

		<div class="mt-auto pt-4 border-t {p.is_important ? 'border-slate-50 dark:border-slate-800' : 'border-slate-100 dark:border-slate-800/50'}">
			<span class="text-[9px] font-black text-slate-300 dark:text-slate-600 uppercase tracking-[0.3em] italic leading-none">Open Gateway</span>
		</div>
	</a>
{/snippet}

<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<a href="/" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-amber-600 dark:hover:text-amber-400 hover:border-amber-200 dark:hover:border-amber-800 transition-all shadow-sm" aria-label="Back to dashboard">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Network Gates<span class="text-amber-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-14">Developer signal extractor monitoring active development gateways</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-amber-600 dark:text-amber-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Scanning Gateways...
		</div>
	{:else if ports.length === 0}
		<div class="py-20 flex flex-col items-center gap-6 text-slate-300 dark:text-slate-700">
			<div class="text-8xl opacity-10 italic font-black uppercase tracking-tighter leading-none">Quiet</div>
			<p class="text-sm font-bold uppercase tracking-[0.3em]">No active gateways detected</p>
		</div>
	{:else}
		<!-- 🔥 Important Ports -->
		<div class="flex flex-col gap-6">
			<h2 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight italic flex items-center gap-3 ml-2">
				<span class="text-amber-500">🔥</span> Important Ports
			</h2>
			{#if importantPorts.length > 0}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
					{#each importantPorts as p}
						{@render portCard(p)}
					{/each}
				</div>
			{:else}
				<div class="py-8 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-3xl text-sm font-bold text-slate-400 uppercase tracking-widest">
					No priority environments found
				</div>
			{/if}
		</div>

		<!-- ⚠️ Other Ports -->
		{#if otherPorts.length > 0}
			<div class="mt-8 pt-8 border-t border-slate-200 dark:border-slate-800">
				<button 
					onclick={() => showOther = !showOther}
					class="flex items-center gap-3 group text-left px-2"
				>
					<h2 class="text-xl font-black text-slate-500 dark:text-slate-400 uppercase tracking-tight italic group-hover:text-slate-900 dark:group-hover:text-white transition-colors duration-300">
						<span class="text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">⚠️</span> Other Ports 
						<span class="text-sm border ml-2 border-slate-200 dark:border-slate-800 px-2 py-0.5 rounded-lg group-hover:border-slate-900 dark:group-hover:border-slate-600 text-slate-400">{otherPorts.length}</span>
					</h2>
					<svg class="w-5 h-5 text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-all transform {showOther ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7" /></svg>
				</button>
				
				{#if showOther}
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-8">
						{#each otherPorts as p}
							{@render portCard(p)}
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	{/if}
</div>
