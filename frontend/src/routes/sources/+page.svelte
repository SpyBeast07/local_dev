<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, slide } from 'svelte/transition';
	import Button from '$lib/components/common/Button.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import InputField from '$lib/components/common/InputField.svelte';

	interface Source {
		id: string;
		name: string;
		endpoint: string;
		access_key: string;
		secret_key: string;
		region: string;
		is_online: boolean;
	}

	let sources = $state<Source[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// New Source Form
	let showAddModal = $state(false);
	let newSource = $state({
		name: '',
		endpoint: 'http://localhost:9000',
		access_key: 'minioadmin',
		secret_key: 'minioadmin',
		region: 'us-east-1'
	});


	async function fetchSources() {
		loading = true;
		try {
			const res = await fetch('http://localhost:8000/sources');
			sources = await res.json();
		} catch (err) {
			error = "Failed to load sources";
		} finally {
			loading = false;
		}
	}

	async function addSource() {
		try {
			const res = await fetch('http://localhost:8000/sources', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newSource)
			});
			if (res.ok) {
				showAddModal = false;
				fetchSources();
				newSource = { name: '', endpoint: 'http://localhost:9000', access_key: 'minioadmin', secret_key: 'minioadmin', region: 'us-east-1' };
			}
		} catch (err) {
			alert("Failed to add source");
		}
	}

	async function deleteSource(id: string) {
		if (!confirm("Are you sure you want to delete this source?")) return;
		try {
			await fetch(`http://localhost:8000/sources/${id}`, { method: 'DELETE' });
			fetchSources();
		} catch (err) {
			alert("Failed to delete source");
		}
	}

	async function testConnection(id: string) {
		try {
			const res = await fetch(`http://localhost:8000/sources/${id}/test`, { method: 'POST' });
			const data = await res.json();
			if (data.success) {
				alert("Success: " + data.message);
			} else {
				alert("Error: " + data.error);
			}
		} catch (err) {
			alert("Connection failed");
		}
	}

	onMount(fetchSources);
</script>

<div class="space-y-12" in:fade>
	<div class="flex items-end justify-between">
		<header class="flex flex-col gap-3">
			<div class="flex items-center gap-4">
				<h1 class="text-6xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">
					Object <span class="text-indigo-600 uppercase italic">Storage.</span>
				</h1>
				<button 
					onclick={fetchSources}
					class="w-10 h-10 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center hover:text-indigo-600 transition-all shadow-sm active:scale-90"
					title="Refresh Status"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
				</button>
			</div>
			<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-1">
				Synchronized S3 & MinIO Data Vaults
			</p>
		</header>

		<Button onclick={() => showAddModal = true} variant="indigo" size="lg">
			+ New Connection
		</Button>
	</div>

	{#if loading}
		<div class="flex flex-col items-center justify-center py-20 grayscale opacity-50">
			<div class="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
			<p class="mt-4 font-bold text-slate-500 uppercase tracking-widest text-[10px]">Scanning Data Vaults...</p>
		</div>
	{:else if sources.length === 0}
		<Card variant="solid" class="py-20 flex flex-col items-center text-center px-6 border-dashed">
			<div class="text-6xl mb-6">📦</div>
			<h3 class="text-2xl font-black text-slate-900 dark:text-white uppercase italic tracking-tight">No Vaults Connected</h3>
			<p class="text-slate-500 mt-2 max-w-sm font-medium">Initialize a MinIO or S3 instance to start exploring buckets and objects in real-time.</p>
			<div class="mt-8">
				<Button onclick={() => showAddModal = true} variant="indigo">Connect Now</Button>
			</div>
		</Card>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
			{#each sources as source}
				<Card padding="p-8" class="relative group h-full">
					<div class="absolute -right-10 -top-10 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-colors pointer-events-none"></div>
					
					<div class="flex items-start justify-between mb-8">
						<div class="w-14 h-14 bg-indigo-50 dark:bg-indigo-900/20 rounded-2xl flex items-center justify-center text-3xl shadow-inner border border-indigo-100 dark:border-indigo-900/30 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
							☁️
						</div>
						<div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-all translate-y-2 group-hover:translate-y-0">
							<Button onclick={() => testConnection(source.id)} variant="ghost" size="sm" class="p-2 min-w-0">⚡</Button>
							<Button onclick={() => deleteSource(source.id)} variant="ghost" size="sm" class="p-2 min-w-0 text-rose-500">🗑️</Button>
						</div>
					</div>

					<div class="space-y-4">
						<div class="flex items-center justify-between">
							<h3 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight italic">{source.name}</h3>
							{#if source.is_online}
								<span class="flex items-center gap-1.5 text-[9px] font-black text-emerald-500 uppercase tracking-widest bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/10">
									<span class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
									Online
								</span>
							{:else}
								<span class="flex items-center gap-1.5 text-[9px] font-black text-rose-500 uppercase tracking-widest bg-rose-500/10 px-2 py-1 rounded-full border border-rose-500/10">
									<span class="w-1.5 h-1.5 bg-rose-500 rounded-full"></span>
									Offline
								</span>
							{/if}
						</div>
						<Badge text={source.endpoint} variant="neutral" />
					</div>

					<div class="mt-10">
						<a 
							href={source.is_online ? `/sources/${source.id}` : '#'}
							class={[
								"w-full py-4 rounded-2xl font-black uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 transition-all shadow-lg active:scale-95",
								source.is_online 
									? "bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-indigo-600 dark:hover:bg-indigo-50 dark:hover:text-indigo-600" 
									: "bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-200 dark:border-slate-700"
							].join(" ")}
						>
							{source.is_online ? 'Explore Vault' : 'Vault Inaccessible'}
						</a>
					</div>
				</Card>
			{/each}
		</div>
	{/if}
</div>

{#if showAddModal}
	<div class="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6" transition:fade>
		<Card padding="p-10" class="w-full max-w-lg relative animate-in zoom-in-95 duration-200">
			<div class="flex items-center justify-between mb-8 pb-8 border-b border-slate-100 dark:border-slate-800">
				<div>
					<h2 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">Add <span class="text-indigo-600">Vault</span></h2>
					<p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mt-2">S3 Instance Credentials</p>
				</div>
				<button onclick={() => showAddModal = false} class="w-10 h-10 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center transition-colors text-slate-400">✕</button>
			</div>
			
			<div class="space-y-6">
				<InputField id="source-name" label="Friendly Name" bind:value={newSource.name} placeholder="e.g. Local MinIO" />
				<InputField id="source-endpoint" label="Endpoint URL" bind:value={newSource.endpoint} placeholder="http://localhost:9000" mono />
				<div class="grid grid-cols-2 gap-4">
					<InputField id="source-access-key" label="Access Key" bind:value={newSource.access_key} placeholder="minioadmin" mono />
					<InputField id="source-secret-key" label="Secret Key" type="password" bind:value={newSource.secret_key} placeholder="••••••••" mono />
				</div>
			</div>

			<div class="mt-10 flex gap-4">
				<Button onclick={() => showAddModal = false} variant="secondary" class="flex-1">Cancel</Button>
				<Button onclick={addSource} variant="indigo" class="flex-1">Connect Vault</Button>
			</div>
		</Card>
	</div>
{/if}

<style>
	/* Styles here if needed */
</style>
