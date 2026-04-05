<script lang="ts">
	import { workspaceStore } from '$lib/stores/workspaceStore';
</script>

<div class="flex flex-col h-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
	<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 flex items-center justify-between">
		<div>
			<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest">Database Security Suite</h3>
			<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Audit of roles and granular table privileges</p>
		</div>
		<div class="flex items-center gap-2">
			<span class="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-black uppercase tracking-widest border border-emerald-500/20">
				{$workspaceStore.roles.length} Roles Active
			</span>
		</div>
	</div>

	<div class="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-10">
		<!-- Roles Section -->
		<section>
			<div class="flex items-center gap-3 mb-4">
				<span class="text-xs font-black text-slate-400 uppercase tracking-widest italic">Defined Roles</span>
				<div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
			</div>
			
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each $workspaceStore.roles as role}
					<div class="flex flex-col p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm hover:shadow-xl hover:border-emerald-500/20 transition-all">
						<div class="flex items-center justify-between mb-4">
							<h4 class="text-[13px] font-black text-slate-800 dark:text-white uppercase tracking-tighter italic leading-none">{role.name}</h4>
							{#if role.is_superuser}
								<span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse shadow-lg shadow-rose-500/50" title="Superuser Status"></span>
							{:else}
								<span class="w-2.5 h-2.5 rounded-full bg-emerald-500" title="Regular User"></span>
							{/if}
						</div>
						<div class="flex flex-wrap gap-2">
							<span class="px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest {role.can_login ? 'bg-emerald-500/10 text-emerald-500' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}">login: {role.can_login}</span>
							<span class="px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest {role.is_superuser ? 'bg-rose-500/10 text-rose-500' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}">superuser: {role.is_superuser}</span>
							<span class="px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest {role.can_create_db ? 'bg-sky-500/10 text-sky-500' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}">create-db: {role.can_create_db}</span>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- Privileges Section -->
		<section>
			<div class="flex items-center gap-3 mb-4">
				<span class="text-xs font-black text-slate-400 uppercase tracking-widest italic">Granular Table Privileges</span>
				<div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
			</div>

			<div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-xl">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr class="bg-slate-50/50 dark:bg-slate-950/20">
							<th class="p-4 text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-200 dark:border-slate-800">Grantee</th>
							<th class="p-4 text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-200 dark:border-slate-800">Schema.Table</th>
							<th class="p-4 text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-200 dark:border-slate-800">Privilege</th>
						</tr>
					</thead>
					<tbody>
						{#each $workspaceStore.privileges as priv}
							<tr class="group hover:bg-slate-800/30 transition-colors">
								<td class="p-4 border-b border-slate-200 dark:border-slate-800 text-xs font-black text-slate-800 dark:text-slate-300 uppercase italic tracking-tighter">{priv.grantee}</td>
								<td class="p-4 border-b border-slate-200 dark:border-slate-800 text-xs font-mono font-bold text-slate-500 italic">{priv.schema}.{priv.table}</td>
								<td class="p-4 border-b border-slate-200 dark:border-slate-800">
									<span class="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest italic">{priv.type}</span>
								</td>
							</tr>
						{:else}
							<tr>
								<td colspan="3" class="p-10 text-center text-xs font-bold text-slate-500 uppercase tracking-widest">No individual grants detected</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>
	</div>
</div>
