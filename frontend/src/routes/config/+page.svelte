<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";
	import Button from "$lib/components/common/Button.svelte";
	import Badge from "$lib/components/common/Badge.svelte";
	import Card from "$lib/components/common/Card.svelte";
	import InputField from "$lib/components/common/InputField.svelte";
	import Modal from "$lib/components/common/Modal.svelte";

	let config = $state({
		db_type: "postgres",
		db_file: "",
		db_host: "",
		db_port: "",
		db_user: "",
		db_password: "",
		db_name: ""
	});

	let loading = $state(true);
	let saving = $state(false);
	let notification = $state({ show: false, message: "", type: "success" });

	// Storage State
	let sources = $state([]);
	let detecting = $state(false);
	let newSource = $state({
		name: "",
		endpoint: "",
		access_key: "",
		secret_key: "",
		region: "us-east-1"
	});

	let deleteSourceModal = $state({ open: false, id: "", name: "" });

	onMount(async () => {
		try {
			const [dbRes, sourcesRes] = await Promise.all([
				axios.get("http://127.0.0.1:8000/config/db"),
				axios.get("http://127.0.0.1:8000/sources")
			]);
			config = { ...config, ...dbRes.data };
			sources = sourcesRes.data;
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

	async function detectStorage() {
		detecting = true;
		try {
			const res = await axios.get("http://127.0.0.1:8000/storage/detect");
			if (res.data && res.data.length > 0) {
				const detected = res.data[0];
				newSource.endpoint = detected.endpoint;
				newSource.name = detected.name;
				showNotification(`Detected: ${detected.name}`, "success");
			} else {
				showNotification("No local storage services found.", "error");
			}
		} catch (err) {
			showNotification("Detection failed.", "error");
		} finally {
			detecting = false;
		}
	}

	async function addSource() {
		if (!newSource.endpoint || !newSource.access_key) return;
		try {
			const res = await axios.post("http://127.0.0.1:8000/sources", newSource);
			sources = [...sources, res.data];
			newSource = { name: "", endpoint: "", access_key: "", secret_key: "", region: "us-east-1" };
			showNotification("Storage source added!", "success");
		} catch (err) {
			showNotification("Failed to add source.", "error");
		}
	}

	async function deleteSource(id: string) {
		try {
			await axios.delete(`http://127.0.0.1:8000/sources/${id}`);
			sources = sources.filter(s => s.id !== id);
			showNotification("Source removed.", "success");
		} catch (err) {
			showNotification("Delete failed.", "error");
		} finally {
			deleteSourceModal.open = false;
		}
	}

	function showNotification(message: string, type: string) {
		notification = { show: true, message, type };
		setTimeout(() => {
			notification.show = false;
		}, 6000);
	}
</script>

<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<a href="/" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-cyan-600 dark:hover:text-cyan-400 hover:border-cyan-200 dark:hover:border-cyan-800 transition-all shadow-sm" aria-label="Back to dashboard">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Settings<span class="text-indigo-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-14">Manage environmental connectivity variables dynamically</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-indigo-600 dark:text-indigo-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Loading Active Configuration...
		</div>
	{:else}
		<div class="grid grid-cols-1 xl:grid-cols-2 gap-8 items-start">
			<!-- DATABASE SECTION -->
			<Card class="h-full">
				<div class="absolute -right-20 -top-20 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl group-hover:bg-cyan-500/10 transition-colors duration-700 pointer-events-none"></div>

				<div class="flex items-center justify-between mb-8 pb-8 border-b border-slate-100 dark:border-slate-800">
					<div class="flex items-center gap-4">
						<div class="w-12 h-12 bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400 rounded-2xl flex items-center justify-center shadow-inner border border-cyan-100 dark:border-cyan-900/30">
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
						</div>
						<div>
							<h2 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight italic leading-none">Database Identity</h2>
							<p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-2 block">Connection Profile</p>
						</div>
					</div>
				</div>

				<form class="space-y-6" onsubmit={(e) => { e.preventDefault(); saveConfig(); }}>
					<!-- TABS FOR DIALECT -->
					<div class="flex bg-slate-100 dark:bg-slate-800/50 p-1.5 rounded-xl w-full">
						<button 
							type="button"
							onclick={() => config.db_type = 'postgres'}
							class="flex-1 py-2.5 text-[10px] uppercase tracking-widest font-black transition-all rounded-lg {config.db_type === 'postgres' ? 'bg-white dark:bg-slate-700 text-cyan-600 dark:text-cyan-400 shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}"
						>
							PostgreSQL Server
						</button>
						<button 
							type="button"
							onclick={() => config.db_type = 'sqlite'}
							class="flex-1 py-2.5 text-[10px] uppercase tracking-widest font-black transition-all rounded-lg {config.db_type === 'sqlite' ? 'bg-white dark:bg-slate-700 text-cyan-600 dark:text-cyan-400 shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}"
						>
							SQLite Local File
						</button>
					</div>

					{#if config.db_type === 'postgres'}
						<div class="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in zoom-in-95 duration-200">
							<InputField id="db_host" label="Host Address" bind:value={config.db_host} placeholder="localhost" mono />
							<InputField id="db_port" label="Traffic Port" bind:value={config.db_port} placeholder="5432" mono />
							<div class="md:col-span-2">
								<InputField id="db_name" label="Target Cluster / DB Name" bind:value={config.db_name} placeholder="postgres" mono />
							</div>
							<InputField id="db_user" label="Authentication User" bind:value={config.db_user} placeholder="postgres" mono />
							<InputField id="db_password" label="Authentication Core" type="password" bind:value={config.db_password} placeholder="••••••••" mono />
						</div>
					{:else}
						<div class="grid grid-cols-1 gap-6 animate-in fade-in zoom-in-95 duration-200">
							<InputField id="db_file" label="Absolute Path to .db File" bind:value={config.db_file} placeholder="/Users/username/project/database.sqlite" mono />
							
							<div class="px-5 py-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/30 rounded-2xl flex items-start gap-4">
								<div class="text-amber-500 mt-0.5">⚠️</div>
								<div>
									<p class="text-xs font-bold text-amber-800 dark:text-amber-500 uppercase tracking-widest">Local Target Warning</p>
									<p class="text-[10px] mt-1 text-amber-700 dark:text-amber-600 font-medium leading-relaxed">Use the exact absolute path to your local working database. The DevBeast UI will immediately sync and execute queries securely via this file handler.</p>
								</div>
							</div>
						</div>
					{/if}

					<div class="pt-6 mt-6 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end">
						<Button type="submit" loading={saving} variant="cyan" size="lg">
							Commit Database
						</Button>
					</div>
				</form>
			</Card>

			<!-- OBJECT STORAGE SECTION -->
			<Card class="h-full flex flex-col">
				<div class="absolute -right-20 -top-20 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl group-hover:bg-indigo-500/10 transition-colors duration-700 pointer-events-none"></div>

				<div class="flex items-center justify-between mb-8 pb-8 border-b border-slate-100 dark:border-slate-800">
					<div class="flex items-center gap-4">
						<div class="w-12 h-12 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 rounded-2xl flex items-center justify-center shadow-inner border border-indigo-100 dark:border-indigo-900/30">
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.022.547l-2.387 2.387a2 2 0 001.414 3.414h15.857a2 2 0 001.414-3.414l-2.387-2.387zM12 2a10 10 0 100 20 10 10 0 000-20z" /></svg>
						</div>
						<div>
							<h2 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight italic leading-none">Cloud Vaults</h2>
							<p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-2 block">S3 / MinIO Storage Sources</p>
						</div>
					</div>
					<Button onclick={detectStorage} loading={detecting} variant="secondary" size="sm">
						🔍 Smart Scan
					</Button>
				</div>

				<div class="space-y-8 flex-1">
					<!-- Active Sources -->
					<div>
						<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4 block">Active Connections</span>
						<div class="space-y-3">
							{#each sources as source}
								<div class="flex items-center justify-between p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/50 border border-slate-100 dark:border-slate-800 group/item">
									<div class="flex items-center gap-3">
										<div class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-500 text-sm">☁️</div>
										<div>
											<p class="text-xs font-bold text-slate-900 dark:text-white">{source.name}</p>
											<p class="text-[9px] text-slate-500 font-mono italic">{source.endpoint}</p>
										</div>
									</div>
									<button 
										onclick={() => deleteSourceModal = { open: true, id: source.id, name: source.name }}
										class="opacity-0 group-hover/item:opacity-100 p-2 text-rose-500 hover:bg-rose-500/10 rounded-lg transition-all"
									>
										🗑️
									</button>
								</div>
							{:else}
								<p class="text-[10px] text-slate-500 italic text-center py-4">No sources connected. Add one below.</p>
							{/each}
						</div>
					</div>

					<!-- Login to MinIO / Add Source -->
					<div class="pt-8 border-t border-slate-100 dark:border-slate-800">
						<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4 block">Login to Storage Console</span>
						<div class="space-y-4">
							<InputField id="storage_endpoint" label="Endpoint URL" bind:value={newSource.endpoint} placeholder="http://localhost:9000" mono />
							<div class="grid grid-cols-2 gap-4">
								<InputField id="storage_user" label="Username (Access Key)" bind:value={newSource.access_key} placeholder="minioadmin" mono />
								<InputField id="storage_pass" label="Password (Secret Key)" type="password" bind:value={newSource.secret_key} placeholder="••••••••" mono />
							</div>
							<Button onclick={addSource} variant="indigo" size="lg" class="w-full mt-4">
								Authorize & Connect
							</Button>
						</div>
					</div>
				</div>
			</Card>
		</div>
	{/if}

	<!-- Global Notification -->
	{#if notification.show}
		<div class="fixed bottom-10 right-10 z-[100] animate-in slide-in-from-bottom-5 duration-300">
			<Badge text={notification.message} variant={notification.type === 'success' ? 'success' : 'danger'} />
		</div>
	{/if}

	<!-- DELETE CONFIRMATION MODAL -->
	<Modal 
		open={deleteSourceModal.open}
		title="Remove Source"
		message={`Are you sure you want to disconnect '${deleteSourceModal.name}'? This will not delete the data on the server, but it will remove it from DevBeast access.`}
		confirmText="Disconnect Source"
		variant="danger"
		onConfirm={() => deleteSource(deleteSourceModal.id)}
		onCancel={() => deleteSourceModal.open = false}
	/>
</div>
