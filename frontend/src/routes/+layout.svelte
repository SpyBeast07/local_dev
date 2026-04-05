<script lang="ts">
	import "../app.css";
	import "../app.css";
	import { onMount } from "svelte";
	import { page } from "$app/state";
	let { children } = $props();

	let isDark = $state(true);
	let isCollapsed = $state(false);

	function isActive(path: string) {
		if (path === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(path);
	}

	function toggleTheme() {
		isDark = !isDark;
		if (typeof window !== 'undefined') {
			localStorage.setItem("devbeast-theme", isDark ? "dark" : "light");
		}
	}

	function toggleSidebar() {
		isCollapsed = !isCollapsed;
		if (typeof window !== 'undefined') {
			localStorage.setItem("devbeast-sidebar", isCollapsed ? "collapsed" : "expanded");
		}
	}

	onMount(() => {
		if (typeof window !== 'undefined') {
			const savedTheme = localStorage.getItem("devbeast-theme");
			if (savedTheme) {
				isDark = savedTheme === "dark";
			}
			const savedSidebar = localStorage.getItem("devbeast-sidebar");
			if (savedSidebar) {
				isCollapsed = savedSidebar === "collapsed";
			}
		}
	});
</script>

<div class={["flex h-screen w-screen overflow-hidden font-sans transition-colors duration-500", isDark ? "dark" : ""].join(" ")}>
	<div class="flex flex-1 w-full max-w-full overflow-hidden bg-slate-50 dark:bg-slate-900 transition-colors duration-500">
		<!-- Sidebar -->
		<aside class={[
			"relative bg-slate-950 text-slate-300 flex flex-col shrink-0 shadow-2xl z-10 border-r border-slate-900 transition-all duration-300 ease-in-out h-screen",
			isCollapsed ? "w-20 px-3 py-6" : "w-72 p-8"
		].join(" ")}>
			<!-- Toggle Button -->
			<button 
				onclick={toggleSidebar}
				class="absolute -right-3 top-10 w-6 h-6 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full flex items-center justify-center shadow-lg shadow-indigo-500/20 z-20 group border border-indigo-400"
				aria-label="Toggle Sidebar"
			>
				<svg 
					class={["w-4 h-4 transition-transform duration-300", isCollapsed ? "rotate-180" : ""].join(" ")}
					fill="none" 
					stroke="currentColor" 
					viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M15 19l-7-7 7-7" />
				</svg>
			</button>

			<div class="flex items-center gap-4 group cursor-default mb-10 overflow-hidden">
				<div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-2xl shadow-lg shadow-indigo-500/20 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shrink-0">
					🚀
				</div>
				{#if !isCollapsed}
					<div class="flex flex-col animate-in fade-in slide-in-from-left duration-300">
						<h1 class="text-xl font-black text-white tracking-tighter leading-none italic uppercase">DEV<span class="text-indigo-500">BEAST</span></h1>
						<span class="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-500 mt-1">Workspace v1.0</span>
					</div>
				{/if}
			</div>

			<nav class="flex flex-col gap-1 overflow-y-auto custom-scrollbar flex-1 pr-2 pb-4">
				
				<a href="/" class="flex items-center gap-3 p-3 rounded-xl transition-all duration-200 group border mb-4 {isActive('/') ? 'bg-slate-800 border-slate-700 text-white shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:text-white hover:border-slate-800'}" title="Dashboard">
					<span class="w-8 h-8 rounded-lg flex items-center justify-center text-lg transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/') ? 'bg-indigo-500/20 shadow-lg shadow-indigo-500/20' : 'bg-slate-900 group-hover:bg-indigo-500/10'}">🏠</span>
					{#if !isCollapsed}
						<span class="font-semibold tracking-tight {isActive('/') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Dashboard</span>
					{/if}
				</a>
				
				<!-- DOCKER ENGINE -->
				{#if !isCollapsed}
					<p class="text-[10px] font-black text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-2 animate-in fade-in duration-300">Docker Engine</p>
				{:else}
					<div class="h-px bg-slate-900 my-4 px-3"></div>
				{/if}
				
				<a href="/containers" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border {isActive('/containers') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Containers">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/containers') ? 'bg-blue-500/20 shadow-lg shadow-blue-500/20' : 'bg-slate-900 group-hover:bg-blue-500/10'}">🐳</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/containers') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Containers</span>
					{/if}
				</a>

				<a href="/deploy" class={["flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border", isActive('/deploy') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800', !isCollapsed ? "ml-5 border-l-2 border-l-slate-800" : ""].join(" ")} title="Deploy App">
					<span class="w-6 h-6 rounded-lg flex items-center justify-center text-xs transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/deploy') ? 'bg-rose-500/20 shadow-lg shadow-rose-500/20' : 'bg-slate-900 group-hover:bg-rose-500/10'}">🚀</span>
					{#if !isCollapsed}
						<span class="font-bold text-xs tracking-tight transition-colors {isActive('/deploy') ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}">Deploy App</span>
					{/if}
				</a>

				<a href="/images" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border {isActive('/images') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Images">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/images') ? 'bg-amber-500/20 shadow-lg shadow-amber-500/20' : 'bg-slate-900 group-hover:bg-amber-500/10'}">📦</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/images') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Images</span>
					{/if}
				</a>

				<a href="/volumes" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border {isActive('/volumes') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Volumes">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/volumes') ? 'bg-orange-500/20 shadow-lg shadow-orange-500/20' : 'bg-slate-900 group-hover:bg-orange-500/10'}">🧱</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/volumes') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Volumes</span>
					{/if}
				</a>

				<a href="/networks" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border {isActive('/networks') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Networks">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/networks') ? 'bg-cyan-500/20 shadow-lg shadow-cyan-500/20' : 'bg-slate-900 group-hover:bg-cyan-500/10'}">🕸️</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/networks') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Networks</span>
					{/if}
				</a>

				<!-- SYSTEM NETWORKING -->
				{#if !isCollapsed}
					<p class="text-[10px] font-black text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Networking</p>
				{:else}
					<div class="h-px bg-slate-900 my-4 px-3"></div>
				{/if}

				<a href="/ports" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border {isActive('/ports') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Active Ports">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/ports') ? 'bg-amber-500/20 shadow-lg shadow-amber-500/20' : 'bg-slate-900 group-hover:bg-amber-500/10'}">🌐</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/ports') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Active Ports</span>
					{/if}
				</a>

				<!-- DATABASE -->
				{#if !isCollapsed}
					<p class="text-[10px] font-black text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Database</p>
				{:else}
					<div class="h-px bg-slate-900 my-4 px-3"></div>
				{/if}

				<a href="/database" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border {isActive('/database') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Schema Explorer">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/database') ? 'bg-emerald-500/20 shadow-lg shadow-emerald-500/20' : 'bg-slate-900 group-hover:bg-emerald-500/10'}">🗄️</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/database') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Schema Explorer</span>
					{/if}
				</a>

				<a href="/relations" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border {isActive('/relations') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Relations">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:scale-125 group-hover:rotate-12 {isActive('/relations') ? 'bg-purple-500/20 shadow-lg shadow-purple-500/20' : 'bg-slate-900 group-hover:bg-purple-500/10'}">🧠</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/relations') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Relations</span>
					{/if}
				</a>

				<a href="/config" class="flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group border mt-6 {isActive('/config') ? 'bg-slate-800 border-slate-700 shadow-inner' : 'border-transparent hover:bg-slate-800/50 hover:border-slate-800'}" title="Settings">
					<span class="w-7 h-7 rounded-lg flex items-center justify-center text-sm transition-all duration-300 group-hover:rotate-90 {isActive('/config') ? 'bg-cyan-500/20 shadow-lg shadow-cyan-500/20' : 'bg-slate-900 group-hover:bg-cyan-500/10'}">⚙️</span>
					{#if !isCollapsed}
						<span class="font-semibold text-sm tracking-tight transition-colors {isActive('/config') ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}">Settings</span>
					{/if}
				</a>
			</nav>

			<div class="mt-auto flex flex-col gap-6 overflow-hidden">
				<!-- Theme Toggle -->
				<button 
					onclick={toggleTheme}
					class={[
						"flex items-center p-3 rounded-2xl bg-slate-950 border border-slate-800 hover:border-indigo-500/50 transition-all group",
						isCollapsed ? "justify-center" : "justify-between"
					].join(" ")}
					aria-label="Toggle dark mode"
				>
					{#if !isCollapsed}
						<span class="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1 animate-in fade-in duration-300">Appearance</span>
					{/if}
					<div class={["flex items-center gap-1 bg-slate-950 rounded-xl", !isCollapsed ? "p-1 border border-slate-800" : ""].join(" ")}>
						{#if !isCollapsed}
							<div class="w-8 h-8 flex items-center justify-center rounded-lg transition-all duration-300 {isDark ? 'text-slate-600' : 'bg-white text-indigo-600 shadow-lg scale-110'}">☀️</div>
							<div class="w-8 h-8 flex items-center justify-center rounded-lg transition-all duration-300 {isDark ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 scale-110' : 'text-slate-600'}">🌙</div>
						{:else}
							<div class="text-xl">{isDark ? '🌙' : '☀️'}</div>
						{/if}
					</div>
				</button>

				{#if !isCollapsed}
					<div class="bg-slate-900/50 p-4 rounded-2xl border border-slate-800/50 animate-in fade-in slide-in-from-bottom-2 duration-300">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-bold text-slate-400">System Load</span>
							<span class="text-[10px] px-1.5 py-0.5 bg-indigo-500/10 text-indigo-400 rounded-full font-bold">Stable</span>
						</div>
						<div class="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
							<div class="h-full w-[35%] bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"></div>
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
		<main class="flex-1 min-w-0 overflow-y-auto bg-slate-50 dark:bg-slate-950 relative transition-colors duration-500">
			<!-- Subtle background gradient -->
			<div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100/20 dark:from-indigo-900/10 via-transparent to-transparent pointer-events-none"></div>
			
			<div class="p-10 w-full max-w-7xl mx-auto relative z-0 text-slate-900 dark:text-slate-100">
				{@render children()}
			</div>
		</main>
	</div>
</div>
