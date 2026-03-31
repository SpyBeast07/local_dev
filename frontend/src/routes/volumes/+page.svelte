<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";

	interface DockerVolume {
		Name: string;
		Driver: string;
		Mountpoint: string;
		Scope: string;
	}

	let volumes = $state<DockerVolume[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/volumes");
			volumes = Array.isArray(res.data) ? res.data : [];
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Volumes<span class="text-orange-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-2">Persistent Virtual Storage Drives</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-orange-600 dark:text-orange-400 font-black animate-pulse uppercase tracking-wider text-sm ml-2">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Loading Data Dumps...
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
			{#each volumes as vol}
				<div class="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col gap-4 relative overflow-hidden group hover:border-orange-500/50 transition-colors">
					<div class="flex flex-col">
						<h3 class="font-black text-slate-900 dark:text-slate-100 uppercase tracking-tight italic break-all" title={vol.Name}>{vol.Name.length > 25 ? vol.Name.slice(0, 25) + '...' : vol.Name}</h3>
						<span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mt-1">Driver: <span class="text-orange-500">{vol.Driver || 'local'}</span></span>
					</div>

					<div class="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4 mt-auto">
						<div class="flex flex-col w-full">
							<span class="text-[8px] font-black tracking-widest uppercase text-slate-400">Mountpoint</span>
							<span class="text-[9px] font-bold font-mono tracking-widest text-slate-500 mt-0.5 break-all bg-slate-50 dark:bg-slate-950 p-2 rounded-lg border border-slate-100 dark:border-slate-800 italic">{vol.Mountpoint}</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
