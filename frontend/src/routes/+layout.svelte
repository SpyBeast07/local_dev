<script lang="ts">
	import "../app.css";
	import { onMount } from "svelte";
	import { page } from "$app/state";
	import axios from "axios";
	import NavItem from "$lib/components/common/NavItem.svelte";
	import { uiState } from "$lib/stores/uiStore.svelte";
	let { children } = $props();

	let systemStats = $state({
		cpu_usage: 0,
		memory_usage: 0,
		load_status: 'Stable'
	});

	async function fetchSystemStats() {
		try {
			const res = await axios.get("http://127.0.0.1:8000/system/stats");
			if (res.data.success) {
				systemStats = {
					cpu_usage: res.data.cpu_usage,
					memory_usage: res.data.memory_usage,
					load_status: res.data.load_status
				};
			}
		} catch (err) {
			console.error("Failed to fetch system stats", err);
		}
	}

	function isActive(path: string) {
		if (path === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(path);
	}

	onMount(() => {
		fetchSystemStats();
		const interval = setInterval(fetchSystemStats, 5000);
		return () => clearInterval(interval);
	});
</script>

<div class={["flex h-screen w-screen overflow-hidden font-sans transition-colors duration-500", uiState.isDark ? "dark" : ""].join(" ")} style="--root-bg: {uiState.isDark ? '#020617' : '#f8fafc'}">
	<div class="flex flex-1 w-full max-w-full overflow-hidden bg-slate-50 dark:bg-slate-900 transition-colors duration-500 min-h-0">
		<!-- Sidebar -->
		<aside class={[
			"relative bg-white dark:bg-slate-950 text-slate-600 dark:text-slate-300 flex flex-col shrink-0 shadow-2xl z-10 border-r border-slate-200 dark:border-slate-900 transition-all duration-300 ease-in-out h-screen",
			uiState.isCollapsed ? "w-20 px-3 py-6" : "w-72 p-8"
		].join(" ")}>
			<!-- Toggle Button -->
			<button 
				onclick={() => uiState.toggleSidebar()}
				class="absolute -right-3 top-10 w-6 h-6 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full flex items-center justify-center shadow-lg shadow-indigo-500/20 z-20 group border border-indigo-400"
				aria-label="Toggle Sidebar"
			>
				<svg 
					class={["w-4 h-4 transition-transform duration-300", uiState.isCollapsed ? "rotate-180" : ""].join(" ")}
					fill="none" 
					stroke="currentColor" 
					viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M15 19l-7-7 7-7" />
				</svg>
			</button>

			<div class="flex items-center gap-4 group cursor-default mb-10 overflow-hidden">
				<div class="w-10 h-10 bg-slate-100 dark:bg-slate-900 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-500/10 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shrink-0 overflow-hidden border border-slate-200 dark:border-slate-800">
					<img src="/logo.png" alt="DevBeast Logo" class="w-full h-full object-cover" />
				</div>
				{#if !uiState.isCollapsed}
					<div class="flex flex-col animate-in fade-in slide-in-from-left duration-300">
						<h1 class="text-xl font-black text-slate-900 dark:text-white tracking-tighter leading-none italic uppercase">DEV<span class="text-indigo-500">BEAST</span></h1>
						<span class="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-400 dark:text-slate-500 mt-1">Workspace v1.0</span>
					</div>
				{/if}
			</div>

			<nav class="flex flex-col gap-1 overflow-y-auto custom-scrollbar flex-1 pr-2 pb-4">
				
				<NavItem 
					href="/" 
					label="Dashboard" 
					icon="🏠" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/')} 
					color="indigo" 
					mt="mb-4"
				/>
				
				<!-- DOCKER ENGINE -->
				{#if !uiState.isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-2 animate-in fade-in duration-300">Docker Engine</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}
				
				<NavItem 
					href="/containers" 
					label="Containers" 
					icon="🐳" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/containers')} 
					color="blue" 
				/>

				<NavItem 
					href="/deploy" 
					label="Deploy App" 
					icon="🚀" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/deploy')} 
					color="rose" 
					indent={true}
				/>

				<NavItem 
					href="/images" 
					label="Images" 
					icon="📦" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/images')} 
					color="amber" 
				/>

				<NavItem 
					href="/volumes" 
					label="Volumes" 
					icon="🧱" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/volumes')} 
					color="orange" 
				/>

				<NavItem 
					href="/networks" 
					label="Networks" 
					icon="🕸️" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/networks')} 
					color="cyan" 
				/>

				<!-- SYSTEM NETWORKING -->
				{#if !uiState.isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Networking</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}

				<NavItem 
					href="/ports" 
					label="Active Ports" 
					icon="🌐" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/ports')} 
					color="amber" 
				/>

				<!-- STORAGE -->
				{#if !uiState.isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Storage</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}

				<NavItem 
					href="/sources" 
					label="Object Storage" 
					icon="📦" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/sources')} 
					color="blue" 
				/>

				<!-- DATABASE -->
				{#if !uiState.isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Database</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}

				<NavItem 
					href="/database" 
					label="Schema Explorer" 
					icon="🗄️" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/database')} 
					color="emerald" 
				/>

				<NavItem 
					href="/relations" 
					label="Relations" 
					icon="🧠" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/relations')} 
					color="purple" 
				/>

				<NavItem 
					href="/query-builder" 
					label="Query Builder" 
					icon="🧩" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/query-builder')} 
					color="indigo" 
				/>

				<NavItem 
					href="/workspace" 
					label="Workspace" 
					icon="🛠️" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/workspace')} 
					color="violet" 
				/>

				<NavItem 
					href="/config" 
					label="Settings" 
					icon="⚙️" 
					isCollapsed={uiState.isCollapsed} 
					active={isActive('/config')} 
					color="cyan" 
					mt="mt-6"
				/>
			</nav>

			<div class="mt-auto flex flex-col gap-6 overflow-hidden">

				{#if !uiState.isCollapsed}
					<div class="bg-slate-50/50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-100 dark:border-slate-800/50 animate-in fade-in slide-in-from-bottom-2 duration-300">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-bold text-slate-400">System Load</span>
							<span class={[
								"text-[10px] px-1.5 py-0.5 rounded-full font-bold transition-colors duration-500",
								systemStats.load_status === 'Heavy' ? 'bg-rose-500/10 text-rose-400' : 
								systemStats.load_status === 'Moderate' ? 'bg-amber-500/10 text-amber-400' : 
								'bg-indigo-500/10 text-indigo-400'
							].join(" ")}>{systemStats.load_status}</span>
						</div>
						<div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
							<div 
								class={[
									"h-full rounded-full transition-all duration-1000 ease-in-out",
									systemStats.cpu_usage > 80 ? 'bg-gradient-to-r from-rose-500 to-orange-500' :
									systemStats.cpu_usage > 40 ? 'bg-gradient-to-r from-amber-500 to-orange-500' :
									'bg-gradient-to-r from-indigo-500 to-purple-500'
								].join(" ")} 
								style="width: {systemStats.cpu_usage}%"
							></div>
						</div>
						<div class="mt-2 flex justify-between items-center text-[8px] font-bold text-slate-400 uppercase tracking-widest">
							<span>CPU: {systemStats.cpu_usage}%</span>
							<span>MEM: {systemStats.memory_usage}%</span>
						</div>
					</div>
				{:else}
					<div class="flex justify-center py-2 animate-in fade-in duration-300">
						<div class="w-3 h-3 bg-indigo-500 rounded-full animate-pulse shadow-lg shadow-indigo-500/50"></div>
					</div>
				{/if}

			</div>
		</aside>

		<!-- Main Content -->
		<main class="flex-1 min-w-0 min-h-0 bg-slate-50 dark:bg-slate-950 relative transition-colors duration-500 overflow-hidden flex flex-col">
			<!-- Subtle background gradient -->
			<div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100/20 dark:from-indigo-900/10 via-transparent to-transparent pointer-events-none"></div>
			
			<div class="flex-1 flex flex-col overflow-hidden min-h-0">
				<div class="w-full max-w-7xl mx-auto flex-1 flex flex-col min-h-0 px-10 pt-10 pb-0">
					{@render children()}
				</div>
			</div>
		</main>
	</div>
</div>
