<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";
	import { workspaceStore } from "$lib/stores/workspaceStore";

	interface Container {
		id: string;
		name: string;
		image: string;
		status: string;
		ports: string;
	}

	interface Port {
		process: string;
		pid: string;
		protocol: string;
		port: string;
		is_important: boolean;
	}

	let containers = $state<Container[]>([]);
	let ports = $state<Port[]>([]);
	let importantPorts = $state<Port[]>([]);
	let tables = $state<string[]>([]);
	let sources = $state<any[]>([]);

	let loading = $state(true);

	onMount(async () => {
		try {
			const [cRes, pRes, tRes, sRes] = await Promise.all([
				axios.get("http://127.0.0.1:8000/containers"),
				axios.get("http://127.0.0.1:8000/ports"),
				axios.get("http://127.0.0.1:8000/db/tables"),
				axios.get("http://127.0.0.1:8000/sources")
			]);

			containers = Array.isArray(cRes.data) ? cRes.data : [];
			ports = Array.isArray(pRes.data) ? pRes.data : [];
			importantPorts = ports.filter(p => p.is_important);
			tables = Array.isArray(tRes.data) ? tRes.data : [];
			sources = Array.isArray(sRes.data) ? sRes.data : [];
			
			// Initialize workspace store (history, snippets, etc.)
			await workspaceStore.fetchAll();
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Dashboard<span class="text-indigo-600 uppercase italic">.</span></h1>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs">Environment Summaries & Shortcuts</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-indigo-600 dark:text-indigo-400 font-black animate-pulse uppercase tracking-wider text-sm">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Synchronizing Environment...
		</div>
	{:else}
		<!-- Main Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
			
			<!-- 🐳 Containers Summary -->
			<section class="bg-white dark:bg-slate-900 rounded-[2rem] p-10 border border-slate-200/60 dark:border-slate-800 shadow-sm flex flex-col gap-8 group/section transition-all duration-500">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-4">
						<div class="w-12 h-12 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-2xl flex items-center justify-center text-2xl shadow-inner border border-blue-100 dark:border-blue-900/30 group-hover/section:scale-110 group-hover/section:rotate-3 transition-all duration-300">🐳</div>
						<div class="flex flex-col">
							<h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase leading-none group-hover/section:text-blue-600 dark:group-hover/section:text-blue-400 transition-colors">Containers</h2>
							<span class="text-[10px] font-bold text-blue-600/60 dark:text-blue-400/60 uppercase tracking-widest mt-1">{containers.length} Total Nodes</span>
						</div>
					</div>
					<a href="/containers" class="text-[10px] font-black bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 px-4 py-2 rounded-xl border border-blue-100 dark:border-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-all uppercase tracking-widest hover:scale-105">VIEW ALL</a>
				</div>

				<div class="flex flex-col gap-5 text-left">
					{#each containers.slice(0, 3) as c}
						<a href={`/container/${c.id}`} class="p-5 bg-slate-50/40 dark:bg-slate-950/40 rounded-3xl border border-slate-100 dark:border-slate-800/60 flex items-center justify-between group hover:border-blue-300 dark:hover:border-blue-800 hover:bg-white dark:hover:bg-slate-800 transition-all duration-300">
							<div>
								<h3 class="font-black text-slate-800 dark:text-slate-200 uppercase tracking-tight italic group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors uppercase italic">{c.name}</h3>
								<p class="text-[9px] font-bold font-mono text-slate-400 dark:text-slate-500 uppercase tracking-tighter">{c.image.split(':')[0]}</p>
							</div>
							<div 
								class="px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-wider shadow-sm
								{c.status.includes('Up') 
									? 'bg-emerald-500 text-white shadow-emerald-500/20' 
									: 'bg-rose-500 text-white shadow-rose-500/20'}"
							>
								{c.status.includes('Up') ? 'Ready' : 'Stopped'}
							</div>
						</a>
					{:else}
						<div class="py-8 flex flex-col items-center gap-4 text-slate-300 dark:text-slate-700">
							<div class="text-3xl opacity-20 italic font-black uppercase leading-none">Offline</div>
						</div>
					{/each}
				</div>
			</section>

			<!-- 🌐 Network Summary -->
			<section class="bg-white dark:bg-slate-900 rounded-[2rem] p-10 border border-slate-200/60 dark:border-slate-800 shadow-sm flex flex-col gap-8 group/section transition-all duration-500">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-4">
						<div class="w-12 h-12 bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded-2xl flex items-center justify-center text-xl shadow-inner border border-amber-100 dark:border-amber-900/30 group-hover/section:scale-110 group-hover/section:-rotate-3 transition-all duration-300">🌐</div>
						<div class="flex flex-col">
							<h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase leading-none group-hover/section:text-amber-600 dark:group-hover/section:text-amber-400 transition-colors">Network</h2>
							<span class="text-[10px] font-bold text-amber-600/60 dark:text-amber-400/60 uppercase tracking-widest mt-1">{importantPorts.length} Open Gates</span>
						</div>
					</div>
					<a href="/ports" class="text-[10px] font-black bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 px-4 py-2 rounded-xl border border-amber-100 dark:border-amber-900/30 hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-all uppercase tracking-widest hover:scale-105">EXPLORE</a>
				</div>

				<div class="grid grid-cols-2 gap-5">
					{#each importantPorts.slice(0, 4) as p}
						<a 
							href={`http://localhost:${p.port}`} 
							target="_blank"
							class="p-5 bg-slate-50/40 dark:bg-slate-950/40 rounded-3xl border border-slate-100 dark:border-slate-800/60 hover:border-amber-300 dark:hover:border-amber-800 hover:bg-white dark:hover:bg-slate-800 transition-all duration-300 group flex flex-col items-center gap-2 relative overflow-hidden"
						>
							<div class="absolute right-3 top-3 text-slate-300 dark:text-slate-700 group-hover:text-amber-500 transition-colors duration-300">
								<svg class="w-3 h-3 group-hover:scale-125 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
							</div>
							<span class="text-xl font-black text-slate-900 dark:text-slate-200 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors tracking-tighter italic leading-none">{p.port}</span>
							<span class="text-[9px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-widest font-mono truncate w-full text-center">{p.process}</span>
						</a>
					{:else}
						<div class="col-span-full py-8 flex flex-col items-center gap-4 text-slate-300 dark:text-slate-700">
							<div class="text-3xl opacity-20 italic font-black uppercase leading-none">Isolated</div>
						</div>
					{/each}
				</div>
			</section>

		<!-- 🗄️ Database Summary -->
		<section class="bg-white dark:bg-slate-900 rounded-[2rem] p-10 border border-slate-200/60 dark:border-slate-800 shadow-sm flex flex-col gap-8 group/section transition-all duration-500">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center text-xl shadow-inner border border-emerald-100 dark:border-emerald-900/30 group-hover/section:scale-110 group-hover/section:rotate-3 transition-all duration-300">🗄️</div>
					<div class="flex flex-col">
						<h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase italic leading-none group-hover/section:text-emerald-600 dark:group-hover:section:text-emerald-400 transition-colors">Database Schema</h2>
						<span class="text-[10px] font-bold text-emerald-600/60 dark:text-emerald-400/60 uppercase tracking-widest mt-1">{tables.length} Schema Tables</span>
					</div>
				</div>
				<a href="/database" class="text-[10px] font-black bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 px-4 py-2 rounded-xl border border-emerald-100 dark:border-emerald-900/30 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-all uppercase tracking-widest hover:scale-105">SCHEMA MAP</a>
			</div>

			<div class="grid grid-cols-2 gap-5">
				{#each tables.slice(0, 4) as t}
					<a 
						href={`/table/${t}`}
						class="p-5 bg-slate-50/40 dark:bg-slate-950/40 rounded-3xl border border-slate-100 dark:border-slate-800/60 hover:border-emerald-300 dark:hover:border-emerald-800 hover:bg-white dark:hover:bg-slate-800 transition-all duration-300 group flex flex-col items-center gap-2 relative overflow-hidden"
					>
						<div class="absolute right-3 top-3 text-slate-300 dark:text-slate-700 group-hover:text-emerald-500 transition-colors duration-300">
							<svg class="w-3 h-3 group-hover:scale-125 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
						</div>
						<span class="text-xl font-black text-slate-900 dark:text-slate-200 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors tracking-tighter italic leading-none">{t}</span>
						<span class="text-[9px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-widest font-mono truncate w-full text-center">TABLE</span>
					</a>
				{:else}
					<div class="col-span-full py-8 flex flex-col items-center gap-4 text-slate-300 dark:text-slate-700">
						<div class="text-3xl opacity-20 italic font-black uppercase leading-none">Void Schema</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- 🗃️ Object Storage Summary -->
		<section class="bg-white dark:bg-slate-900 rounded-[2rem] p-10 border border-slate-200/60 dark:border-slate-800 shadow-sm flex flex-col gap-8 group/section transition-all duration-500">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 rounded-2xl flex items-center justify-center text-xl shadow-inner border border-indigo-100 dark:border-indigo-900/30 group-hover/section:scale-110 group-hover/section:-rotate-3 transition-all duration-300">🗃️</div>
					<div class="flex flex-col">
						<h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase italic leading-none group-hover/section:text-indigo-600 dark:group-hover:section:text-indigo-400 transition-colors">Object Storage</h2>
						<span class="text-[10px] font-bold text-indigo-600/60 dark:text-indigo-400/60 uppercase tracking-widest mt-1">{sources.length} Connected Data Vaults</span>
					</div>
				</div>
				<a href="/sources" class="text-[10px] font-black bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 px-4 py-2 rounded-xl border border-indigo-100 dark:border-indigo-900/30 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-all uppercase tracking-widest hover:scale-105">EXPLORE VAULTS</a>
			</div>

			<div class="flex flex-col gap-5 text-left">
				{#each sources.slice(0, 3) as s}
					<a href={`/sources/${s.id}`} class="p-5 bg-slate-50/40 dark:bg-slate-950/40 rounded-3xl border border-slate-100 dark:border-slate-800/60 flex items-center justify-between group hover:border-indigo-300 dark:hover:border-indigo-800 hover:bg-white dark:hover:bg-slate-800 transition-all duration-300">
						<div>
							<h3 class="font-black text-slate-800 dark:text-slate-200 uppercase tracking-tight italic group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors uppercase italic">{s.name}</h3>
							<p class="text-[9px] font-bold font-mono text-slate-400 dark:text-slate-500 uppercase tracking-tighter">{s.endpoint}</p>
						</div>
						<div class="px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-wider shadow-sm bg-indigo-500 text-white shadow-indigo-500/20">
							Connected
						</div>
					</a>
				{:else}
					<div class="py-8 flex flex-col items-center gap-4 text-slate-300 dark:text-slate-700">
						<div class="text-3xl opacity-20 italic font-black uppercase leading-none">Disconnected</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- Close Main Grid -->
		</div>
	{/if}
</div>