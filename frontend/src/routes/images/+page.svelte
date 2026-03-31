<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";

	interface DockerImage {
		Repository: string;
		Tag: string;
		ImageID: string;
		CreatedSince: string;
		Size: string;
	}

	let images = $state<DockerImage[]>([]);
	let loading = $state(true);
	let pullImageName = $state("");
	let pulling = $state(false);
	let deleting = $state<string | null>(null);

	async function fetchImages() {
		try {
			const res = await axios.get("http://127.0.0.1:8000/images");
			images = Array.isArray(res.data) ? res.data : [];
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	}

	async function pullImage() {
		if (!pullImageName) return;
		pulling = true;
		try {
			await axios.post("http://127.0.0.1:8000/images/pull", { image: pullImageName });
			pullImageName = "";
			await fetchImages();
		} catch (err) {
			console.error("Action failed", err);
		} finally {
			pulling = false;
		}
	}

	async function deleteImage(id: string) {
		deleting = id;
		try {
			await axios.delete(`http://127.0.0.1:8000/images/${id}`);
			await fetchImages();
		} catch (err) {
			console.error("Action failed", err);
		} finally {
			deleting = null;
		}
	}

	onMount(fetchImages);
</script>

<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Image Registry<span class="text-amber-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-2">Manage Local Base Images</p>
	</header>

	<div class="bg-white dark:bg-slate-900 rounded-[2rem] p-6 text-slate-400 border border-slate-200 dark:border-slate-800 flex gap-4 items-center">
		<input 
			type="text" 
			bind:value={pullImageName} 
			placeholder="e.g. postgres:15-alpine" 
			class="flex-1 bg-slate-50 dark:bg-slate-950 px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 text-sm font-bold tracking-wider placeholder:text-slate-500 focus:outline-none focus:border-amber-500"
			onkeydown={(e) => e.key === 'Enter' && pullImage()}
		/>
		<button 
			onclick={pullImage} 
			disabled={pulling || !pullImageName}
			class="bg-amber-500 hover:bg-amber-600 px-6 py-3 rounded-xl text-white font-black tracking-widest uppercase transition-colors flex items-center gap-2 text-sm disabled:opacity-50"
		>
			{#if pulling}
				<div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
				Pulling...
			{:else}
				⏬ Pull Image
			{/if}
		</button>
	</div>

	{#if loading}
		<div class="flex items-center gap-4 text-amber-600 dark:text-amber-400 font-black animate-pulse uppercase tracking-wider text-sm ml-2">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Loading Registry...
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
			{#each images as img}
				<div class="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col gap-4 relative overflow-hidden group hover:border-amber-500/50 transition-colors">
					<div class="flex flex-col">
						<h3 class="font-black text-slate-900 dark:text-slate-100 uppercase tracking-tight italic break-all">{img.Repository || '<none>'}</h3>
						<span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mt-1">TAG: {img.Tag || '<none>'}</span>
					</div>

					<div class="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-4 mt-auto">
						<div class="flex flex-col">
							<span class="text-[9px] font-black tracking-widest uppercase text-slate-400">{img.Size}</span>
							<span class="text-[9px] font-bold tracking-widest uppercase text-slate-500 mt-0.5">{img.CreatedSince}</span>
						</div>

						<button 
							onclick={() => deleteImage(img.ImageID)} 
							disabled={deleting === img.ImageID}
							title="Delete Image"
							class="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/10 text-rose-500 border border-rose-100 dark:border-rose-900/20 flex items-center justify-center hover:bg-rose-500 hover:text-white transition-all disabled:opacity-50"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
