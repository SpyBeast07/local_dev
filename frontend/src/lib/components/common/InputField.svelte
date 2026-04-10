<script lang="ts">
	let { 
		label, 
		id, 
		value = $bindable(), 
		type = "text", 
		placeholder = "",
		mono = false
	}: { 
		label: string,
		id: string,
		value: any,
		type?: string,
		placeholder?: string,
		mono?: boolean
	} = $props();
</script>

<div class="space-y-2">
	<label for={id} class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">{label}</label>
	<input 
		{id}
		{type} 
		bind:value={value}
		{placeholder}
		class="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-700 {mono ? 'font-mono' : ''}" 
	/>
</div>
