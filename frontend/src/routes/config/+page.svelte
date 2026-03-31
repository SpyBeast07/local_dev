<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";

	let config = $state({
		db_host: "",
		db_port: "",
		db_user: "",
		db_password: "",
		db_name: ""
	});

	let loading = $state(true);
	let saving = $state(false);
	let notification = $state({ show: false, message: "", type: "success" });

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/config/db");
			config = { ...config, ...res.data };
		} catch (err) {
			console.error("Failed to load config", err);
			showNotification("Failed to load configuration from backend.", "error");
		} finally {
			loading = false;
		}
	});

	async function saveConfig() {
		saving = true;
		try {
			await axios.post("http://127.0.0.1:8000/config/db", config);
			showNotification("Database configuration successfully updated!", "success");
		} catch (err) {
			console.error("Failed to save config", err);
			showNotification("Failed to save configuration parameters.", "error");
		} finally {
			saving = false;
		}
	}

	function showNotification(message: string, type: string) {
		notification = { show: true, message, type };
		setTimeout(() => {
			notification.show = false;
		}, 3000);
	}
</script>

<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<a href="/" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-cyan-600 dark:hover:text-cyan-400 hover:border-cyan-200 dark:hover:border-cyan-800 transition-all shadow-sm" aria-label="Back to dashboard">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Settings<span class="text-cyan-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-14">Manage environmental connectivity variables dynamically</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-cyan-600 dark:text-cyan-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Loading Active Configuration...
		</div>
	{:else}
		<div class="max-w-3xl bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 md:p-12 border border-slate-200/60 dark:border-slate-800 shadow-xl relative overflow-hidden group">
			<div class="absolute -right-20 -top-20 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl group-hover:bg-cyan-500/10 transition-colors duration-700 pointer-events-none"></div>

			<div class="flex items-center justify-between mb-8 pb-8 border-b border-slate-100 dark:border-slate-800">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400 rounded-2xl flex items-center justify-center shadow-inner border border-cyan-100 dark:border-cyan-900/30">
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
					</div>
					<div>
						<h2 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight italic leading-none">Database Identity</h2>
						<p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-2 block">PostgreSQL Gateway Profile</p>
					</div>
				</div>

				{#if notification.show}
					<div 
						class="px-4 py-2 rounded-full text-xs font-black uppercase tracking-widest flex items-center gap-2 animate-in fade-in slide-in-from-right-4 
						{notification.type === 'success' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-500 border border-rose-500/20'}"
					>
						<span class="w-2 h-2 rounded-full {notification.type === 'success' ? 'bg-emerald-500' : 'bg-rose-500'} animate-pulse"></span>
						{notification.message}
					</div>
				{/if}
			</div>

			<form class="space-y-6" onsubmit={(e) => { e.preventDefault(); saveConfig(); }}>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					
					<!-- Host -->
					<div class="space-y-2">
						<label for="db_host" class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Host Address</label>
						<input 
							id="db_host"
							type="text" 
							bind:value={config.db_host}
							placeholder="localhost"
							class="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-700" 
						/>
					</div>

					<!-- Port -->
					<div class="space-y-2">
						<label for="db_port" class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Traffic Port</label>
						<input 
							id="db_port"
							type="text" 
							bind:value={config.db_port}
							placeholder="5432"
							class="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-700" 
						/>
					</div>

					<!-- Database Name -->
					<div class="space-y-2 md:col-span-2">
						<label for="db_name" class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Target Cluster / DB Name</label>
						<input 
							id="db_name"
							type="text" 
							bind:value={config.db_name}
							placeholder="postgres"
							class="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-700" 
						/>
					</div>

					<!-- User -->
					<div class="space-y-2">
						<label for="db_user" class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Authentication User</label>
						<input 
							id="db_user"
							type="text" 
							bind:value={config.db_user}
							placeholder="postgres"
							class="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-700" 
						/>
					</div>

					<!-- Password -->
					<div class="space-y-2">
						<label for="db_password" class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Authentication Core</label>
						<input 
							id="db_password"
							type="password" 
							bind:value={config.db_password}
							placeholder="••••••••"
							class="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-700" 
						/>
					</div>
				</div>

				<div class="pt-6 mt-6 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end">
					<button 
						type="submit" 
						disabled={saving}
						class="bg-cyan-500 hover:bg-cyan-400 text-white font-black italic uppercase tracking-widest text-xs px-8 py-4 rounded-xl shadow-lg shadow-cyan-500/20 transition-all hover:-translate-y-1 hover:shadow-cyan-500/40 disabled:opacity-50 disabled:hover:translate-y-0 flex items-center gap-3"
					>
						{#if saving}
							<div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
							Committing...
						{:else}
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
							Commit Configuration
						{/if}
					</button>
				</div>
			</form>
		</div>
	{/if}
</div>
