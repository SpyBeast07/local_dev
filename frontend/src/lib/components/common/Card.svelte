<script lang="ts">
	let { 
		children, 
		variant = "glass",
		padding = "p-8 md:p-12",
		class: className = ""
	}: { 
		children: any,
		variant?: "glass" | "solid",
		padding?: string,
		class?: string
	} = $props();

	const variants = {
		glass: "bg-white dark:bg-slate-900 border-slate-200/60 dark:border-slate-800 shadow-xl overflow-hidden group",
		solid: "bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-800 shadow-sm"
	};
</script>

<div class="rounded-[2.5rem] border transition-all duration-300 {variants[variant]} {padding} {className}">
	{@render children()}
</div>
