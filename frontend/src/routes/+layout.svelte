<script lang="ts">
	import "../app.css";
	import { onMount } from "svelte";
	import { page } from "$app/state";
	import NavItem from "$lib/components/common/NavItem.svelte";
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

<div class={["flex h-screen w-screen overflow-hidden font-sans transition-colors duration-500", isDark ? "dark" : ""].join(" ")} style="--root-bg: {isDark ? '#020617' : '#f8fafc'}">
	<div class="flex flex-1 w-full max-w-full overflow-hidden bg-slate-50 dark:bg-slate-900 transition-colors duration-500 min-h-0">
		<!-- Sidebar -->
		<aside class={[
			"relative bg-white dark:bg-slate-950 text-slate-600 dark:text-slate-300 flex flex-col shrink-0 shadow-2xl z-10 border-r border-slate-200 dark:border-slate-900 transition-all duration-300 ease-in-out h-screen",
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
				<div class="w-10 h-10 bg-slate-100 dark:bg-slate-900 rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-500/10 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shrink-0 overflow-hidden border border-slate-200 dark:border-slate-800">
					<img src="/logo.png" alt="DevBeast Logo" class="w-full h-full object-cover" />
				</div>
				{#if !isCollapsed}
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
					{isCollapsed} 
					active={isActive('/')} 
					color="indigo" 
					mt="mb-4"
				/>
				
				<!-- DOCKER ENGINE -->
				{#if !isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-2 animate-in fade-in duration-300">Docker Engine</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}
				
				<NavItem 
					href="/containers" 
					label="Containers" 
					icon="🐳" 
					{isCollapsed} 
					active={isActive('/containers')} 
					color="blue" 
				/>

				<NavItem 
					href="/deploy" 
					label="Deploy App" 
					icon="🚀" 
					{isCollapsed} 
					active={isActive('/deploy')} 
					color="rose" 
					indent={true}
				/>

				<NavItem 
					href="/images" 
					label="Images" 
					icon="📦" 
					{isCollapsed} 
					active={isActive('/images')} 
					color="amber" 
				/>

				<NavItem 
					href="/volumes" 
					label="Volumes" 
					icon="🧱" 
					{isCollapsed} 
					active={isActive('/volumes')} 
					color="orange" 
				/>

				<NavItem 
					href="/networks" 
					label="Networks" 
					icon="🕸️" 
					{isCollapsed} 
					active={isActive('/networks')} 
					color="cyan" 
				/>

				<!-- SYSTEM NETWORKING -->
				{#if !isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Networking</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}

				<NavItem 
					href="/ports" 
					label="Active Ports" 
					icon="🌐" 
					{isCollapsed} 
					active={isActive('/ports')} 
					color="amber" 
				/>

				<!-- STORAGE -->
				{#if !isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Storage</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}

				<NavItem 
					href="/sources" 
					label="Object Storage" 
					icon="📦" 
					{isCollapsed} 
					active={isActive('/sources')} 
					color="blue" 
				/>

				<!-- DATABASE -->
				{#if !isCollapsed}
					<p class="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-[0.2em] mb-2 px-3 mt-6 animate-in fade-in duration-300">Database</p>
				{:else}
					<div class="h-px bg-slate-100 dark:bg-slate-900 my-4 px-3"></div>
				{/if}

				<NavItem 
					href="/database" 
					label="Schema Explorer" 
					icon="🗄️" 
					{isCollapsed} 
					active={isActive('/database')} 
					color="emerald" 
				/>

				<NavItem 
					href="/relations" 
					label="Relations" 
					icon="🧠" 
					{isCollapsed} 
					active={isActive('/relations')} 
					color="purple" 
				/>

				<NavItem 
					href="/query-builder" 
					label="Query Builder" 
					icon="🧩" 
					{isCollapsed} 
					active={isActive('/query-builder')} 
					color="indigo" 
				/>

				<NavItem 
					href="/workspace" 
					label="Workspace" 
					icon="🛠️" 
					{isCollapsed} 
					active={isActive('/workspace')} 
					color="violet" 
				/>

				<NavItem 
					href="/config" 
					label="Settings" 
					icon="⚙️" 
					{isCollapsed} 
					active={isActive('/config')} 
					color="cyan" 
					mt="mt-6"
				/>
			</nav>

			<div class="mt-auto flex flex-col gap-6 overflow-hidden">
				<!-- Theme Toggle -->
				<button 
					onclick={toggleTheme}
					class={[
						"flex items-center p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 transition-all group",
						isCollapsed ? "justify-center" : "justify-between"
					].join(" ")}
					aria-label="Toggle dark mode"
				>
					{#if !isCollapsed}
						<span class="text-xs font-bold text-slate-400 uppercase tracking-widest pl-1 animate-in fade-in duration-300">Appearance</span>
					{/if}
					<div class={["flex items-center gap-1 bg-slate-100 dark:bg-slate-950 rounded-xl", !isCollapsed ? "p-1 border border-slate-200 dark:border-slate-800" : ""].join(" ")}>
						{#if !isCollapsed}
							<div class="w-8 h-8 flex items-center justify-center rounded-lg transition-all duration-300 {isDark ? 'text-slate-600' : 'bg-white text-indigo-600 shadow-lg scale-110'}">☀️</div>
							<div class="w-8 h-8 flex items-center justify-center rounded-lg transition-all duration-300 {isDark ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 scale-110' : 'text-slate-600'}">🌙</div>
						{:else}
							<div class="text-xl">{isDark ? '🌙' : '☀️'}</div>
						{/if}
					</div>
				</button>

				{#if !isCollapsed}
					<div class="bg-slate-50/50 dark:bg-slate-900/50 p-4 rounded-2xl border border-slate-100 dark:border-slate-800/50 animate-in fade-in slide-in-from-bottom-2 duration-300">
						<div class="flex items-center justify-between mb-2">
							<span class="text-xs font-bold text-slate-400">System Load</span>
							<span class="text-[10px] px-1.5 py-0.5 bg-indigo-500/10 text-indigo-400 rounded-full font-bold">Stable</span>
						</div>
						<div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
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
