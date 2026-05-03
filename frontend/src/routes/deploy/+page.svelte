<script lang="ts">
	import axios from "axios";

	let form = $state({
		image: "",
		name: "",
		ports: [""],
		envs: [""]
	});

	let deploying = $state(false);
	let successMsg = $state("");
	let errorMsg = $state("");

	function addPort() { form.ports = [...form.ports, ""]; }
	function removePort(i: number) { form.ports = form.ports.filter((_, idx) => idx !== i); }

	function addEnv() { form.envs = [...form.envs, ""]; }
	function removeEnv(i: number) { form.envs = form.envs.filter((_, idx) => idx !== i); }

	async function deployContainer() {
		errorMsg = "";
		successMsg = "";
		
		if (!form.image) {
			errorMsg = "Image name is required";
			return;
		}

		deploying = true;
		try {
			// Filter out empty strings
			const payload = {
				image: form.image,
				name: form.name,
				ports: form.ports.filter(p => p.trim() !== ""),
				envs: form.envs.filter(e => e.trim() !== "")
			};

			const res = await axios.post("http://127.0.0.1:8000/containers/deploy", payload);
			if (res.data.error) {
				errorMsg = res.data.error;
			} else {
				successMsg = `Container launched successfully! ID: ${res.data.id.slice(0, 12)}`;
				// Reset form
				form = { image: "", name: "", ports: [""], envs: [""] };
			}
		} catch (err: any) {
			errorMsg = err.message || "Failed to deploy container";
		} finally {
			deploying = false;
		}
	}
</script>

<div class="flex flex-col gap-10 pb-20 max-w-4xl">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Deploy<span class="text-rose-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-2">Docker Container Orchestration Engine</p>
	</header>

	<div class="bg-white dark:bg-slate-900 rounded-[2.5rem] p-10 border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col gap-8 relative overflow-hidden">
		<!-- Core Info -->
		<div class="space-y-4">
			<h2 class="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-widest italic flex items-center gap-2"><span class="text-rose-500">1</span> Base Configuration</h2>
			
			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
				<div class="flex flex-col gap-2">
					<label for="image-name" class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Image Name (required)</label>
					<input 
						id="image-name"
						type="text" 
						bind:value={form.image} 
						placeholder="e.g. nginx:latest" 
						class="bg-slate-50 dark:bg-slate-950 px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 text-sm font-bold tracking-wider placeholder:text-slate-500 focus:outline-none focus:border-rose-500 transition-colors"
					/>
				</div>
				<div class="flex flex-col gap-2">
					<label for="container-name" class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Container Name (optional)</label>
					<input 
						id="container-name"
						type="text" 
						bind:value={form.name} 
						placeholder="e.g. web-server" 
						class="bg-slate-50 dark:bg-slate-950 px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 text-sm font-bold tracking-wider placeholder:text-slate-500 focus:outline-none focus:border-rose-500 transition-colors"
					/>
				</div>
			</div>
		</div>

		<!-- Networking -->
		<div class="space-y-4 pt-6 border-t border-slate-100 dark:border-slate-800">
			<div class="flex justify-between items-center">
				<h2 class="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-widest italic flex items-center gap-2"><span class="text-rose-500">2</span> Port Mappings</h2>
				<button onclick={addPort} class="text-[10px] bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 px-3 py-1.5 rounded-lg font-bold uppercase tracking-widest transition-colors flex items-center gap-1">+ Add Binding</button>
			</div>

			<div class="flex flex-col gap-3">
				{#each form.ports as port, i}
					<div class="flex gap-4">
						<input 
							type="text" 
							bind:value={form.ports[i]} 
							placeholder="e.g. 8080:80" 
							class="flex-1 bg-slate-50 dark:bg-slate-950 px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 text-sm font-bold tracking-wider placeholder:text-slate-500 focus:outline-none focus:border-rose-500 transition-colors"
						/>
						<button onclick={() => removePort(i)} aria-label="Remove port binding" class="w-12 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 hover:bg-rose-500 hover:text-white hover:border-rose-500 transition-all">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
						</button>
					</div>
				{/each}
			</div>
		</div>

		<!-- Environment Variables -->
		<div class="space-y-4 pt-6 border-t border-slate-100 dark:border-slate-800">
			<div class="flex justify-between items-center">
				<h2 class="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-widest italic flex items-center gap-2"><span class="text-rose-500">3</span> Environment Variables</h2>
				<button onclick={addEnv} class="text-[10px] bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 px-3 py-1.5 rounded-lg font-bold uppercase tracking-widest transition-colors flex items-center gap-1">+ Add Env</button>
			</div>

			<div class="flex flex-col gap-3">
				{#each form.envs as env, i}
					<div class="flex gap-4">
						<input 
							type="text" 
							bind:value={form.envs[i]} 
							placeholder="e.g. POSTGRES_PASSWORD=secret" 
							class="flex-1 bg-slate-50 dark:bg-slate-950 px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 text-sm font-bold tracking-wider placeholder:text-slate-500 focus:outline-none focus:border-rose-500 transition-colors font-mono"
						/>
						<button onclick={() => removeEnv(i)} aria-label="Remove environment variable" class="w-12 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 hover:bg-rose-500 hover:text-white hover:border-rose-500 transition-all">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
						</button>
					</div>
				{/each}
			</div>
		</div>

		{#if errorMsg}
			<div class="bg-rose-500/10 border border-rose-500/30 text-rose-500 dark:text-rose-400 p-4 rounded-xl text-sm font-bold uppercase tracking-widest break-all">
				⚠️ {errorMsg}
			</div>
		{/if}

		{#if successMsg}
			<div class="bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 p-4 rounded-xl text-sm font-bold uppercase tracking-widest break-all">
				✅ {successMsg}
			</div>
		{/if}

		<button 
			onclick={deployContainer} 
			disabled={deploying || !form.image}
			class="mt-4 bg-rose-500 hover:bg-rose-600 px-8 py-4 rounded-xl text-white font-black tracking-widest uppercase transition-colors flex justify-center items-center gap-3 text-lg shadow-lg shadow-rose-500/20 disabled:opacity-50 disabled:shadow-none"
		>
			{#if deploying}
				<div class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
				Deploying Container...
			{:else}
				🚀 Launch Workload
			{/if}
		</button>
	</div>
</div>
