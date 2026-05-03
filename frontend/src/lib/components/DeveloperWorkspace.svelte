<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { workspaceStore } from '$lib/stores/workspaceStore';
	import QueryHistory from './QueryHistory.svelte';
	import SnippetManager from './SnippetManager.svelte';
	import RoleViewer from './RoleViewer.svelte';
	import SchemaDiff from './SchemaDiff.svelte';
	import InsightDashboard from './InsightDashboard.svelte';
	import RealTimeMonitor from './RealTimeMonitor.svelte';

	let activeTab = $state('intelligence'); // intelligence, audit, history, snippets

	onMount(() => {
		workspaceStore.fetchAll();
	});

	const tabs = [
		{ id: 'intelligence', label: 'Architecture', icon: '📡', tooltip: 'Aggregated Performance & Table Impact' },
		{ id: 'audit', label: 'Auditor', icon: '🌓', tooltip: 'Structural Comparative & Safe Migrations' },
		{ id: 'history', label: 'History', icon: '📜', tooltip: 'Execution Audit & Performance Logs' },
		{ id: 'snippets', label: 'Library', icon: '📝', tooltip: 'SQL Utility Assets & Favorites' }
	];
</script>

<div class="flex-1 flex flex-col gap-8 min-h-0 animate-in fade-in duration-1000 pb-10 pr-4">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-4xl font-black text-slate-900 dark:text-white tracking-tighter uppercase italic">
				Workspace <span class="text-indigo-500">Intelligence</span>
			</h1>
			<p class="text-slate-500 dark:text-slate-400 text-sm font-bold mt-1 uppercase tracking-widest leading-none italic">
				Deterministic diagnostics, architectural auditing, and real-time awareness.
			</p>
		</div>
		<div class="flex items-center gap-3">
			<button 
				onclick={() => workspaceStore.fetchAll()}
				disabled={$workspaceStore.isLoading}
				class="px-5 py-2.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:text-indigo-500 transition-all flex items-center gap-2 shadow-sm active:scale-95"
			>
				{#if $workspaceStore.isLoading}
					<div class="w-3 h-3 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
				{:else}
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
				{/if}
				Refresh Sync
			</button>
		</div>
	</div>

	<!-- Main Tabbed Interface -->
	<div class="flex-1 flex flex-col min-h-0 bg-white/40 dark:bg-slate-900/40 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden backdrop-blur-3xl animate-in zoom-in-95 duration-700">
		<!-- Tab Switcher -->
		<div class="flex items-center p-4 gap-2 bg-slate-50/50 dark:bg-slate-950/20 border-b border-slate-200 dark:border-slate-800 overflow-x-auto no-scrollbar">
			{#each tabs as tab}
				<button 
					onclick={() => activeTab = tab.id}
					title={tab.tooltip}
					class={[
						"px-6 py-3 rounded-2xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-3 whitespace-nowrap",
						activeTab === tab.id 
							? "bg-white dark:bg-slate-800 text-indigo-500 shadow-xl shadow-indigo-500/10 border border-indigo-500/20 scale-[1.02]" 
							: "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-200/50 dark:hover:bg-slate-800/30 border border-transparent"
					].join(" ")}
				>
					<span class="text-sm">{tab.icon}</span>
					{tab.label}
				</button>
			{/each}
		</div>

		<!-- Tab Content -->
		<div class="flex-1 overflow-hidden relative">
			{#if activeTab === 'intelligence'}
				<InsightDashboard />
			{:else if activeTab === 'awareness'}
				<RealTimeMonitor />
			{:else if activeTab === 'audit'}
				<SchemaDiff />
			{:else if activeTab === 'security'}
				<RoleViewer />
			{:else if activeTab === 'history'}
				<QueryHistory />
			{:else if activeTab === 'snippets'}
				<SnippetManager />
			{/if}
		</div>
	</div>
</div>

<style>
	:global(.custom-scrollbar::-webkit-scrollbar) {
		width: 4px;
		height: 4px;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-track) {
		background: transparent;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-thumb) {
		background: rgba(99, 102, 241, 0.1);
		border-radius: 10px;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) {
		background: rgba(99, 102, 241, 0.3);
	}
	.no-scrollbar::-webkit-scrollbar {
		display: none;
	}
	.no-scrollbar {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}
</style>
