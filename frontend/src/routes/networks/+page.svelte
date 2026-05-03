<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";

	interface DockerNetwork {
		ID: string;
		Name: string;
		Driver: string;
		Scope: string;
	}

	let networks = $state<DockerNetwork[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/networks");
			networks = Array.isArray(res.data) ? res.data : [];
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-10 ">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Networks<span class="text-cyan-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-2">Docker Daemon Bridge Topologies</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-cyan-600 dark:text-cyan-400 font-black animate-pulse uppercase tracking-wider text-sm ml-2">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Sniffing Interfaces...
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
			{#each networks as net}
				<div class="bg-white dark:bg-slate-900 rounded-[2rem] p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col gap-4 relative overflow-hidden group hover:border-cyan-500/50 transition-colors">
					<div class="flex flex-col">
						<h3 class="font-black text-slate-900 dark:text-slate-100 uppercase tracking-tight italic" title={net.Name}>{net.Name}</h3>
						<span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mt-1">Driver: <span class="text-cyan-500">{net.Driver || 'bridge'}</span></span>
					</div>

					<div class="flex flex-col border-t border-slate-100 dark:border-slate-800 pt-4 mt-auto">
						<div class="flex justify-between items-center w-full">
							<span class="text-[9px] font-black tracking-widest uppercase text-slate-400">ID: {net.ID.slice(0, 12)}</span>
							<span class="text-[9px] font-bold tracking-widest text-slate-500 px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded uppercase">{net.Scope}</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
